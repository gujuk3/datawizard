from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from datasets.models import Dataset
from .models import MLModel, ModelMetric
from .serializers import MLModelSerializer

from datawizard_core.data_loader import load_csv
from datawizard_core.ml_engine import (
    split_data,
    train_model,
    evaluate_classification_model,
    evaluate_regression_model,
    get_feature_importance,
)
from datawizard_core.exceptions import ValidationError, TrainingError


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def train(request):
    dataset_id = request.data.get('dataset_id')
    algorithm = request.data.get('algorithm', 'random_forest_classifier')
    model_type = request.data.get('model_type', 'classification')
    target_column = request.data.get('target_column')
    feature_columns = request.data.get('feature_columns', None)
    test_size = float(request.data.get('test_size', 0.2))
    hyperparameters = request.data.get('hyperparameters', {})

    if not dataset_id or not target_column:
        return Response(
            {'error': 'dataset_id and target_column are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        dataset = Dataset.objects.get(pk=dataset_id, user=request.user)
    except Dataset.DoesNotExist:
        return Response({'error': 'Dataset not found.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        df = load_csv(dataset.file.path)

        split = split_data(
            df,
            target_column=target_column,
            feature_columns=feature_columns,
            test_size=test_size,
        )

        result = train_model(
            split['X_train'],
            split['y_train'],
            algorithm=algorithm,
            model_type=model_type,
            hyperparameters=hyperparameters,
        )

        if model_type == 'classification':
            evaluation = evaluate_classification_model(
                result['model'],
                split['X_test'],
                split['y_test'],
            )
        else:
            evaluation = evaluate_regression_model(
                result['model'],
                split['X_test'],
                split['y_test'],
            )

        # Modeli kaydet
        ml_model = MLModel.objects.create(
            user=request.user,
            dataset=dataset,
            name=f"{algorithm}_{dataset.name}",
            algorithm=algorithm,
            model_type=model_type,
            target_column=target_column,
            feature_columns=feature_columns or split.get('feature_columns', []),
            hyperparameters=hyperparameters,
            train_test_split=test_size,
            training_status='completed',
            training_duration=result.get('training_duration', 0),
        )

        # Metrikleri kaydet
        for metric_name, metric_value in evaluation.items():
            if isinstance(metric_value, (int, float)):
                ModelMetric.objects.create(
                    model=ml_model,
                    metric_name=metric_name,
                    metric_value=metric_value,
                )
            else:
                ModelMetric.objects.create(
                    model=ml_model,
                    metric_name=metric_name,
                    metric_value=None,
                    additional_data=metric_value,
                )

        return Response({
            'model': MLModelSerializer(ml_model).data,
            'evaluation': evaluation,
        }, status=status.HTTP_201_CREATED)

    except (ValidationError, TrainingError) as e:
        return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_models(request):
    models = MLModel.objects.filter(user=request.user).order_by('-created_at')
    return Response(MLModelSerializer(models, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def model_detail(request, pk):
    try:
        ml_model = MLModel.objects.get(pk=pk, user=request.user)
    except MLModel.DoesNotExist:
        return Response({'error': 'Model not found.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(MLModelSerializer(ml_model).data)
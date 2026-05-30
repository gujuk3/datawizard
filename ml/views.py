import base64
import os
import tempfile

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
    compute_shap_values,
    save_model,
    load_model,
)
from datawizard_core.exceptions import ValidationError, TrainingError
from datawizard_core.llm_prompter import build_model_results_prompt, call_llm
from datawizard_core.visualizer import (
    plot_feature_importance,
    plot_confusion_matrix,
    plot_prediction_vs_actual,
)
from django.conf import settings


def _chart_to_base64(plot_func, *args, **kwargs) -> str:
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        tmp_path = tmp.name
    try:
        plot_func(*args, output_path=tmp_path, **kwargs)
        with open(tmp_path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode()
        return f"data:image/png;base64,{b64}"
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def train(request):

    dataset_id = request.data.get('dataset_id')
    name = request.data.get('name', '').strip()
    algorithm = request.data.get('algorithm', 'random_forest_classifier')
    model_type = request.data.get('model_type', 'classification')
    target_column = request.data.get('target_column')
    feature_columns = request.data.get('feature_columns', None)
    test_size = float(request.data.get('test_size', 0.2))
    hyperparameters = request.data.get('hyperparameters', {})

    if not name:
        return Response(
            {'error': 'Model ismi zorunludur.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Aynı isimde model var mı kontrol et
    if MLModel.objects.filter(user=request.user, name=name).exists():
        return Response(
            {'error': f'"{name}" isimli bir model zaten mevcut. Farklı bir isim seçin.'},
            status=status.HTTP_400_BAD_REQUEST
        )

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

        # Serialize trained model to disk
        rel_path = save_model(result['model'], settings.MEDIA_ROOT)

        # Modeli kaydet
        ml_model = MLModel.objects.create(
            user=request.user,
            dataset=dataset,
            name=name,
            algorithm=algorithm,
            model_type=model_type,
            target_column=target_column,
            feature_columns=feature_columns or split.get('feature_columns', []),
            hyperparameters=hyperparameters,
            train_test_split=test_size,
            training_status='completed',
            training_duration=result.get('training_duration_seconds', 0),
            model_file=rel_path,
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

        feature_importance = get_feature_importance(result['model'], split['feature_names'])
        shap_values = compute_shap_values(result['model'], split['X_test'], split['feature_names'], model_type)

        # LLM explanation — non-blocking: training succeeds even if LLM fails
        llm_explanation = None
        try:
            prompt = build_model_results_prompt(evaluation, feature_importance, model_type, algorithm, shap_values)
            llm_explanation = call_llm(prompt)
        except Exception:
            pass

        return Response({
            'model': MLModelSerializer(ml_model).data,
            'evaluation': evaluation,
            'feature_importance': feature_importance,
            'shap_values': shap_values,
            'llm_explanation': llm_explanation,
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict(request, pk):
    try:
        ml_model = MLModel.objects.get(pk=pk, user=request.user)
    except MLModel.DoesNotExist:
        return Response({'error': 'Model not found.'}, status=status.HTTP_404_NOT_FOUND)

    features = request.data.get('features', {})
    if not features:
        return Response({'error': 'No features provided.'}, status=status.HTTP_400_BAD_REQUEST)

    if not ml_model.model_file:
        return Response(
            {'error': 'No serialized model found. Please retrain this model.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        model = load_model(ml_model.model_file.path)

        import pandas as pd
        input_df = pd.DataFrame([features])
        input_df = input_df[ml_model.feature_columns]
        prediction = model.predict(input_df)[0]

        if hasattr(prediction, 'item'):
            prediction = prediction.item()

        return Response({'prediction': prediction})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_model(request, pk):
    try:
        ml_model = MLModel.objects.get(pk=pk, user=request.user)
        ml_model.delete()
        return Response({'message': 'Model deleted.'}, status=status.HTTP_204_NO_CONTENT)
    except MLModel.DoesNotExist:
        return Response({'error': 'Model not found.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chart(request, pk):
    try:
        ml_model = MLModel.objects.get(pk=pk, user=request.user)
    except MLModel.DoesNotExist:
        return Response({'error': 'Model not found.'}, status=status.HTTP_404_NOT_FOUND)

    chart_type = request.query_params.get('type', '')
    if not chart_type:
        return Response({'error': "'type' query param required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        if chart_type == 'feature_importance':
            if not ml_model.model_file:
                return Response({'error': 'No model file. Please retrain.'}, status=status.HTTP_400_BAD_REQUEST)
            model = load_model(ml_model.model_file.path)
            fi = get_feature_importance(model, ml_model.feature_columns)
            if not fi:
                return Response({'error': 'Feature importance not available for this model type.'}, status=status.HTTP_400_BAD_REQUEST)
            data = _chart_to_base64(plot_feature_importance, fi)

        elif chart_type == 'confusion_matrix':
            if ml_model.model_type != 'classification':
                return Response({'error': 'Confusion matrix is only for classification models.'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                cm_metric = ml_model.metrics.get(metric_name='confusion_matrix')
                labels_metric = ml_model.metrics.get(metric_name='class_labels')
            except ModelMetric.DoesNotExist:
                return Response({'error': 'Confusion matrix data not found. Please retrain.'}, status=status.HTTP_400_BAD_REQUEST)
            data = _chart_to_base64(plot_confusion_matrix, cm_metric.additional_data, labels_metric.additional_data)

        elif chart_type == 'prediction_vs_actual':
            if ml_model.model_type != 'regression':
                return Response({'error': 'Prediction vs Actual is only for regression models.'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                pred_metric = ml_model.metrics.get(metric_name='predictions')
                actual_metric = ml_model.metrics.get(metric_name='actuals')
            except ModelMetric.DoesNotExist:
                return Response({'error': 'Prediction data not found. Please retrain.'}, status=status.HTTP_400_BAD_REQUEST)
            data = _chart_to_base64(plot_prediction_vs_actual, pred_metric.additional_data, actual_metric.additional_data)

        else:
            return Response({'error': f"Unknown chart type '{chart_type}'."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'chart': data})

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from datasets.models import Dataset
from datawizard_core.data_loader import load_csv
from datawizard_core.data_analyzer import (
    compute_basic_statistics,
    compute_correlation_matrix,
    detect_missing_data,
)
from datawizard_core.data_preprocessor import handle_missing_values
from datawizard_core.exceptions import ValidationError, PreprocessingError
from datawizard_core.llm_prompter import build_statistics_prompt, call_groq
from datawizard_core.exceptions import LLMError

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def llm_explain(request, pk):
    dataset = _get_dataset_or_404(pk, request.user)
    if not dataset:
        return Response({'error': 'Dataset not found.'}, status=status.HTTP_404_NOT_FOUND)

    explain_type = request.data.get('type', 'statistics')

    try:
        df = _load_df(dataset)
        stats = compute_basic_statistics(df)
        missing = detect_missing_data(df)

        summary_data = {
            'row_count': df.shape[0],
            'column_count': df.shape[1],
            'numeric_column_count': len(stats['numeric']),
            'categorical_column_count': len(stats['categorical']),
            'missing_pct': missing['total_missing_pct'],
            'duplicate_row_count': int(df.duplicated().sum()),
        }

        prompt = build_statistics_prompt(summary_data, stats)
        explanation = call_groq(prompt)

        return Response({'explanation': explanation})
    except LLMError as e:
        return Response({'error': e.message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _get_dataset_or_404(pk, user):
    try:
        return Dataset.objects.get(pk=pk, user=user)
    except Dataset.DoesNotExist:
        return None


def _load_df(dataset):
    return load_csv(dataset.file.path)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def statistics(request, pk):
    dataset = _get_dataset_or_404(pk, request.user)
    if not dataset:
        return Response({'error': 'Dataset not found.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        df = _load_df(dataset)
        stats = compute_basic_statistics(df)
        return Response({'dataset_id': pk, 'statistics': stats})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def correlation(request, pk):
    dataset = _get_dataset_or_404(pk, request.user)
    if not dataset:
        return Response({'error': 'Dataset not found.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        df = _load_df(dataset)
        method = request.query_params.get('method', 'pearson')
        corr = compute_correlation_matrix(df, method=method)
        return Response({'dataset_id': pk, 'correlation': corr})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def missing_values(request, pk):
    dataset = _get_dataset_or_404(pk, request.user)
    if not dataset:
        return Response({'error': 'Dataset not found.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        df = _load_df(dataset)
        report = detect_missing_data(df)
        return Response({'dataset_id': pk, 'missing_values': report})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def preprocess(request, pk):
    dataset = _get_dataset_or_404(pk, request.user)
    if not dataset:
        return Response({'error': 'Dataset not found.'}, status=status.HTTP_404_NOT_FOUND)

    strategy = request.data.get('strategy', 'mean')
    columns = request.data.get('columns', None)

    try:
        df = _load_df(dataset)
        df_processed, report = handle_missing_values(df, strategy=strategy, columns=columns)
        return Response({'dataset_id': pk, 'report': report})
    except (ValidationError, PreprocessingError) as e:
        return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
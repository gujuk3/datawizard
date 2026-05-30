import base64
import os
import tempfile

import pandas as pd
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from datasets.models import Dataset, DataColumn
from datawizard_core.data_loader import load_csv
from datawizard_core.data_analyzer import (
    compute_basic_statistics,
    compute_correlation_matrix,
    detect_missing_data,
)
from datawizard_core.data_preprocessor import handle_missing_values
from datawizard_core.exceptions import ValidationError, PreprocessingError
from datawizard_core.llm_prompter import build_statistics_prompt, call_llm
from datawizard_core.exceptions import LLMError
from datawizard_core.visualizer import (
    plot_histogram,
    plot_bar_chart,
    plot_box,
    plot_scatter,
    plot_correlation_heatmap,
)


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

        # Compute correlation alongside statistics — silently skip if not enough numeric columns
        corr_data = None
        try:
            corr_data = compute_correlation_matrix(df, method='pearson')
        except Exception:
            pass

        prompt = build_statistics_prompt(summary_data, stats, corr_data=corr_data)
        explanation = call_llm(prompt)

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

        if not df.isnull().values.any():
            return Response(
                {'error': 'Bu veri setinde eksik değer bulunmuyor. Herhangi bir işlem yapılmadı.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        df_processed, report = handle_missing_values(df, strategy=strategy, columns=columns)

        # Persist processed CSV back to the same file
        df_processed.to_csv(dataset.file.path, index=False)

        # Update dataset row count (may change if strategy='drop')
        dataset.row_count = len(df_processed)
        dataset.save(update_fields=['row_count'])

        # Update DataColumn missing counts
        for col in df_processed.columns:
            DataColumn.objects.filter(dataset=dataset, name=col).update(
                missing_count=int(df_processed[col].isna().sum())
            )

        return Response({'dataset_id': pk, 'report': report})
    except (ValidationError, PreprocessingError) as e:
        return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chart(request, pk):
    dataset = _get_dataset_or_404(pk, request.user)
    if not dataset:
        return Response({'error': 'Dataset not found.'}, status=status.HTTP_404_NOT_FOUND)

    chart_type = request.query_params.get('type', '')
    if not chart_type:
        return Response({'error': "'type' query param required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        df = _load_df(dataset)

        if chart_type == 'histogram':
            column = request.query_params.get('column', '')
            if not column or column not in df.columns:
                return Response({'error': f"Column '{column}' not found."}, status=status.HTTP_400_BAD_REQUEST)
            if not pd.api.types.is_numeric_dtype(df[column]):
                return Response({'error': f"Column '{column}' is not numeric."}, status=status.HTTP_400_BAD_REQUEST)
            data = _chart_to_base64(plot_histogram, df, column)

        elif chart_type == 'bar':
            column = request.query_params.get('column', '')
            if not column or column not in df.columns:
                return Response({'error': f"Column '{column}' not found."}, status=status.HTTP_400_BAD_REQUEST)
            data = _chart_to_base64(plot_bar_chart, df, column)

        elif chart_type == 'box':
            numeric_cols = df.select_dtypes(include='number').columns.tolist()
            if not numeric_cols:
                return Response({'error': 'No numeric columns.'}, status=status.HTTP_400_BAD_REQUEST)
            data = _chart_to_base64(plot_box, df, numeric_cols)

        elif chart_type == 'scatter':
            x_col = request.query_params.get('x', '')
            y_col = request.query_params.get('y', '')
            hue_col = request.query_params.get('hue', '') or None
            if not x_col or x_col not in df.columns or not y_col or y_col not in df.columns:
                return Response({'error': 'Invalid x or y column.'}, status=status.HTTP_400_BAD_REQUEST)
            data = _chart_to_base64(plot_scatter, df, x_col, y_col, hue_column=hue_col)

        elif chart_type == 'correlation':
            method = request.query_params.get('method', 'pearson')
            corr_data = compute_correlation_matrix(df, method=method)
            data = _chart_to_base64(plot_correlation_heatmap, corr_data)

        else:
            return Response({'error': f"Unknown chart type '{chart_type}'."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'chart': data})

    except ValidationError as e:
        return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
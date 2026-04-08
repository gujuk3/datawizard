from django.shortcuts import render
import os
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .models import Dataset, DataColumn
from .serializers import DatasetSerializer

from datawizard_core.data_loader import (
    validate_file_size,
    load_csv,
    validate_csv_structure,
)
from datawizard_core.exceptions import InvalidFileError, ValidationError


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def upload_dataset(request):
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

    file = request.FILES['file']

    # Geçici olarak kaydet
    from django.core.files.storage import default_storage
    saved_path = default_storage.save(f'datasets/{file.name}', file)
    full_path = default_storage.path(saved_path)

    try:
        # Dosya boyutu kontrolü
        size_check = validate_file_size(full_path)
        if not size_check['valid']:
            default_storage.delete(saved_path)
            return Response({
                'error': f"File too large: {size_check['file_size_mb']}MB. Max: {size_check['max_size_mb']}MB"
            }, status=status.HTTP_400_BAD_REQUEST)

        # CSV yükle ve parse et
        df = load_csv(full_path)

        # Yapı doğrulama
        validation = validate_csv_structure(df)

        # Dataset kaydı oluştur
        dataset = Dataset.objects.create(
            user=request.user,
            name=file.name,
            file=saved_path,
            file_size=size_check['file_size_mb'],
            row_count=df.shape[0],
            column_count=df.shape[1],
            status='ready',
        )

        # Sütunları kaydet
        for col in df.columns:
            DataColumn.objects.create(
                dataset=dataset,
                name=col,
                data_type=str(df[col].dtype),
                missing_count=int(df[col].isna().sum()),
                unique_count=int(df[col].nunique()),
            )

        return Response({
            'dataset': DatasetSerializer(dataset).data,
            'validation': validation,
        }, status=status.HTTP_201_CREATED)

    except (InvalidFileError, ValidationError) as e:
        default_storage.delete(saved_path)
        return Response({'error': e.message, 'details': e.details}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        default_storage.delete(saved_path)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_datasets(request):
    datasets = Dataset.objects.filter(user=request.user).order_by('-uploaded_at')
    return Response(DatasetSerializer(datasets, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dataset_detail(request, pk):
    try:
        dataset = Dataset.objects.get(pk=pk, user=request.user)
    except Dataset.DoesNotExist:
        return Response({'error': 'Dataset not found.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(DatasetSerializer(dataset).data)
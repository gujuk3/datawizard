from rest_framework import serializers
from .models import Dataset, DataColumn


class DataColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataColumn
        fields = ['id', 'name', 'data_type', 'missing_count', 'unique_count']


class DatasetSerializer(serializers.ModelSerializer):
    columns = DataColumnSerializer(many=True, read_only=True)

    class Meta:
        model = Dataset
        fields = ['id', 'name', 'file_size', 'row_count', 'column_count', 'uploaded_at', 'status', 'columns']
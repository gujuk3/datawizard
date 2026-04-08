from rest_framework import serializers
from .models import MLModel, ModelMetric


class ModelMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelMetric
        fields = ['metric_name', 'metric_value', 'additional_data']


class MLModelSerializer(serializers.ModelSerializer):
    metrics = ModelMetricSerializer(many=True, read_only=True)

    class Meta:
        model = MLModel
        fields = [
            'id', 'name', 'algorithm', 'model_type', 'target_column',
            'feature_columns', 'hyperparameters', 'train_test_split',
            'training_status', 'training_duration', 'created_at', 'metrics'
        ]
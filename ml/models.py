from django.db import models
from django.conf import settings
from datasets.models import Dataset


class MLModel(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=255)
    algorithm = models.CharField(max_length=100)
    model_type = models.CharField(max_length=50)  # classification / regression
    target_column = models.CharField(max_length=255)
    feature_columns = models.JSONField(default=list)
    hyperparameters = models.JSONField(default=dict)
    train_test_split = models.FloatField(default=0.2)
    training_status = models.CharField(max_length=50, default='pending')
    training_duration = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.algorithm})"


class ModelMetric(models.Model):
    model = models.ForeignKey(MLModel, on_delete=models.CASCADE, related_name='metrics')
    metric_name = models.CharField(max_length=100)
    metric_value = models.FloatField(null=True, blank=True)
    additional_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
from django.contrib import admin
from .models import MLModel, ModelMetric

class ModelMetricInline(admin.TabularInline):
    model = ModelMetric
    extra = 0
    readonly_fields = ['metric_name', 'metric_value', 'additional_data', 'created_at']

@admin.register(MLModel)
class MLModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'algorithm', 'model_type', 'training_status', 'training_duration', 'created_at']
    list_filter = ['model_type', 'training_status', 'algorithm']
    search_fields = ['name', 'user__email']
    readonly_fields = ['created_at', 'training_duration']
    inlines = [ModelMetricInline]
    ordering = ['-created_at']

@admin.register(ModelMetric)
class ModelMetricAdmin(admin.ModelAdmin):
    list_display = ['metric_name', 'metric_value', 'model', 'created_at']
    list_filter = ['metric_name']
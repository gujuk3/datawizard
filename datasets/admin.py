from django.contrib import admin
from .models import Dataset, DataColumn

class DataColumnInline(admin.TabularInline):
    model = DataColumn
    extra = 0
    readonly_fields = ['name', 'data_type', 'missing_count', 'unique_count']

@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'row_count', 'column_count', 'status', 'uploaded_at']
    list_filter = ['status']
    search_fields = ['name', 'user__email']
    readonly_fields = ['uploaded_at', 'row_count', 'column_count', 'file_size']
    inlines = [DataColumnInline]
    ordering = ['-uploaded_at']

@admin.register(DataColumn)
class DataColumnAdmin(admin.ModelAdmin):
    list_display = ['name', 'dataset', 'data_type', 'missing_count', 'unique_count']
    search_fields = ['name', 'dataset__name']
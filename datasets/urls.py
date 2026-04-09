from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_dataset, name='upload_dataset'),
    path('', views.list_datasets, name='list_datasets'),
    path('<int:pk>/', views.dataset_detail, name='dataset_detail'),
    path('<int:pk>/preview/', views.dataset_preview, name='dataset_preview'),
    path('<int:pk>/delete/', views.delete_dataset, name='delete_dataset'),
]
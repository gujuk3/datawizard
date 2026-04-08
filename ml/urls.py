from django.urls import path
from . import views

urlpatterns = [
    path('train/', views.train, name='train'),
    path('', views.list_models, name='list_models'),
    path('<int:pk>/', views.model_detail, name='model_detail'),
]
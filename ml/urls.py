from django.urls import path
from . import views

urlpatterns = [
    path('train/', views.train, name='train'),
    path('', views.list_models, name='list_models'),
    path('<int:pk>/', views.model_detail, name='model_detail'),
    path('<int:pk>/predict/', views.predict, name='predict'),
    path('<int:pk>/delete/', views.delete_model, name='delete_model'),
]
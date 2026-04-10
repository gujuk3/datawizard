from django.urls import path
from . import views

urlpatterns = [
    path('<int:pk>/statistics/', views.statistics, name='statistics'),
    path('<int:pk>/correlation/', views.correlation, name='correlation'),
    path('<int:pk>/missing/', views.missing_values, name='missing_values'),
    path('<int:pk>/preprocess/', views.preprocess, name='preprocess'),
    path('<int:pk>/explain/', views.llm_explain, name='llm_explain'),
]
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/analyze/', views.api_analyze, name='api_analyze'),
    path('healthz/', views.healthz, name='healthz'),
]
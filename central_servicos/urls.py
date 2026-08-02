# pyrefly: ignore [untyped-import]
from django.urls import path
from . import views

app_name = 'central_servicos'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('nova/', views.OrdemServicoCreateView.as_view(), name='nova_os'),
]

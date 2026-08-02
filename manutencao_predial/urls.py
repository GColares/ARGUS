from django.urls import path
from . import views

app_name = 'home_manutencao_predial'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('nova/', views.OrdemServicoCreateView.as_view(), name='nova_os'),
]

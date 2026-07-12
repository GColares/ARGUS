from django.urls import path
from . import views

app_name = 'patrimonio'
urlpatterns = [
    path('', views.home_patrimonio, name='home_patrimonio'), # Relatórios de Bens Ativos
]
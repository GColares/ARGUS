from django.urls import path
from . import views

app_name = 'patrimonio'

urlpatterns = [
    path('', views.home_patrimonio, name='home_patrimonio'),
    path('importar/', views.importar_pdf, name='importar_pdf'),
    path('conferir/<int:verificacao_id>/', views.conferir_importacao, name='conferir_importacao'),
    path('confirmar/<int:verificacao_id>/', views.confirmar_importacao, name='confirmar_importacao'),
    path('detalhe/<int:verificacao_id>/', views.detalhe_importacao, name='detalhe_importacao'),
    path('relatorio/', views.relatorio_geral, name='relatorio_geral'),
    path(
        'projeto/<int:projeto_id>/conferir-bens/',
        views.conferir_bens_projeto,
        name='conferir_bens_projeto',
    ),
]
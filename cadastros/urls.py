from django.urls import path

from cadastros import views

app_name = 'cadastros'

urlpatterns = [
    path('', views.home_cadastros, name='home_cadastros'), # Dashboard de Projetos/Contas
    path('projeto/novo/', views.novo_projeto, name='novo_projeto'),
    path('projeto/<int:projeto_id>/contas/', views.gerenciar_contas, name='gerenciar_contas'),
    path('projeto/<int:projeto_id>/processos/', views.gerenciar_processos, name='gerenciar_processos'),
    path('processo/novo/', views.cadastrar_processo, name='cadastrar_processo'),
    path('fornecedor/novo/', views.cadastrar_fornecedor, name='cadastrar_fornecedor'),
]
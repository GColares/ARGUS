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
    path('projeto/<int:projeto_id>/cotas/', views.gerenciar_cotas, name='gerenciar_cotas'),
    path('cota/<int:cota_id>/visualizar/', views.visualizar_cota, name='visualizar_cota'),
    path('cota/<int:cota_id>/editar/', views.editar_cota, name='editar_cota'),

    path('bolsistas/', views.listar_bolsistas, name='listar_bolsistas'),
    path('bolsistas/novo/', views.criar_bolsista, name='criar_bolsista'),
    path('bolsistas/<int:id>/editar/', views.editar_bolsista, name='editar_bolsista'),
    path('bolsistas/<int:id>/excluir/', views.excluir_bolsista, name='excluir_bolsista'),
]
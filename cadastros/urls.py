from django.urls import path

from cadastros import views

app_name = 'cadastros'

urlpatterns = [
    path('', views.home_cadastros, name='home_cadastros'), # Dashboard de Projetos/Contas
    path('projeto/novo/', views.novo_projeto, name='novo_projeto'),
    path('projeto/<int:projeto_id>/visualizar/', views.visualizar_projeto, name='visualizar_projeto'),
    path('projeto/<int:projeto_id>/editar/', views.editar_projeto, name='editar_projeto'),
    path('projeto/<int:projeto_id>/excluir/', views.excluir_projeto, name='excluir_projeto'),
    path('projeto/<int:projeto_id>/contas/', views.gerenciar_contas, name='gerenciar_contas'),
    path('projeto/<int:projeto_id>/processos/', views.gerenciar_processos, name='gerenciar_processos'),
    path('processo/novo/', views.cadastrar_processo, name='cadastrar_processo'),

    path('projeto/<int:projeto_id>/cotas/', views.gerenciar_cotas, name='gerenciar_cotas'),
    path('cota/<int:cota_id>/visualizar/', views.visualizar_cota, name='visualizar_cota'),
    path('cota/<int:cota_id>/editar/', views.editar_cota, name='editar_cota'),

    path('bolsistas/', views.listar_bolsistas, name='listar_bolsistas'),
    path('bolsistas/novo/', views.criar_bolsista, name='criar_bolsista'),
    path('bolsistas/<int:id>/visualizar/', views.visualizar_bolsista, name='visualizar_bolsista'),
    path('bolsistas/<int:id>/editar/', views.editar_bolsista, name='editar_bolsista'),
    path('bolsistas/<int:id>/excluir/', views.excluir_bolsista, name='excluir_bolsista'),
    path('projetos/', views.listar_projetos, name='listar_projetos'),
    path('fornecedores/', views.listar_fornecedores_global, name='listar_fornecedores_global'),
    path('fornecedores/novo/', views.cadastrar_fornecedor, name='cadastrar_fornecedor'),
    path('fornecedores/<int:id>/visualizar/', views.visualizar_fornecedor, name='visualizar_fornecedor'),
    path('fornecedores/<int:id>/editar/', views.editar_fornecedor, name='editar_fornecedor'),
    path('fornecedores/<int:id>/excluir/', views.excluir_fornecedor, name='excluir_fornecedor'),
    path('processos/', views.listar_processos_global, name='listar_processos_global'),
    path('processos/<int:id>/visualizar/', views.visualizar_processo, name='visualizar_processo'),
    path('processos/<int:id>/editar/', views.editar_processo, name='editar_processo'),
    path('processos/<int:id>/excluir/', views.excluir_processo, name='excluir_processo'),
    path('fontes-recurso/', views.listar_fontes_recurso, name='listar_fontes_recurso'),
    path('fontes-recurso/nova/', views.nova_fonte_recurso, name='nova_fonte_recurso'),
    path('fontes-recurso/<int:id>/editar/', views.editar_fonte_recurso, name='editar_fonte_recurso'),
    path('fontes-recurso/<int:id>/visualizar/', views.visualizar_fonte_recurso, name='visualizar_fonte_recurso'),
    path('fontes-recurso/<int:id>/excluir/', views.excluir_fonte_recurso, name='excluir_fonte_recurso'),
]
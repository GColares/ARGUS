#gestao_projetos/urls.py
from django.urls import path
from . import views

app_name = 'gestao_projetos'

urlpatterns = [
    #home do módulo
    path('', views.home_gestao_projetos, name='home_gestao_projetos'),
    
    # Rota de listagem (ponto de entrada)
    path('relatorios/', views.listar_relatorios, name='listar_relatorios'),
    
    # Geração em lote
    path('relatorios/gerar-lote/', views.gerar_relatorios_lote, name='gerar_relatorios_lote'),
    
    # Orçamento e Financeiro
    path('orcamento-financeiro/', views.relatorio_orcamento_financeiro, name='orcamento_financeiro'),

    path('relatorio/novo/', views.criar_relatorio, name='criar_relatorio'), # CREATE
    path('relatorio/<int:relatorio_id>/elaborar/', views.elaborar_relatorio, name='elaborar_relatorio'), # UPDATE
    path('relatorio/<int:relatorio_id>/preview/', views.preview_relatorio, name='preview_relatorio'), # PREVIEW
    path('relatorio/<int:relatorio_id>/baixar/', views.baixar_relatorio_docx, name='baixar_relatorio_docx'), # DOWNLOAD
    path('relatorio/<int:relatorio_id>/excluir/', views.excluir_relatorio, name='excluir_relatorio'), # DELETE
    path('relatorios/excluir-todos/', views.excluir_todos_relatorios, name='excluir_todos_relatorios'), # DELETE ALL
    path('relatorios/exportar-zip/', views.exportar_rascunhos_zip, name='exportar_rascunhos_zip'), # EXPORT ZIP

    path('relatorio/novo/lote/', views.gerar_relatorios_lote, name='gerar_relatorios_lote'), # BATCH CREATE
    path('poc-extracao/', views.extrair_tabelas_docx_poc, name='poc_extracao'),

    path('projeto/<int:projeto_id>/importar-cronograma/', views.importar_cronograma_projeto, name='importar_cronograma'),
]

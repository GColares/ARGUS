#gestao_projetos/urls.py
from django.urls import path
from . import views

app_name = 'gestao_projetos'

urlpatterns = [
    #home do módulo
    path('', views.home_gestao_projetos, name='home_gestao_projetos'),
    
    # Rota de listagem (ponto de entrada)
    path('relatorios/', views.listar_relatorios, name='listar_relatorios'),
    path('termos/', views.listar_termos_bolsa, name='listar_termos_bolsa'),
    path('termo/<int:termo_id>/editar/', views.editar_termo_bolsa, name='editar_termo_bolsa'),
    
    # Geração em lote
    # Orçamento e Financeiro
    path('orcamento-financeiro/', views.relatorio_orcamento_financeiro, name='orcamento_financeiro'),

    # Folha Mensal de Pagamento de Bolsas
    path('folha-pagamento/', views.folha_mensal_pagamentos, name='folha_mensal_pagamentos'),
    path('parcela/<int:parcela_id>/confirmar-pagamento/', views.confirmar_pagamento_parcela, name='confirmar_pagamento_parcela'),

    path('relatorio/novo/', views.criar_relatorio, name='criar_relatorio'), # CREATE
    path('relatorio/<int:relatorio_id>/visualizar/', views.visualizar_relatorio, name='visualizar_relatorio'), # READ
    path('relatorio/<int:relatorio_id>/alterar/', views.alterar_relatorio, name='alterar_relatorio'), # UPDATE
    path('relatorio/<int:relatorio_id>/baixar/', views.baixar_relatorio_docx, name='baixar_relatorio_docx'), # DOWNLOAD
    path('relatorio/<int:relatorio_id>/excluir/', views.excluir_relatorio, name='excluir_relatorio'), # DELETE
    path('relatorios/excluir-todos/', views.excluir_todos_relatorios, name='excluir_todos_relatorios'), # DELETE ALL
    path('relatorios/exportar-zip/', views.exportar_relatorios_zip, name='exportar_relatorios_zip'), # EXPORT ZIP


    path('poc-extracao/', views.extrair_tabelas_docx_poc, name='poc_extracao'),

    path('projeto/<int:projeto_id>/importar-cronograma/', views.importar_cronograma_projeto, name='importar_cronograma'),
]

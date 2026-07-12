# pyrefly: ignore [missing-import]
from django.urls import path
from . import views

app_name = 'almoxarifado'

urlpatterns = [
    # Dashboard Principal
    path('', views.home_almoxarifado, name='home_almoxarifado'),
    
    # Importação e IA
    path('importar/', views.importar_nfe, name='importar_nfe'),
    
    # Histórico e Exportação de Notas Fiscais
    path('notas/', views.lista_notas_almoxarifado, name='lista_notas'),
    path('notas/csv/', views.exportar_csv_notas, name='exportar_csv_notas'),
    
    # Gestão de uma Nota Fiscal Específica (Capa)
    path('nota/<int:pk>/', views.detalhe_nota_almoxarifado, name='detalhe_nota'),
    path('nota/<int:pk>/editar/', views.editar_nota_almoxarifado, name='editar_nota'),
    path('nota/<int:pk>/excluir/', views.excluir_nota_almoxarifado, name='excluir_nota'),
    
    # Gestão de Insumos (Produtos) Aninhados
    path('produto/<int:produto_id>/editar/', views.editar_produto_almoxarifado, name='editar_produto'),
    path('produto/<int:produto_id>/foto/adicionar/', views.upload_foto_produto, name='upload_foto_produto'),
    path('foto/<int:foto_id>/excluir/', views.excluir_foto_produto, name='excluir_foto_produto'),
    
    # Relatórios por Categoria de Estoque
    path('relatorio/categoria/<str:categoria_codigo>/', views.relatorio_categoria, name='relatorio_categoria'),
    path('relatorio/categoria/<str:categoria_codigo>/csv/', views.exportar_csv_categoria, name='exportar_csv_categoria'),

    # Geração do Termo de Recebimento em Word e Tela
    path('nota/<int:pk>/termo-docx/', views.gerar_termo_recebimento_docx, name='gerar_termo_docx'),
    path('nota/<int:pk>/termo/', views.visualizar_termo_rme, name='ver_termo_rme'),
    path('nota/<int:pk>/anexar-termo/', views.anexar_termo_assinado, name='anexar_termo'),
    
    # Rota para gerar o PDF do RME
    path('rme/<int:rme_id>/pdf/', views.exportar_pdf_rme, name='exportar_pdf_rme'),
]
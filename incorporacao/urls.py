from django.urls import path
from . import views

# Define o namespace para ser usado nos templates e views
app_name = 'incorporacao'

urlpatterns = [
    # Página principal da incorporação (Fila de Processamento)
    path('', views.home_incorporacao, name='home_incorporacao'),
    
    # Página para cadastrar um novo termo de doação
    path('novo/', views.cadastrar_termo, name='novo_termo'),
    
    # Página de detalhes de um termo específico
    path('termo/<int:pk>/', views.detalhe_termo, name='detalhe_termo'),
    
    # ROTA DO ROBÔ: Aciona a extração via IA (Gemini)
    # Esta é a URL que o botão verde deve chamar
    path('termo/<int:pk>/extrair/', views.executar_extracao_argus, name='executar_extracao_argus'),


    path('termo/<int:pk>/excluir/', views.excluir_termo, name='excluir_termo'),
    path('limpar-testes/', views.limpar_registros_incompletos, name='limpar_testes'),

    path('api/buscar-fornecedor/', views.buscar_fornecedor_cnpj, name='api_buscar_fornecedor'),
    
    path('item/editar/<int:pk>/', views.editar_item, name='editar_item'),
    path('item/excluir/<int:pk>/', views.excluir_item, name='excluir_item'),
    path('termo/<int:pk>/extrair-itens/', views.processar_itens_automaticos, name='extrair_itens_automaticos'),

]
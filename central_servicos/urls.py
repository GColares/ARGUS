# pyrefly: ignore [untyped-import]
from django.urls import path
from . import views

app_name = 'central_servicos'

urlpatterns = [
    path('', views.home_central_servicos, name='home_central_servicos'),
    path('nova/', views.OrdemServicoCreateView.as_view(), name='nova_os'),
    path('relatorio/<str:status>/', views.RelatorioOSView.as_view(), name='relatorio_os'),
    path('historico/', views.OrdemServicoHistoricoView.as_view(), name='historico_os'),
    path('cancelar/<int:pk>/', views.OrdemServicoCancelarView.as_view(), name='cancelar_os'),
    
    # Gestão de Prédios
    path('predios/', views.PredioListView.as_view(), name='predio_list'),
    path('predios/novo/', views.PredioCreateView.as_view(), name='predio_novo'),
    path('predios/<int:pk>/editar/', views.PredioUpdateView.as_view(), name='predio_editar'),
    path('predios/<int:pk>/excluir/', views.PredioDeleteView.as_view(), name='predio_excluir'),

    # Gestão de Andares
    path('andares/', views.AndarListView.as_view(), name='andar_list'),
    path('andares/novo/', views.AndarCreateView.as_view(), name='andar_novo'),
    path('andares/<int:pk>/editar/', views.AndarUpdateView.as_view(), name='andar_editar'),
    path('andares/<int:pk>/excluir/', views.AndarDeleteView.as_view(), name='andar_excluir'),

    # Gestão de Salas
    path('salas/', views.SalaListView.as_view(), name='sala_list'),
    path('salas/novo/', views.SalaCreateView.as_view(), name='sala_novo'),
    path('salas/<int:pk>/editar/', views.SalaUpdateView.as_view(), name='sala_editar'),
    path('salas/<int:pk>/excluir/', views.SalaDeleteView.as_view(), name='sala_excluir'),

    # Gestão de Ativos Prediais
    path('ativos/', views.AtivoPredialListView.as_view(), name='ativopredial_list'),
    path('ativos/novo/', views.AtivoPredialCreateView.as_view(), name='ativopredial_novo'),
    path('ativos/<int:pk>/editar/', views.AtivoPredialUpdateView.as_view(), name='ativopredial_editar'),
    path('ativos/<int:pk>/excluir/', views.AtivoPredialDeleteView.as_view(), name='ativopredial_excluir'),

    # Categoria de Serviço
    path('categorias/', views.CategoriaServicoListView.as_view(), name='categoriaservico_list'),
    path('categorias/novo/', views.CategoriaServicoCreateView.as_view(), name='categoriaservico_novo'),
    path('categorias/<int:pk>/editar/', views.CategoriaServicoUpdateView.as_view(), name='categoriaservico_editar'),
    path('categorias/<int:pk>/excluir/', views.CategoriaServicoDeleteView.as_view(), name='categoriaservico_excluir'),

    # Tipo de Ativo
    path('tipos-ativos/', views.TipoAtivoListView.as_view(), name='tipoativo_list'),
    path('tipos-ativos/novo/', views.TipoAtivoCreateView.as_view(), name='tipoativo_novo'),
    path('tipos-ativos/<int:pk>/editar/', views.TipoAtivoUpdateView.as_view(), name='tipoativo_editar'),
    path('tipos-ativos/<int:pk>/excluir/', views.TipoAtivoDeleteView.as_view(), name='tipoativo_excluir'),

    # Finalidade
    path('finalidades/', views.FinalidadeListView.as_view(), name='finalidade_list'),
    path('finalidades/novo/', views.FinalidadeCreateView.as_view(), name='finalidade_novo'),
    path('finalidades/<int:pk>/editar/', views.FinalidadeUpdateView.as_view(), name='finalidade_editar'),
    path('finalidades/<int:pk>/excluir/', views.FinalidadeDeleteView.as_view(), name='finalidade_excluir'),
]

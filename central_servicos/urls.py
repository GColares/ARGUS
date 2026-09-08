# pyrefly: ignore [untyped-import]
from django.urls import path
from . import views

app_name = 'central_servicos'

urlpatterns = [
    path('', views.home_central_servicos, name='home_central_servicos'),
    path('nova/', views.OrdemServicoCreateView.as_view(), name='nova_os'),
    path('relatorio/<str:status>/', views.RelatorioOSView.as_view(), name='relatorio_os'),
    path('historico/', views.OrdemServicoHistoricoView.as_view(), name='historico_os'),
    path('relatorios/', views.RelatoriosView.as_view(), name='relatorios'),
    path('reordenar/', views.ReordenarItensView.as_view(), name='reordenar_itens'),
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

    # Gestão de Ambientes
    path('ambientes/', views.AmbienteListView.as_view(), name='ambiente_list'),
    path('ambientes/novo/', views.AmbienteCreateView.as_view(), name='ambiente_novo'),
    path('ambientes/<int:pk>/editar/', views.AmbienteUpdateView.as_view(), name='ambiente_editar'),
    path('ambientes/<int:pk>/excluir/', views.AmbienteInativarView.as_view(), name='ambiente_excluir'),
    path('ambientes/<int:pk>/reativar/', views.AmbienteReativarView.as_view(), name='ambiente_reativar'),


    # Gestão de Tipos de Ambiente
    path('tipos-ambiente/', views.TipoAmbienteListView.as_view(), name='tipoambiente_list'),
    path('tipos-ambiente/ajax-add/', views.TipoAmbienteAjaxCreateView.as_view(), name='tipoambiente_ajax_add'),
    path('tipos-ambiente/novo/', views.TipoAmbienteCreateView.as_view(), name='tipoambiente_novo'),
    path('tipos-ambiente/<int:pk>/editar/', views.TipoAmbienteUpdateView.as_view(), name='tipoambiente_editar'),
    path('tipos-ambiente/<int:pk>/excluir/', views.TipoAmbienteDeleteView.as_view(), name='tipoambiente_excluir'),

    # Gestão de Categorias de Elementos Construtivos
    path('categorias-elemento/', views.CategoriaElementoListView.as_view(), name='categoriaelemento_list'),
    path('categorias-elemento/novo/', views.CategoriaElementoCreateView.as_view(), name='categoriaelemento_novo'),
    path('categorias-elemento/<int:pk>/editar/', views.CategoriaElementoUpdateView.as_view(), name='categoriaelemento_editar'),
    path('categorias-elemento/<int:pk>/excluir/', views.CategoriaElementoDeleteView.as_view(), name='categoriaelemento_excluir'),

    # Gestão de Tipos de Elementos Construtivos
    path('tipos-elemento/', views.TipoElementoListView.as_view(), name='tipoelemento_list'),
    path('tipos-elemento/novo/', views.TipoElementoCreateView.as_view(), name='tipoelemento_novo'),
    path('tipos-elemento/<int:pk>/editar/', views.TipoElementoUpdateView.as_view(), name='tipoelemento_editar'),
    path('tipos-elemento/<int:pk>/excluir/', views.TipoElementoDeleteView.as_view(), name='tipoelemento_excluir'),

    # Gestão de Elementos Construtivos
    path('elementos-construtivos/', views.ElementoConstrutivoListView.as_view(), name='elementoconstrutivo_list'),
    path('elementos-construtivos/novo/', views.ElementoConstrutivoCreateView.as_view(), name='elementoconstrutivo_novo'),
    path('elementos-construtivos/<int:pk>/editar/', views.ElementoConstrutivoUpdateView.as_view(), name='elementoconstrutivo_editar'),
    path('elementos-construtivos/<int:pk>/excluir/', views.ElementoConstrutivoDeleteView.as_view(), name='elementoconstrutivo_excluir'),

    # Gestão de Ativos Prediais
    path('ativos/', views.AtivoPredialListView.as_view(), name='ativopredial_list'),
    path('ativos/novo/', views.AtivoPredialCreateView.as_view(), name='ativopredial_novo'),
    path('ativos/ambiente/<int:ambiente_id>/', views.AmbienteAtivosOffcanvasView.as_view(), name='ambiente_ativos_offcanvas'),
    path('ativos/ambiente/<int:ambiente_id>/rapido/', views.AtivoPredialRapidoCreateView.as_view(), name='ativopredial_rapido_novo'),
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

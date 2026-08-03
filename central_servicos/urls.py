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
]

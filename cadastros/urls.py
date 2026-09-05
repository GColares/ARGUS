from django.urls import path

from cadastros import views

app_name = 'cadastros'

urlpatterns = [

    path('termos/', views.TermoCooperacaoListView.as_view(), name='listar_termos'),
    path('termos/novo/', views.TermoCooperacaoCreateView.as_view(), name='cadastrar_termo'),
    path('termos/<int:pk>/visualizar/', views.TermoCooperacaoDetailView.as_view(), name='visualizar_termo'),
    path('termos/<int:pk>/editar/', views.TermoCooperacaoUpdateView.as_view(), name='editar_termo'),
    path('termos/<int:pk>/excluir/', views.TermoCooperacaoDeleteView.as_view(), name='excluir_termo'),
    
    path('programas/', views.ProgramaListView.as_view(), name='listar_programas'),
    path('programas/novo/', views.ProgramaCreateView.as_view(), name='cadastrar_programa'),
    path('programas/<int:pk>/visualizar/', views.ProgramaDetailView.as_view(), name='visualizar_programa'),
    path('programas/<int:pk>/editar/', views.ProgramaUpdateView.as_view(), name='editar_programa'),
    path('programas/<int:pk>/excluir/', views.ProgramaDeleteView.as_view(), name='excluir_programa'),

    path('', views.home_cadastros, name='home_cadastros'), # Dashboard de Projetos/Contas
    path('projeto/novo/', views.novo_projeto, name='novo_projeto'),
    path('api/termos-por-empresa/<int:empresa_id>/', views.api_termos_por_empresa, name='api_termos_por_empresa'),
    path('projeto/<int:projeto_id>/visualizar/', views.visualizar_projeto, name='visualizar_projeto'),
    path('projeto/<int:projeto_id>/editar/', views.editar_projeto, name='editar_projeto'),
    path('projeto/<int:projeto_id>/excluir/', views.excluir_projeto, name='excluir_projeto'),
    path('projeto/<int:projeto_id>/contas/', views.gerenciar_contas, name='gerenciar_contas'),
    path('conta/<int:conta_id>/editar/', views.editar_conta_bancaria, name='editar_conta_bancaria'),
    path('conta/<int:conta_id>/excluir/', views.excluir_conta_bancaria, name='excluir_conta_bancaria'),
    path('projeto/<int:projeto_id>/processos/', views.gerenciar_processos, name='gerenciar_processos'),
    path('processo/novo/', views.cadastrar_processo, name='cadastrar_processo'),

    path('projeto/<int:projeto_id>/cotas/', views.gerenciar_cotas, name='gerenciar_cotas'),
    path('cota/<int:cota_id>/visualizar/', views.visualizar_cota, name='visualizar_cota'),
    path('cota/<int:cota_id>/editar/', views.editar_cota, name='editar_cota'),

    path('projetos/', views.listar_projetos, name='listar_projetos'),
    path('pessoas-fisicas/', views.listar_pessoas_fisicas, name='listar_pessoas_fisicas'),
    path('pessoas-fisicas/nova/', views.cadastrar_pessoa_fisica, name='cadastrar_pessoa_fisica'),
    path('pessoas-fisicas/<int:id>/editar/', views.editar_pessoa_fisica, name='editar_pessoa_fisica'),
    path('pessoas-fisicas/<int:id>/excluir/', views.excluir_pessoa_fisica, name='excluir_pessoa_fisica'),
    path('pessoas-juridicas/', views.listar_pessoas_juridicas, name='listar_pessoas_juridicas'),
    path('pessoas-juridicas/nova/', views.cadastrar_pessoa_juridica, name='cadastrar_pessoa_juridica'),
    path('pessoas-juridicas/<int:pk>/visualizar/', views.PessoaJuridicaDetailView.as_view(), name='visualizar_pessoa_juridica'),
    path('pessoas-juridicas/<int:id>/editar/', views.editar_pessoa_juridica, name='editar_pessoa_juridica'),
    path('pessoas-juridicas/<int:id>/excluir/', views.excluir_pessoa_juridica, name='excluir_pessoa_juridica'),
    path('processos/', views.listar_processos_global, name='listar_processos_global'),
    path('processos/<int:id>/visualizar/', views.visualizar_processo, name='visualizar_processo'),
    path('processos/<int:id>/editar/', views.editar_processo, name='editar_processo'),
    path('processos/<int:id>/excluir/', views.excluir_processo, name='excluir_processo'),
    path('fontes-recurso/', views.listar_fontes_recurso, name='listar_fontes_recurso'),
    path('fontes-recurso/nova/', views.nova_fonte_recurso, name='nova_fonte_recurso'),
    path('fontes-recurso/<int:id>/editar/', views.editar_fonte_recurso, name='editar_fonte_recurso'),
    path('fontes-recurso/<int:id>/visualizar/', views.visualizar_fonte_recurso, name='visualizar_fonte_recurso'),
    path('fontes-recurso/<int:id>/excluir/', views.excluir_fonte_recurso, name='excluir_fonte_recurso'),

    # Termos de Parceria
    path('termos-parceria/', views.TermoDeParceriaListView.as_view(), name='listar_termos_parceria'),
    path('termos-parceria/novo/', views.TermoDeParceriaCreateView.as_view(), name='cadastrar_termo_parceria'),
    path('termos-parceria/<int:pk>/visualizar/', views.TermoDeParceriaDetailView.as_view(), name='visualizar_termo_parceria'),
    path('termos-parceria/<int:pk>/editar/', views.TermoDeParceriaUpdateView.as_view(), name='editar_termo_parceria'),
    path('termos-parceria/<int:pk>/excluir/', views.TermoDeParceriaDeleteView.as_view(), name='excluir_termo_parceria'),

]
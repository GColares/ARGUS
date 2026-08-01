from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [ 
    # ==========================================
    # HOME DO SISTEMA INTEIRO
    # ==========================================
    path('admin/', admin.site.urls),
    path('', views.home_argus, name='home_geral'), # Rota raiz

    # ==========================================
    # ROTAS DE AUTENTICAÇÃO INSTITUCIONAL
    # ==========================================
    path('login/', auth_views.LoginView.as_view(
        template_name='autenticacao/login.html',
        redirect_authenticated_user=True # Impede que quem já está logado veja a tela de login
    ), name='login'),
    
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # ==========================================
    # MÓDULOS DO SISTEMA ARGUS
    # ==========================================
    path('cadastros/', include('cadastros.urls', namespace='home_cadastros')),
    path('incorporacao/', include('incorporacao.urls', namespace='home_incorporacao')),
    path('patrimonio/', include('patrimonio.urls', namespace='home_patrimonio')),
    path('almoxarifado/', include('almoxarifado.urls', namespace='home_almoxarifado')),
    path('gestao_projetos/', include('gestao_projetos.urls', namespace='home_gestao_projetos')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
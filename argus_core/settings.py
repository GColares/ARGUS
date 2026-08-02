# argus_core/settings.py

import os
from pathlib import Path
from dotenv import load_dotenv


# Carrega as variáveis de ambiente do arquivo .env local
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# CONFIGURAÇÕES DE SEGURANÇA INSTITUCIONAL (BLINDAGEM CONTRA VAZAMENTOS)
# ==============================================================================

# SECURITY WARNING: keep the secret key used in production secret!
# Em produção, a chave será lida do ambiente. Localmente, usa um fallback de desenvolvimento.
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-AMBIENTE-LOCAL-PADRAO-NUNCA-USAR-EM-PRODUCAO')

# Chave de acesso à API do Gemini para a extração de NF-e via IA
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
# O DEBUG agora é controlado via variável de ambiente (falso por padrão se não declarado)
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Permite conexões dinâmicas baseadas no ambiente Docker/Produção ou local
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')


# ==============================================================================
# DEFINIÇÃO DE APLICATIVOS (INSTALLED APPS)
# ==============================================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',  # Para formatação institucional de números e datas

    # Módulos Core do Sistema ARGUS
    'cadastros',
    'patrimonio',
    'incorporacao',
    'almoxarifado',
    'gestao_projetos',
    'manutencao_predial',
]


# ==============================================================================
# MIDDLEWARES (PRODUÇÃO E ENTREGA DE ESTÁTICOS COMPACTADOS)
# ==============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # <-- ADICIONADO: Entrega estáticos diretamente no Docker
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'argus_core.urls'


# ==============================================================================
# TEMPLATES
# ==============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'argus_core.wsgi.application'

# =====================================================================
# BANCO DE DADOS (PERSISTÊNCIA DINÂMICA COM FALLBACK SEGURO)
# =====================================================================
if os.getenv('DATABASE_URL'):
    # Configuração automatizada para contêiner de produção PostgreSQL
    import urllib.parse as urlparse
    url = urlparse.urlparse(os.getenv('DATABASE_URL'))
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': url.path[1:],
            'USER': url.username,
            'PASSWORD': url.password,
            'HOST': url.hostname,
            'PORT': url.port or 5432,
        }
    }
else:
    # DEFINITIVO: Conectado ao servidor de grande porte PostgreSQL local
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'argus_db',
            'USER': 'postgres',
            'PASSWORD': 'argus',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }

    # -----------------------------------------------------------------
    # FALLBACK PARA SQLITE (Em caso de emergência ou máquina sem Postgres)
    # Para usar, comente o dicionário DATABASES do 'else' acima e descomente abaixo:
    # -----------------------------------------------------------------
    # DATABASES = {
    #     'default': {
    #         'ENGINE': 'django.db.backends.sqlite3',
    #         'NAME': BASE_DIR / 'db.sqlite3',
    #         'OPTIONS': {
    #             'timeout': 30,
    #         }
    #     }
    # }
# ==============================================================================
# VALIDAÇÃO DE SENHAS
# ==============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ==============================================================================
# INTERNACIONALIZAÇÃO E LOCALIZAÇÃO CORPORATIVA
# ==============================================================================

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Manaus'  # Rigorosamente alinhado ao IFAM

USE_I18N = True

USE_TZ = True

USE_L10N = True

USE_THOUSAND_SEPARATOR = True  # Formatação padrão de moedas (ex: 1.500,00)


# ==============================================================================
# ARQUIVOS ESTÁTICOS, MÍDIA E ARMAZENAMENTO (STORAGES FOR DOCKER)
# ==============================================================================

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Pasta onde o Django irá consolidar os estáticos no ambiente Docker (via collectstatic)
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Diretórios para upload de arquivos reais (PDFs de convênios, notas fiscais, fotos de insumos)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Configuração do motor de armazenamento padrão do Django 6.0+ integrado ao WhiteNoise
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# ==============================================================================
# AJUSTES OPERACIONAIS DE CONVENIÊNCIA
# ==============================================================================

# Mantido para suportar tabelas de conferência massivas
DATA_UPLOAD_MAX_NUMBER_FIELDS = 20000

# ==============================================================================
# CONFIGURAÇÕES DE AUTENTICAÇÃO E REDIRECIONAMENTO
# ==============================================================================

# Para onde o usuário vai se tentar acessar uma URL protegida sem estar logado
LOGIN_URL = 'login'

# Para onde o usuário é redirecionado após o login bem-sucedido
# (Vamos apontar para o dashboard que unificamos ontem)
LOGIN_REDIRECT_URL = 'home_geral'

# Para onde o usuário vai após clicar em "Sair"
LOGOUT_REDIRECT_URL = 'login'
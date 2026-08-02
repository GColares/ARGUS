# pyrefly: ignore [untyped-import]
from django.apps import AppConfig


class CentralServicosConfig(AppConfig):
    # pyrefly: ignore [bad-override]
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'central_servicos'
    verbose_name = 'Central de Serviços'

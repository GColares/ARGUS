import os
import sys
import glob
import django

# Adiciona a raiz do projeto ao path do Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Detecta automaticamente o caminho do arquivo settings.py no projeto
settings_files = glob.glob('**/settings.py', recursive=True)
if not settings_files:
    print("Erro crítico: Arquivo settings.py não foi encontrado no projeto.")
    sys.exit(1)

# Converte o caminho do diretório em um módulo Python válido (ex: core.settings, config.settings)
settings_dir = os.path.dirname(settings_files[0])
settings_module = f"{settings_dir.replace(os.sep, '.')}.settings" if settings_dir else "settings"

print(f"Módulo de configuração detectado: {settings_module}")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)
django.setup()

from django.db import connection
from cadastros.models import MembroEquipe

# Recria a tabela física da Fonte Única de Verdade
with connection.schema_editor() as editor:
    editor.create_model(MembroEquipe)

print("Sucesso: A tabela 'argus_membro_equipe' foi recriada no banco de dados!")
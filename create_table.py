import django
django.setup()
from django.db import connection
from cadastros.models import MembroEquipe
with connection.schema_editor() as editor:
    editor.create_model(MembroEquipe)

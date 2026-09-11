import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "argus_core.settings")
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("DROP SCHEMA public CASCADE;")
    cursor.execute("CREATE SCHEMA public;")

print("Schema dropped and recreated successfully.")

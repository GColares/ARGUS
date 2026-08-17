import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'argus_core.settings')
django.setup()

from cadastros.models import InstituicaoParceira, Convenio, ProjetoPDI

print("InstituicaoParceira count:", InstituicaoParceira.objects.count())
print("Convenio count:", Convenio.objects.count())
print("ProjetoPDI count:", ProjetoPDI.objects.count())

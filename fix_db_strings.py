import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'argus_core.settings')
django.setup()

from django.apps import apps
from django.db import models

mapping = {
    '¾': 'ó',
    'Ò': 'ã',
    'þ': 'ç',
    'Ô': 'â',
    'Û': 'ê',
    'ß': 'á',
    'Ú': 'é',
    'Ý': 'í',
    '·': 'ú',
    '¶': 'ô',
    'Ó': 'à',
    '║': 'º'
}

def fix_string(s):
    if not isinstance(s, str):
        return s
    for bad, good in mapping.items():
        s = s.replace(bad, good)
    return s

for model in apps.get_models():
    # Only models in our apps
    if not model._meta.app_label in ['cadastros', 'central_servicos', 'gestao_projetos']:
        continue
    
    char_fields = [f for f in model._meta.get_fields() if isinstance(f, (models.CharField, models.TextField))]
    if not char_fields:
        continue

    try:
        for obj in model.objects.all():
            changed = False
            for f in char_fields:
                old_val = getattr(obj, f.name)
                if old_val:
                    new_val = fix_string(old_val)
                    if new_val != old_val:
                        setattr(obj, f.name, new_val)
                        changed = True
            if changed:
                obj.save()
    except Exception as e:
        pass
        
print('Correção finalizada!')

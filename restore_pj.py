import os
import json
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "argus_core.settings")
django.setup()

from django.core.management import call_command

with open('backups_refatoracao_pre_rename.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# models to restore
target_models = {
    'cadastros.pessoajuridica',
    'cadastros.empresaparceira',
    'cadastros.fundacaoapoio',
    'cadastros.ict',
    'cadastros.agenciafomento',
    'cadastros.fornecedor',
}

filtered_data = [obj for obj in data if obj['model'] in target_models]

with open('pj_backup_filtered.json', 'w', encoding='utf-8') as f:
    json.dump(filtered_data, f)

print(f"Filtered {len(filtered_data)} records. Loading...")
call_command('loaddata', 'pj_backup_filtered.json')
print("Restore completed!")

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
    'cadastros.pessoafisica',
    'cadastros.perfilaluno',
    'cadastros.perfilcolaboradorexterno',
    'cadastros.perfilservidor',
    'cadastros.perfilterceirizado',
    'cadastros.dadobancario',
}

# Remove 'user' FK from PessoaFisica if it exists and the user might not exist anymore
filtered_data = []
for obj in data:
    if obj['model'] in target_models:
        if obj['model'] == 'cadastros.pessoafisica' and 'user' in obj['fields']:
            # We created a new superuser with id=1, but the old users are gone.
            # Just set user to null to avoid ForeignKey constraint errors.
            obj['fields']['user'] = None
        filtered_data.append(obj)


with open('pf_backup_filtered.json', 'w', encoding='utf-8') as f:
    json.dump(filtered_data, f)

print(f"Filtered {len(filtered_data)} records. Loading...")
call_command('loaddata', 'pf_backup_filtered.json')
print("Restore completed!")

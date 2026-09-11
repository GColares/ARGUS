import json
with open('backups_refatoracao_pre_rename.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

models = set([obj['model'] for obj in data])
print(models)

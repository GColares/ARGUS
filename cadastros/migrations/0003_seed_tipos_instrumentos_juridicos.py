from django.db import migrations

def populate_tipos(apps, schema_editor):
    TipoInstrumentoJuridico = apps.get_model('cadastros', 'TipoInstrumentoJuridico')
    
    tipos = [
        # O legado de Termo de Parceria agora se chama Convenio e fica aqui:
        {"nome": "Convênio para PD&I", "sigla": "CV", "descricao": "Projetos legados executados antes da adoção de Acordos de Parceria."},
        {"nome": "Acordo de Parceria para PD&I", "sigla": "AP", "descricao": "Novo modelo de parceria baseado no Marco Legal de CT&I."},
        {"nome": "Termo de Cooperação", "sigla": "TC", "descricao": "Termo guarda-chuva ou de cooperação mais amplo (Programa)."},
        {"nome": "Protocolo de Intenções", "sigla": "PI", "descricao": "Manifestação de intenções sem obrigação financeira imediata."},
    ]
    
    for tipo_data in tipos:
        TipoInstrumentoJuridico.objects.create(**tipo_data)

class Migration(migrations.Migration):

    dependencies = [
        ('cadastros', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(populate_tipos),
    ]

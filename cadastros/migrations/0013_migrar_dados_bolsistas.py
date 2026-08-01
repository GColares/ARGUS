from django.db import migrations
from decimal import Decimal

def transferir_dados_legados(apps, schema_editor):
    """
    Lê os dados da entidade deprecada BolsistaProjeto e os fragmenta 
    nas novas entidades CotaBolsaPT (Planejamento) e TermoBolsa (Execução),
    garantindo a rastreabilidade do histórico.
    """
    BolsistaProjeto = apps.get_model('cadastros', 'BolsistaProjeto')
    CotaBolsaPT = apps.get_model('cadastros', 'CotaBolsaPT')
    TermoBolsa = apps.get_model('cadastros', 'TermoBolsa')

    for legado in BolsistaProjeto.objects.all():
        # 1. Cria a previsão da cota orçamentária amarrada ao Projeto
        cota, created = CotaBolsaPT.objects.get_or_create(
            projeto=legado.projeto,
            perfil_funcao=legado.funcao if legado.funcao else 'Função Não Informada',
            defaults={
                'quantidade_vagas': 1,
                'parcelas_previstas': 12, # Valor padrão sistêmico temporário
                'valor_global_previsto': Decimal('0.00') # O Gestor deve atualizar via painel Admin
            }
        )

        # 2. Cria o contrato efetivo do bolsista amarrado à cota
        TermoBolsa.objects.create(
            cota_pt=cota,
            bolsista_nome=legado.nome_completo,
            bolsista_cpf=legado.cpf,
            numero_termo=legado.termo_bolsa if legado.termo_bolsa else 'S/N',
            vigencia_inicio=legado.data_inicio,
            vigencia_fim=legado.data_fim,
            quantidade_parcelas=1, # Necessário valor mínimo > 0 para validação
            valor_parcela=Decimal('0.00'),
            status='ATIVO'
        )

class Migration(migrations.Migration):

    dependencies = [
        # Restabelece a linearidade do grafo de migrações
        ('cadastros', '0012_cotabolsapt_termobolsa'),
    ]

    operations = [
        migrations.RunPython(transferir_dados_legados, reverse_code=migrations.RunPython.noop),
    ]
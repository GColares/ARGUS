import os
import django
import pandas as pd
from datetime import datetime

# Configuração do ambiente Django para script avulso
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'argus.settings')
django.setup()

from cadastros.models import ProjetoPDI
from gestao_projetos.models import Bolsista, RelatorioAtividade

def popular_banco():
    """
    Lê a planilha relatorios-atividades-cabecalhos_2.xlsx e injeta os 
    dados estruturais no banco do ARGUS.
    """
    arquivo = 'relatorios-atividades-cabecalhos_2.xlsx'
    
    try:
        df = pd.read_excel(arquivo)
    except FileNotFoundError:
        print(f"Erro: Arquivo {arquivo} não encontrado.")
        return

    # Trata dados nulos
    df = df.fillna('')

    # Criação do Projeto Mestre (Fixo para este escopo)
    projeto, _ = ProjetoPDI.objects.get_or_create(
        convenio='0002/2026', # Considerando o formato do módulo cadastros
        defaults={'nome': 'Bio Caroço', 'projeto': 'Bio Caroço'}
    )

    for index, row in df.iterrows():
        # 1. Cadastra ou atualiza o Bolsista
        # Parse rudimentar das datas da string '25/06/2026 a 28/02/2027'
        datas_contrato = str(row['bolsista_contratacao']).split(' a ')
        dt_inicio = datetime.strptime(datas_contrato[0].strip(), '%d/%m/%Y').date() if len(datas_contrato) > 0 else datetime.now().date()
        dt_fim = datetime.strptime(datas_contrato[1].strip(), '%d/%m/%Y').date() if len(datas_contrato) > 1 else datetime.now().date()

        bolsista, _ = Bolsista.objects.get_or_create(
            cpf=str(row['bolsista_cpf']).strip(),
            defaults={
                'projeto': projeto,
                'nome_completo': str(row['bolsista_nome']).strip(),
                'rg': str(row['bolsista_rg']).strip(),
                'funcao': str(row['bolsista_funcao']).strip(),
                'termo_bolsa': str(row['bolsista_termodebolsa']).strip(),
                'carga_horaria_total': int(row['bolsista_ch']) if row['bolsista_ch'] else 0,
                'data_inicio': dt_inicio,
                'data_fim': dt_fim
            }
        )

        # 2. Cria o Rascunho do Relatório associado à Parcela
        datas_parcela = str(row['parcela_periodo']).split(' a ')
        dt_inicio_parc = datetime.strptime(datas_parcela[0].strip(), '%d/%m/%y').date() if len(datas_parcela) > 0 else datetime.now().date()
        dt_fim_parc = datetime.strptime(datas_parcela[1].strip(), '%d/%m/%y').date() if len(datas_parcela) > 1 else datetime.now().date()

        RelatorioAtividade.objects.get_or_create(
            bolsista=bolsista,
            parcela=int(row['bolsa_parcela']),
            defaults={
                'criado_por_id': 1, # ID do Superuser para a carga inicial
                'status': 'RASCUNHO',
                'macroentrega': int(row['macroentrega_numero']) if row['macroentrega_numero'] else 1,
                'periodo_inicio': dt_inicio_parc,
                'periodo_fim': dt_fim_parc,
                'carga_horaria_periodo': int(row['parcela_ch']) if row['parcela_ch'] else 0,
                'ocorrencias': ''
            }
        )

    print("Carga de dados finalizada com sucesso.")

if __name__ == '__main__':
    popular_banco()
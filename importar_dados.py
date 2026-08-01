import os
import csv
import django
from decimal import Decimal

# Configuração do ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'argus_core.settings')
django.setup()

from patrimonio.models import BemPatrimonial
from cadastros.models import ProjetoPDI

def limpar_valor(valor_str):
    if not valor_str: return Decimal('0.00')
    try:
        # Remove R$, pontos de milhar e troca vírgula por ponto
        limpo = str(valor_str).replace('R$', '').replace('.', '').replace(',', '.').strip()
        return Decimal(limpo)
    except:
        return Decimal('0.00')

def importar():
    diretorio = 'importacao'
    
    print("--- Iniciando Limpeza e Re-importação (Nova Estrutura) ---")
    # Limpa os bens para evitar duplicidade, mas mantém os projetos
    BemPatrimonial.objects.all().delete()
    
    if not os.path.exists(diretorio):
        print(f"Erro: Pasta '{diretorio}' não encontrada.")
        return

    for arquivo in os.listdir(diretorio):
        if arquivo.lower().endswith('.csv'):
            caminho_csv = os.path.join(diretorio, arquivo)
            print(f"Processando: {arquivo}")

            with open(caminho_csv, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for linha in reader:
                    # Limpeza das chaves para evitar espaços invisíveis no CSV
                    dados = {k.strip() if k else '': v for k, v in linha.items()}
                    
                    # Pular linhas vazias ou de totais
                    if not dados.get('Cód. Projeto') or 'Total' in str(dados.get('Nº Patrimônio', '')):
                        continue

                    # 1. Garantir que o Projeto existe
                    projeto, _ = ProjetoPDI.objects.get_or_create(
                        codigo=dados['Cód. Projeto'].strip(),
                        defaults={'nome': dados.get('Projeto', 'Projeto sem nome')}
                    )

                    # 2. Criar o Bem com a nova estrutura de conformidade
                    BemPatrimonial.objects.create(
                        patrimonio_doador=dados.get('Nº Patrimônio'),
                        produto_categoria=dados.get('Produto'),
                        descricao=dados.get('Descrição'),
                        valor=limpar_valor(dados.get('Valor')),
                        projeto=projeto,
                        nota_fiscal=dados.get('NF'),
                        # Mapeamento automático para os novos campos
                        # Por padrão, itens importados da FAEPI entram como NOVO/ATIVO
                        estado_conservacao='NOVO', 
                        status_operacional='ATIVO'
                    )

    print(f"--- Importação Concluída: {BemPatrimonial.objects.count()} bens processados ---")

if __name__ == '__main__':
    importar()
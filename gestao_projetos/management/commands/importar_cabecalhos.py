import os
import pandas as pd
from datetime import datetime
from django.conf import settings
from django.db import transaction
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from cadastros.models import ProjetoPDI, BolsistaProjeto
from gestao_projetos.models import RelatorioAtividade

class Command(BaseCommand):
    """
    Comando customizado para ingestão de dados em lote de Bolsistas e Relatórios.
    Execução: python manage.py importar_cabecalhos
    """
    help = 'Importa os cabeçalhos dos relatórios de atividades via planilha Excel.'

    def parse_data_range(self, date_string, year_format='%Y'):
        """
        Converte strings como '25/06/2026 a 28/02/2027' para objetos date do Python.
        """
        try:
            partes = date_string.split(' a ')
            if len(partes) != 2:
                raise ValueError
            data_inicio = datetime.strptime(partes[0].strip(), f'%d/%m/{year_format}').date()
            data_fim = datetime.strptime(partes[1].strip(), f'%d/%m/{year_format}').date()
            return data_inicio, data_fim
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao converter período '{date_string}': {e}"))
            return None, None

    @transaction.atomic
    def handle(self, *args, **options):
        # Defina o caminho absoluto seguro
        filepath = os.path.join(settings.BASE_DIR, 'relatorios-atividades-cabecalhos.xlsx')
        
        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR(f"Arquivo não encontrado: {filepath}"))
            return

        df = pd.read_excel(filepath, sheet_name='relatorios-de-atividade')
        
        # Recupera um usuário administrador do sistema para assumir a autoria dos rascunhos criados
        usuario_sistema = User.objects.filter(is_superuser=True).first()
        if not usuario_sistema:
            self.stdout.write(self.style.ERROR("Nenhum superusuário encontrado para atribuir como 'criado_por'."))
            return

        registros_criados = 0

        for index, row in df.iterrows():
            # 1. Parse das datas de contratação do bolsista PRIMEIRO
            inicio_contrato, fim_contrato = self.parse_data_range(row['bolsista_contratacao'], '%Y')
            
            if not inicio_contrato:
                continue

            # 2. Recupera ou cria o Projeto PDI atrelado ao Convênio
            # Utiliza as datas do bolsista como fallback temporário para satisfazer a restrição NOT NULL do banco
            projeto, projeto_criado = ProjetoPDI.objects.get_or_create(
                convenio=row['convenio_numero'],
                defaults={
                    'nome': 'Projeto Bio Caroço',
                    'vigencia_inicio': inicio_contrato,
                    'vigencia_fim': fim_contrato,
                    'plano_inicio': inicio_contrato,
                    'plano_fim': fim_contrato,
                }
            )
            
            if projeto_criado:
                self.stdout.write(self.style.WARNING(
                    f"Aviso: Projeto '{projeto.convenio}' criado automaticamente com datas provisórias. "
                    f"Atualize os dados oficiais no painel de Cadastros posteriormente."
                ))

            # 3. Inserção ou atualização do Bolsista (Fonte Única de Verdade)
            bolsista, _ = BolsistaProjeto.objects.get_or_create(
                cpf=row['bolsista_cpf'],
                projeto=projeto,
                defaults={
                    'nome_completo': row['bolsista_nome'],
                    'rg': str(row['bolsista_rg']),
                    'email': row['bolsista_email'],
                    'telefone': row['bolsista_fone'],
                    'funcao': row['bolsista_funcao'],
                    'termo_bolsa': row['bolsista_termodebolsa'],
                    'data_inicio': inicio_contrato,
                    'data_fim': fim_contrato,
                    'carga_horaria_total': int(row['bolsista_ch'])
                }
            )

            # 4. Parse das datas do período da parcela (formato com ano de 2 dígitos)
            inicio_parcela, fim_parcela = self.parse_data_range(row['parcela_periodo'], '%y')
            
            if not inicio_parcela:
                continue

            # 5. Inserção do Relatório de Atividade (status RASCUNHO padrão)
            _, relatorio_criado = RelatorioAtividade.objects.get_or_create(
                bolsista=bolsista,
                parcela=int(row['bolsa_parcela']),
                defaults={
                    'criado_por': usuario_sistema,
                    'macroentrega': str(row['macroentrega_numero']),
                    'periodo_inicio': inicio_parcela,
                    'periodo_fim': fim_parcela,
                    'carga_horaria_periodo': int(row['parcela_ch'])
                }
            )

            if relatorio_criado:
                registros_criados += 1

        self.stdout.write(self.style.SUCCESS(f"Importação concluída. {registros_criados} relatórios gerados com sucesso."))
        
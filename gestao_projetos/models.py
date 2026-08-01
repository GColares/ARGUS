# gestao_projetos/models.py
from django.db import models
from django.contrib.auth.models import User
from cadastros.models import MembroEquipe, ProjetoPDI, BolsistaProjeto, AtividadePlanoAcao

class RelatorioAtividade(models.Model):
    """
    Armazena o cabeçalho e os metadados do relatório de atividades da parcela.
    A validação de permissão (RBAC via MembroEquipe) deve ocorrer exclusivamente nas views, 
    garantindo que apenas membros alocados no projeto manipulem o documento.
    """
    STATUS_CHOICES = [
        ('RASCUNHO', 'Rascunho'),
        ('CONCLUIDO', 'Pronto para Download'),
    ]

    # Utilização de Lazy Reference ('app.Model') para evitar circular imports 
    # com o módulo de cadastros, que atua como nossa Fonte Única de Verdade.
    termo_bolsa = models.ForeignKey(
        'cadastros.TermoBolsa', 
        on_delete=models.CASCADE, 
        related_name='relatorios_termo',
        null=True,  # Para manter compatibilidade durante a migração
        blank=True
    )
    # BolsistaProjeto mantido temporariamente apenas por compatibilidade (será descontinuado)
    bolsista = models.ForeignKey(
        'cadastros.BolsistaProjeto', 
        on_delete=models.SET_NULL, 
        related_name='relatorios_bolsista',
        null=True,
        blank=True
    )
    criado_por = models.ForeignKey(User, on_delete=models.PROTECT)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='RASCUNHO')
    
    versao = models.PositiveIntegerField(default=1, verbose_name="Versão do Relatório")
    
    parcela = models.PositiveIntegerField(verbose_name="Número da Parcela")
    macroentrega = models.CharField(max_length=50, blank=True, null=True, verbose_name="Ref. Macro Entrega")
    periodo_inicio = models.DateField(verbose_name="Período Início")
    periodo_fim = models.DateField(verbose_name="Período Fim")
    carga_horaria_periodo = models.PositiveIntegerField(verbose_name="Carga Horária do Período")
    
    ocorrencias = models.TextField(
        blank=True, 
        null=True, 
        help_text="Injetado no bloco 'Ocorrências' do relatório. Deixe em branco para 'Nenhuma'."
    )

    # Parecer do Coordenador (Requisito de Governança para atesto por Servidor Efetivo)
    cumpriu_carga_horaria = models.BooleanField(default=True, verbose_name="Cumpriu com a Carga Horária")
    parecer_coordenador = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Demais informações pertinentes (Parecer)"
    )
    
    class Meta:
        db_table = 'argus_relatorio_atividade'
        unique_together = ('termo_bolsa', 'parcela', 'versao')
        verbose_name = 'Relatório de Atividade'
        verbose_name_plural = 'Relatórios de Atividades'

    def __str__(self):
        # Proteção contra erros ao tentar ler dados vazios
        if self.termo_bolsa:
            nome = self.termo_bolsa.bolsista_nome
        elif self.bolsista_id:
            nome = self.bolsista.nome_completo
        else:
            nome = 'Desconhecido'
        return f"Relatório Parcela {self.parcela} (v{self.versao}) - {nome}"


class ItemAtividade(models.Model):
    """
    Refatorado para representar a 'Tarefa' executada pelo bolsista, 
    obrigatoriamente subordinada a uma Atividade-Mãe do Plano de Ação.
    """
    relatorio = models.ForeignKey('RelatorioAtividade', on_delete=models.CASCADE, related_name='itens_atividade')

    atividade_mae = models.ForeignKey(
        AtividadePlanoAcao, 
        on_delete=models.PROTECT, 
        related_name='tarefas_executadas',
        null=True,
        blank=True
    )
    
    periodo_execucao = models.CharField(max_length=50) # Ex: 01/07 a 15/07
    descricao = models.TextField(verbose_name="Descrição da Tarefa Realizada")
    carga_horaria_percentual = models.CharField(max_length=10, default='100%')

    @property
    def numero_atividade(self):
        return self.atividade_mae.numero if self.atividade_mae else 'N/I'
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
        ('PENDENTE', 'Aguardando Assinatura'),
        ('CONCLUIDO', 'Assinado / Concluído'),
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
    
    conta_pagamento = models.ForeignKey(
        'cadastros.ContaBancaria',
        on_delete=models.SET_NULL,
        related_name='relatorios_pagos',
        null=True,
        blank=True,
        verbose_name="Conta Pagadora / Fonte de Recurso"
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
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDENTE')
    
    versao = models.PositiveIntegerField(default=1, verbose_name="Versão do Relatório")
    
    parcela_referencia = models.ForeignKey(
        'cadastros.Parcela', 
        on_delete=models.CASCADE, 
        related_name='relatorios', 
        verbose_name="Parcela de Referência",
        null=True
    )
    macroentregas = models.ManyToManyField('cadastros.Macroentrega', blank=True, related_name='relatorios', verbose_name="Macroentregas Associadas")
    periodo_inicio = models.DateField(verbose_name="Período Início")
    periodo_fim = models.DateField(verbose_name="Período Fim")
    carga_horaria_periodo = models.PositiveIntegerField(verbose_name="Carga Horária do Período")
    
    ocorrencias = models.TextField(
        blank=True, 
        null=True, 
        help_text="Injetado no bloco 'Ocorrências' do relatório. Deixe em branco para 'Nenhuma'."
    )
    
    arquivo_pdf = models.FileField(
        upload_to='projetos/relatorios_assinados/', 
        null=True, 
        blank=True, 
        verbose_name="Relatório Assinado (PDF)"
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
        unique_together = ('termo_bolsa', 'parcela_referencia')
        verbose_name = 'Relatório de Atividade'
        verbose_name_plural = 'Relatórios de Atividades'

    def __str__(self):
        # Proteção contra erros ao tentar ler dados vazios
        if self.termo_bolsa:
            nome = self.termo_bolsa.bolsista.nome
        elif self.bolsista_id: # type: ignore
            nome = self.bolsista.nome_completo
        else:
            nome = 'Desconhecido'
        return f"Relatório Parcela {self.parcela_referencia.numero if self.parcela_referencia else '?'} (v{self.versao}) - {nome}"


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


# =====================================================================
# GERENCIADOR DE MATRIZES DOCX DO CONVENIAR / FAEPI (Passo 4)
# =====================================================================

class TemplateDocumentoConveniar(models.Model):
    """
    Biblioteca de matrizes DOCX institucionais utilizadas pelo Conveniar/FAEPI.
    Permite versionamento e manutenção centralizada sem alterar o código.
    """
    TIPO_CHOICES = [
        ('OFICIO_EQUIPE', 'Ofício de Pagamento da Equipe'),
        ('OFICIO_COORDENADOR', 'Ofício de Pagamento do Coordenador'),
        ('RECIBO', 'Recibo de Pagamento'),
        ('DECLARACAO', 'Declaração de Vínculo'),
        ('OUTRO', 'Outro Documento Institucional'),
    ]

    nome = models.CharField(max_length=200, verbose_name="Nome do Template")
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, verbose_name="Tipo do Documento")
    descricao = models.TextField(verbose_name="Descrição / Orientações de Uso")
    arquivo_docx = models.FileField(
        upload_to='templates_conveniar/',
        verbose_name="Arquivo DOCX (Matriz)"
    )
    versao = models.CharField(max_length=20, default='1.0', verbose_name="Versão")
    ativo = models.BooleanField(default=True, verbose_name="Template Ativo")
    tags_disponiveis = models.TextField(
        blank=True, null=True,
        verbose_name="Tags Disponíveis",
        help_text="Lista das variáveis {{ tag }} suportadas por este template, uma por linha."
    )
    atualizado_em = models.DateTimeField(auto_now=True)
    atualizado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='templates_atualizados', verbose_name="Atualizado por"
    )

    class Meta:
        verbose_name = "Template de Documento Conveniar"
        verbose_name_plural = "Templates de Documentos Conveniar"
        ordering = ['-atualizado_em']

    def __str__(self):
        return f"{self.nome} (v{self.versao}) — {self.get_tipo_display()}"


class OficioSolicitacao(models.Model):
    """
    Rastreia cada ofício requisitório emitido pelo ARGUS para o Conveniar/FAEPI.
    Garante idempotência: uma parcela não pode constar em dois ofícios da mesma competência.
    """
    TIPO_CHOICES = [
        ('EQUIPE', 'Ofício de Pagamento da Equipe'),
        ('COORDENADOR', 'Ofício de Pagamento do Coordenador'),
    ]

    projeto = models.ForeignKey(
        'cadastros.ProjetoPDI', on_delete=models.CASCADE,
        related_name='oficios_solicitacao', verbose_name="Projeto"
    )
    template_utilizado = models.ForeignKey(
        TemplateDocumentoConveniar, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='oficios_gerados', verbose_name="Template Utilizado"
    )
    numero_sequencial = models.PositiveIntegerField(verbose_name="Número Sequencial")
    ano = models.PositiveIntegerField(verbose_name="Ano do Ofício")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo do Ofício")
    competencia = models.DateField(verbose_name="Mês de Competência (dia 1)")

    # Signatários
    signatario_nome = models.CharField(max_length=255, verbose_name="Nome do Signatário (Requisitante)")
    signatario_cargo = models.CharField(max_length=255, verbose_name="Cargo do Signatário")
    coordenador_is_diretor_campus = models.BooleanField(
        default=False,
        verbose_name="Coordenador é Diretor-Geral de Campus?",
        help_text="Quando True, o Reitor assina como Requisitante em vez do Diretor do Polo."
    )
    visto_nome = models.CharField(max_length=255, blank=True, verbose_name="Nome do Visto (Ciência)")
    visto_cargo = models.CharField(max_length=255, blank=True, verbose_name="Cargo do Visto")

    # Parcelas despachadas neste ofício
    parcelas = models.ManyToManyField(
        'cadastros.Parcela',
        related_name='oficios_conveniar',
        blank=True,
        verbose_name="Parcelas Incluídas"
    )

    # Arquivos gerados
    arquivo_docx = models.FileField(
        upload_to='oficios_conveniar/',
        null=True, blank=True,
        verbose_name="Ofício Gerado (.docx)"
    )
    arquivo_pdf = models.FileField(
        upload_to='oficios_conveniar/',
        null=True, blank=True,
        verbose_name="Ofício Assinado (.pdf)"
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='oficios_criados', verbose_name="Criado por"
    )

    class Meta:
        verbose_name = "Ofício de Solicitação"
        verbose_name_plural = "Ofícios de Solicitação"
        ordering = ['-criado_em']
        unique_together = ('projeto', 'numero_sequencial', 'ano')

    def __str__(self):
        return f"Ofício {self.numero_sequencial}/{self.ano} — {self.get_tipo_display()} — {self.projeto.nome}"
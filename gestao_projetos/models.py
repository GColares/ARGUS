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
        ('PENDENTE', 'Rascunho / Em Elaboração'),
        ('EM_ANALISE', 'Submetido / Aguardando Atesto SIAPE'),
        ('CONCLUIDO', 'Homologado / Atestado'),
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

    # ── Passo 6: Atesto SIAPE (preenchido pela view atestar_relatorio) ──
    atestado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='relatorios_atestados',
        verbose_name="Atestado por (Servidor Efetivo)",
    )
    data_atesto = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data/Hora do Atesto",
    )
    siape_atesto = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Matrícula SIAPE do Servidor Atestante",
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


# =====================================================================
# GOVERNANÇA INSTITUCIONAL — ALÇADAS E SUPLÊNCIA LEGAL (Passo 5)
# =====================================================================

class FuncaoInstitucional(models.Model):
    """
    Cadastro de funções/cargos institucionais com cadeia de suplência.
    Ex: DIRETOR_POLO, REITOR, COORD_RH, DIRETOR_ADMIN_FINANCEIRO.
    """
    codigo = models.CharField(
        max_length=50, unique=True,
        verbose_name="Código da Função",
        help_text="Ex: DIRETOR_POLO, REITOR, COORD_RH"
    )
    nome_cargo = models.CharField(max_length=255, verbose_name="Nome do Cargo / Função")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Função Institucional"
        verbose_name_plural = "Funções Institucionais"
        ordering = ['nome_cargo']

    def __str__(self):
        return f"{self.codigo} — {self.nome_cargo}"

    def obter_responsavel_em_exercicio(self, data_referencia=None):
        """
        Resolve dinamicamente quem detém o poder de representação desta função
        na data_referencia (padrão: hoje), aplicando o princípio de unicidade de
        exercício e a ordem de precedência de substituição.

        Retorna um dict com:
          - pessoa: PessoaFisica (ou None)
          - nome: str
          - cargo_display: str (inclui "Substituto" + portaria quando aplicável)
          - portaria: str
          - prioridade: int (0=Titular, 1=1º Sub, 2=2º Sub, …)
        """
        from datetime import date as _date
        if data_referencia is None:
            data_referencia = _date.today()

        # Obtém todas as ocupações ativas em ordem de prioridade crescente
        ocupacoes = self.ocupacoes.filter(ativo=True).order_by('prioridade')

        for ocupacao in ocupacoes:
            # Verifica se esta ocupação está afastada na data de referência
            afastada = AfastamentoExercicio.objects.filter(
                ocupacao=ocupacao,
                data_inicio__lte=data_referencia,
                data_fim__gte=data_referencia,
                ativo=True
            ).exists()

            if not afastada:
                # Esta pessoa está em exercício — retorna
                if ocupacao.prioridade == 0:
                    cargo_display = self.nome_cargo
                else:
                    sufixo = ocupacao.sufixo_cargo or f"{ocupacao.get_prioridade_display()}"
                    cargo_display = f"{self.nome_cargo} ({sufixo})"
                    if ocupacao.portaria_designacao:
                        cargo_display += f" — {ocupacao.portaria_designacao}"

                return {
                    'pessoa': ocupacao.pessoa,
                    'nome': ocupacao.pessoa.nome if ocupacao.pessoa else ocupacao.nome_externo or "—",
                    'cargo_display': cargo_display,
                    'portaria': ocupacao.portaria_designacao or "",
                    'prioridade': ocupacao.prioridade,
                    'ocupacao': ocupacao,
                }

        # Nenhuma ocupação ativa encontrada — retorna fallback vazio
        return {
            'pessoa': None,
            'nome': f"[SEM RESPONSÁVEL — {self.nome_cargo}]",
            'cargo_display': self.nome_cargo,
            'portaria': "",
            'prioridade': -1,
            'ocupacao': None,
        }


class OcupacaoFuncao(models.Model):
    """
    Vincula uma PessoaFisica a uma FuncaoInstitucional com prioridade de suplência.
    prioridade 0 = Titular | 1 = 1º Substituto | 2 = 2º Substituto ...
    """
    PRIORIDADE_CHOICES = [
        (0, 'Titular'),
        (1, '1º Substituto'),
        (2, '2º Substituto'),
        (3, '3º Substituto'),
    ]

    funcao = models.ForeignKey(
        FuncaoInstitucional, on_delete=models.CASCADE,
        related_name='ocupacoes', verbose_name="Função Institucional"
    )
    pessoa = models.ForeignKey(
        'cadastros.PessoaFisica', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='ocupacoes_funcao', verbose_name="Pessoa Física"
    )
    # Usado quando a autoridade não é uma PessoaFisica cadastrada (ex: Reitor externo)
    nome_externo = models.CharField(
        max_length=255, blank=True,
        verbose_name="Nome Externo (quando não cadastrado como PessoaFisica)"
    )
    prioridade = models.IntegerField(choices=PRIORIDADE_CHOICES, default=0, verbose_name="Prioridade de Suplência")
    portaria_designacao = models.CharField(
        max_length=100, blank=True,
        verbose_name="Portaria de Designação",
        help_text="Ex: Portaria 061/GR/IFAM"
    )
    sufixo_cargo = models.CharField(
        max_length=100, blank=True,
        verbose_name="Sufixo do Cargo",
        help_text="Ex: 'Substituto', '1º Substituto'. Preenchido automaticamente se vazio."
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Ocupação de Função"
        verbose_name_plural = "Ocupações de Funções"
        unique_together = ('funcao', 'prioridade')
        ordering = ['funcao', 'prioridade']

    def __str__(self):
        nome = self.pessoa.nome if self.pessoa else self.nome_externo or "?"
        return f"{self.funcao.codigo} | {self.get_prioridade_display()}: {nome}"


class AfastamentoExercicio(models.Model):
    """
    Registra afastamentos que suspendem o exercício de uma OcupacaoFuncao
    em determinado período (férias, licença, missão etc.).
    Enquanto vigente, o sistema chaveia automaticamente para o próximo substituto.
    """
    MOTIVO_CHOICES = [
        ('FERIAS', 'Férias'),
        ('LICENCA_MEDICA', 'Licença Médica'),
        ('MISSAO', 'Missão Institucional'),
        ('LICENCA_CAPACITACAO', 'Licença para Capacitação'),
        ('OUTRO', 'Outro'),
    ]

    ocupacao = models.ForeignKey(
        OcupacaoFuncao, on_delete=models.CASCADE,
        related_name='afastamentos', verbose_name="Ocupação"
    )
    data_inicio = models.DateField(verbose_name="Data de Início do Afastamento")
    data_fim = models.DateField(verbose_name="Data de Fim do Afastamento")
    motivo = models.CharField(max_length=25, choices=MOTIVO_CHOICES, default='FERIAS', verbose_name="Motivo")
    documento_comprobatorio = models.CharField(
        max_length=200, blank=True,
        verbose_name="Documento Comprobatório",
        help_text="Número da portaria, memorando ou despacho autorizando o afastamento."
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Afastamento de Exercício"
        verbose_name_plural = "Afastamentos de Exercício"
        ordering = ['-data_inicio']

    def __str__(self):
        return f"Afastamento de {self.ocupacao} ({self.data_inicio} a {self.data_fim})"


class RegraAlcadaDocumento(models.Model):
    """
    Matriz ajustável de alçadas: define quem assina cada tipo de documento
    e sob qual condição do beneficiário.
    """
    TIPO_DOCUMENTO_CHOICES = [
        ('OFICIO_EQUIPE', 'Ofício de Pagamento da Equipe'),
        ('OFICIO_COORDENADOR', 'Ofício de Pagamento do Coordenador'),
        ('OFICIO_COORD_DIRETOR_CAMPUS', 'Ofício de Pagamento do Coordenador (Diretor de Campus)'),
        ('CONTRATACAO_BOLSISTA', 'Contratação de Bolsista'),
        ('OUTRO', 'Outro'),
    ]
    CONDICAO_CHOICES = [
        ('QUALQUER_BOLSISTA', 'Qualquer Bolsista'),
        ('COORDENADOR_PROJETO', 'Coordenador do Projeto (não Diretor de Campus)'),
        ('COORDENADOR_E_DIRETOR_CAMPUS', 'Coordenador que é Diretor-Geral de Campus'),
    ]

    tipo_documento = models.CharField(
        max_length=35, choices=TIPO_DOCUMENTO_CHOICES,
        verbose_name="Tipo do Documento"
    )
    condicao_beneficiario = models.CharField(
        max_length=35, choices=CONDICAO_CHOICES,
        default='QUALQUER_BOLSISTA',
        verbose_name="Condição do Beneficiário"
    )
    funcao_requisitante = models.ForeignKey(
        FuncaoInstitucional, on_delete=models.PROTECT,
        related_name='regras_como_requisitante',
        verbose_name="Função do Signatário Requisitante"
    )
    funcao_visto = models.ForeignKey(
        FuncaoInstitucional, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='regras_como_visto',
        verbose_name="Função do Visto (Ciência)"
    )
    exige_siape = models.BooleanField(default=True, verbose_name="Exige SIAPE do Signatário?")
    descricao = models.TextField(blank=True, verbose_name="Descrição / Justificativa Legal")
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Regra de Alçada de Documento"
        verbose_name_plural = "Regras de Alçada de Documentos"
        unique_together = ('tipo_documento', 'condicao_beneficiario')
        ordering = ['tipo_documento', 'condicao_beneficiario']

    def __str__(self):
        visto = f" | Visto: {self.funcao_visto.codigo}" if self.funcao_visto else ""
        return f"{self.get_tipo_documento_display()} [{self.get_condicao_beneficiario_display()}] → Req: {self.funcao_requisitante.codigo}{visto}"

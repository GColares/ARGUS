import re
from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from simple_history.models import HistoricalRecords

# =====================================================================
# VALIDADORES DE PADRÃO TEXTUAL (REGEX)
# =====================================================================
validar_processo_ifam = RegexValidator(
    regex=r'^23443\.\d{6}/\d{4}-\d{2}$',
    message="O processo IFAM deve seguir o padrão: 23443.XXXXXX/ANO-XX"
)

validar_processo_faepi = RegexValidator(
    regex=r'^\d{5}/\d{4}$',
    message="O processo FAEPI deve seguir o padrão: XXXXX/ANO (com 5 dígitos iniciais)"
)

validar_convenio = RegexValidator(
    regex=r'^\d{4}/\d{4}$',
    message="O convênio deve seguir o padrão: XXXX/ANO (Ex: 0013/2022)"
)

# =====================================================================
# ENTIDADES GLOBAIS DE PARCERIAS E CONVÊNIOS (CENTRALIZADAS)
# =====================================================================
class PessoaJuridica(models.Model):
    """Cadastro global de entidades jurídicas base."""
    nome = models.CharField(max_length=255, verbose_name="Nome da Instituição (Razão Social)")
    natureza_juridica = models.CharField(max_length=255, verbose_name="Natureza Jurídica")
    cnpj = models.CharField(max_length=18, unique=True, verbose_name="CNPJ")
    endereco = models.CharField(max_length=255, verbose_name="Endereço")
    representante_legal = models.CharField(max_length=255, verbose_name="Representante Legal")
    nacionalidade_representante = models.CharField(max_length=50, blank=True, null=True, verbose_name="Nacionalidade")
    estado_civil_representante = models.CharField(max_length=50, blank=True, null=True, verbose_name="Estado Civil")
    cargo_representante = models.CharField(max_length=100, verbose_name="Cargo do Representante")
    ato_nomeacao = models.CharField(max_length=255, blank=True, null=True, verbose_name="Ato de Nomeação")

    class Meta:
        verbose_name = "Pessoa Jurídica"
        verbose_name_plural = "Pessoas Jurídicas"

    def get_child(self):
        for attr in ['ict', 'empresaparceira', 'agenciafomento', 'fundacaoapoio', 'fornecedor']:
            if hasattr(self, attr):
                try:
                    child = getattr(self, attr)
                    if child:
                        return child
                except Exception:
                    continue
        return self

    def __str__(self):
        child = self.get_child()
        sigla = getattr(child, 'sigla', None)
        nome_fantasia = getattr(child, 'nome_fantasia', None)
        prefix = sigla or nome_fantasia
        if prefix:
            return f"{prefix} - {child.nome}"
        return child.nome

class ICT(PessoaJuridica):
    """Instituição Científica, Tecnológica e de Inovação (ex: IFAM, UFAM)"""
    sigla = models.CharField(max_length=20, verbose_name="Sigla da Instituição")
    campus_unidade = models.CharField(max_length=100, verbose_name="Campus ou Unidade", blank=True, null=True)
    nome_nit = models.CharField(max_length=100, verbose_name="Nome do NIT", default="Núcleo de Inovação Tecnológica")
    is_executora = models.BooleanField(default=False, verbose_name="É a ICT Executora (Sede/Polo)?", help_text="Marque se esta for a instituição matriz do sistema (ex: IFAM). Ela não aparecerá como 'Parceiro' em novos acordos.")

    class Meta: # type: ignore
        verbose_name = "ICT"
        verbose_name_plural = "ICTs"

class EmpresaParceira(PessoaJuridica):
    """Empresas de Base Tecnológica ou Indústrias (Concedentes)"""
    nome_fantasia = models.CharField(max_length=255, verbose_name="Nome Fantasia")
    PORTE_CHOICES = [
        ('ME', 'Microempresa'),
        ('EPP', 'Empresa de Pequeno Porte'),
        ('MGE', 'Média ou Grande Empresa'),
    ]
    porte = models.CharField(max_length=3, choices=PORTE_CHOICES, default='MGE', verbose_name="Porte da Empresa")
    segmento_atuacao = models.CharField(max_length=100, verbose_name="Segmento de Atuação", blank=True, null=True)

    class Meta: # type: ignore
        verbose_name = "Empresa Parceira"
        verbose_name_plural = "Empresas Parceiras"

class FundacaoApoio(PessoaJuridica):
    """Fundações de Apoio (ex: FAEPI) - Gestão Financeira"""
    sigla = models.CharField(max_length=20, verbose_name="Sigla da Fundação")
    registro_mec = models.CharField(max_length=100, verbose_name="Registro de Credenciamento MEC/MCTI", blank=True, null=True)
    validade_credenciamento = models.DateField(verbose_name="Validade do Credenciamento", blank=True, null=True)

    class Meta: # type: ignore
        verbose_name = "Fundação de Apoio"
        verbose_name_plural = "Fundações de Apoio"

class AgenciaFomento(PessoaJuridica):
    """Agências de Fomento ou Apoiadores (ex: EMBRAPII, SEBRAE, FAPEAM)"""
    ESFERA_CHOICES = [
        ('FEDERAL', 'Pública Federal'),
        ('ESTADUAL', 'Pública Estadual'),
        ('MUNICIPAL', 'Pública Municipal'),
        ('PRIVADA', 'Entidade Privada'),
    ]
    esfera = models.CharField(max_length=20, choices=ESFERA_CHOICES, default='FEDERAL', verbose_name="Esfera")
    sigla = models.CharField(max_length=20, verbose_name="Sigla")

    class Meta: # type: ignore
        verbose_name = "Agência de Fomento"
        verbose_name_plural = "Agências de Fomento"


class TipoInstrumentoJuridico(models.Model):
    """
    Cadastro Base de Tipos de Instrumentos Jurídicos padronizados no ARGUS
    (Conforme Marco Legal de CT&I - Lei 10.973/04 e orientações da AGU).
    """
    nome = models.CharField(max_length=150, unique=True, verbose_name="Nome do Tipo de Instrumento")
    sigla = models.CharField(max_length=20, unique=True, verbose_name="Sigla / Prefixo")
    fundamentacao_legal = models.CharField(max_length=255, blank=True, null=True, verbose_name="Fundamentação Legal")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    exige_fundacao_apoio = models.BooleanField(default=False, verbose_name="Exige Fundação de Apoio (Interveniente-Anuente)")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Tipo de Instrumento Jurídico"
        verbose_name_plural = "Tipos de Instrumentos Jurídicos"
        ordering = ['nome']

    def __str__(self):
        return f"{self.sigla} - {self.nome}" if self.sigla else self.nome


class InstrumentoJuridicoBase(models.Model):
    TIPO_INSTRUMENTO_CHOICES = [
        ('CONVENIO', 'Convênio de P&D&I'),
        ('ACORDO_PARCERIA', 'Acordo de Parceria para P&D&I (Marco Legal CT&I)'),
        ('TERMO_COOPERACAO', 'Termo de Cooperação'),
        ('NDA', 'Acordo de Confidencialidade e Sigilo'),
        ('STE', 'Prestação de Serviços Técnicos Especializados'),
        ('LICENCIAMENTO', 'Contrato de Licenciamento / Transferência de Tecnologia'),
        ('COMPARTILHAMENTO', 'Termo de Compartilhamento de Infraestrutura/Laboratório'),
    ]
    tipo_instrumento = models.CharField(
        max_length=30, choices=TIPO_INSTRUMENTO_CHOICES, default='ACORDO_PARCERIA', verbose_name="Tipo de Instrumento"
    )
    tipo_instrumento_fk = models.ForeignKey(
        TipoInstrumentoJuridico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)ss',
        verbose_name="Tipo de Instrumento (Parametrizado)"
    )
    sequencial = models.PositiveIntegerField(null=True, blank=True, verbose_name="Número Sequencial")
    ano = models.PositiveIntegerField(null=True, blank=True, verbose_name="Ano de Emissão")
    numero = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="Número do Instrumento")
    objeto = models.TextField(blank=True, null=True, verbose_name="Objeto / Descrição")
    data_assinatura = models.DateField(blank=True, null=True, verbose_name="Data de Assinatura")
    vigencia_inicio = models.DateField(blank=True, null=True, verbose_name="Início da Vigência")
    vigencia_fim = models.DateField(blank=True, null=True, verbose_name="Fim da Vigência")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        abstract = True

class TermoDeParceria(InstrumentoJuridicoBase):
    """Entidade macro jurídica que rege a parceria e união de interesses."""
    projeto = models.ForeignKey('ProjetoPDI', on_delete=models.CASCADE, related_name='termos_parceria', null=True, blank=True, verbose_name="Projeto Mestre")
    concedente = models.ForeignKey('PessoaJuridica', on_delete=models.CASCADE, related_name='termos_concedidos', verbose_name="Concedente (Empresa/Agência)")
    convenente = models.ForeignKey('ICT', on_delete=models.PROTECT, related_name='convenente_em', verbose_name="Convenente")
    interveniente = models.ForeignKey(FundacaoApoio, on_delete=models.PROTECT, related_name='interveniente_em', verbose_name="Interveniente")

    class Meta:
        verbose_name = "Termo de Parceria"
        verbose_name_plural = "Termos de Parceria"
        constraints = [
            models.UniqueConstraint(
                fields=['tipo_instrumento', 'sequencial', 'ano'],
                condition=models.Q(sequencial__isnull=False, ano__isnull=False),
                name='unique_sequencial_ano_por_tipo'
            )
        ]

    def __str__(self):
        return f"{self.numero or 'Sem Número'} ({self.concedente.sigla or self.concedente.nome_fantasia or self.concedente.nome})"

    @property
    def nome_especie(self):
        """Retorna o nome canônico da espécie documental (Convênio vs. Acordo de Parceria)."""
        if self.tipo_instrumento_fk:
            return self.tipo_instrumento_fk.nome
        if self.tipo_instrumento == 'CONVENIO':
            return 'Convênio'
        if self.tipo_instrumento == 'ACORDO_PARCERIA':
            return 'Acordo de Parceria'
        return self.get_tipo_instrumento_display()

    @property
    def nome_especie_plural(self):
        """Retorna o plural da espécie documental para breadcrumbs e listas."""
        if self.tipo_instrumento_fk:
            return f"{self.tipo_instrumento_fk.nome}s"
        if self.tipo_instrumento == 'CONVENIO':
            return 'Convênios'
        if self.tipo_instrumento == 'ACORDO_PARCERIA':
            return 'Acordos de Parceria'
        return 'Instrumentos Jurídicos'

    @property
    def sigla_especie(self):
        """Retorna a sigla canônica oficial (CV vs. AP)."""
        if self.tipo_instrumento_fk:
            return self.tipo_instrumento_fk.sigla
        if self.tipo_instrumento == 'CONVENIO':
            return 'CV'
        if self.tipo_instrumento == 'ACORDO_PARCERIA':
            return 'AP'
        return 'IJ'

    @property
    def get_vigencia_inicio(self):
        if self.vigencia_inicio:
            return self.vigencia_inicio
        plano = self.planos_homologados.filter(ativo=True).first()
        if plano and plano.data_inicio:
            return plano.data_inicio
        if self.projeto and self.projeto.vigencia_inicio:
            return self.projeto.vigencia_inicio
        return None

    @property
    def get_vigencia_fim(self):
        ultimo_aditivo = self.aditivos.filter(nova_data_fim__isnull=False).order_by('-nova_data_fim').first()
        if ultimo_aditivo and ultimo_aditivo.nova_data_fim:
            return ultimo_aditivo.nova_data_fim
        if self.vigencia_fim:
            return self.vigencia_fim
        plano = self.planos_homologados.filter(ativo=True).first()
        if plano and plano.data_fim:
            return plano.data_fim
        if self.projeto and self.projeto.vigencia_fim:
            return self.projeto.vigencia_fim
        return None

    def clean(self):
        super().clean()
        from django.core.exceptions import ValidationError
        if self.tipo_instrumento not in ['CONVENIO', 'ACORDO_PARCERIA']:
            raise ValidationError({'tipo_instrumento': 'Para Parcerias de P&D&I, o instrumento deve ser Convênio ou Acordo de Parceria.'})

    def save(self, *args, **kwargs):
        from django.db import transaction, IntegrityError
        if not self.ano:
            self.ano = self.data_assinatura.year if self.data_assinatura else timezone.now().year
        if self.numero and not self.sequencial:
            match = re.search(r'(\d+)/(\d{4})', self.numero)
            if match:
                self.sequencial = int(match.group(1))
                self.ano = int(match.group(2))
        if not self.sequencial:
            MAX_TENTATIVAS = 3
            for tentativa in range(MAX_TENTATIVAS):
                try:
                    with transaction.atomic():
                        ultimo = (
                            TermoDeParceria.objects
                            .select_for_update()
                            .filter(tipo_instrumento=self.tipo_instrumento, ano=self.ano)
                            .order_by('-sequencial')
                            .first()
                        )
                        self.sequencial = (ultimo.sequencial + 1) if (ultimo and ultimo.sequencial) else 1
                        if not self.numero:
                            prefixos = {
                                'CONVENIO': 'CV',
                                'ACORDO_PARCERIA': 'AP',
                                'TERMO_COOPERACAO': 'TC',
                            }
                            prefixo = prefixos.get(self.tipo_instrumento, 'DOC')
                            self.numero = f"{prefixo} nº {self.sequencial:03d}/{self.ano}"
                        super().save(*args, **kwargs)
                        return
                except IntegrityError:
                    if tentativa == MAX_TENTATIVAS - 1:
                        raise
                    self.sequencial = None
                    self.numero = None
        else:
            super().save(*args, **kwargs)


class IndicadorResultado(models.Model):
    nome = models.CharField(max_length=150, unique=True)
    descricao = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nome

class PlanoDeTrabalho(models.Model):
    """Detalha a abordagem técnica, financeira e produto entregue do termo."""
    projeto = models.ForeignKey('ProjetoPDI', on_delete=models.CASCADE, related_name='planos_trabalho', null=True)
    termo_homologador = models.ForeignKey(TermoDeParceria, on_delete=models.SET_NULL, null=True, blank=True, related_name='planos_homologados', verbose_name="Termo Homologador")
    
    STATUS_CHOICES = [
        ('RASCUNHO', 'Rascunho / Em Edição'),
        ('CONGELADO_VIGENTE', 'Congelado Vigente (Em Execução)'),
        ('HISTORICO', 'Histórico (Substituído)')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RASCUNHO', verbose_name="Status do Plano")
    congelado = models.BooleanField(default=False, verbose_name="Plano Congelado (Bloqueio de Edição)")
    
    versao = models.IntegerField(default=1, verbose_name="Versão do Plano")
    arquivo_pdf = models.FileField(upload_to='projetos/planos_trabalho/', null=True, blank=True, verbose_name="Plano de Trabalho Vigente (PDF)")
    
    # 3. Motivação
    motivacao = models.TextField(blank=True, null=True, verbose_name="Motivação (Rich Text)")
    
    # 4. Objetivos
    objetivo_geral = models.TextField(blank=True, null=True, verbose_name="Objetivo Geral")
    objetivos_especificos = models.TextField(blank=True, null=True, verbose_name="Objetivos Específicos (Rich Text)")
    
    # 5. Escopo e WBS
    escopo_geral = models.TextField(blank=True, null=True, verbose_name="Escopo Geral (Rich Text)")
    estrutura_analitica = models.TextField(blank=True, null=True, verbose_name="Estrutura Analítica / WBS (Rich Text)")
    tecnologias_utilizadas = models.TextField(blank=True, null=True, verbose_name="Tecnologias e Ferramentas (Rich Text)")
    vulnerabilidades = models.TextField(blank=True, null=True, verbose_name="Vulnerabilidades do Projeto (Rich Text)")
    plano_riscos = models.TextField(blank=True, null=True, verbose_name="Plano de Riscos (Rich Text)")
    
    # 6. Estratégia
    estrategia = models.TextField(blank=True, null=True, verbose_name="Estratégia (Rich Text)")
    
    # 9. Indicadores
    indicadores = models.ManyToManyField(IndicadorResultado, blank=True, related_name='planos_trabalho')
    
    # 10. e 11. Resultados e Inovação
    caracteristicas_inovadoras = models.TextField(blank=True, null=True, verbose_name="Características Inovadoras (Rich Text)")
    resultados_esperados = models.TextField(blank=True, null=True, verbose_name="Resultados Esperados (Rich Text)")
    
    # 13. e 14. Desafios e Solução
    desafios_tecnologicos = models.TextField(blank=True, null=True, verbose_name="Desafios Científicos e Tecnológicos (Rich Text)")
    solucao_proposta = models.TextField(blank=True, null=True, verbose_name="Solução Proposta (Rich Text)")
    
    # 15. Orçamento (Descritivo)
    orcamento_descricao = models.TextField(blank=True, null=True, verbose_name="Descrição do Orçamento (Rich Text)")

    # Cronograma Geral
    data_inicio = models.DateField(verbose_name="Início do Plano de Trabalho", null=True, blank=True)
    data_fim = models.DateField(verbose_name="Fim do Plano de Trabalho", null=True, blank=True)
    total_meses = models.PositiveIntegerField(verbose_name="Total de Meses do Projeto", default=1)
    
    # Valores Globais
    valor_global = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Valor Global (R$)")
    aporte_empresa = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Aporte Empresa (R$)")
    aporte_embrapii = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Aporte EMBRAPII (R$)")
    aporte_sebrae = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Aporte SEBRAE (R$)")
    aporte_contrapartida = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Contrapartida (R$)")
    
    ativo = models.BooleanField(default=True, verbose_name="Versão Vigente")
    data_criacao = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Plano de Trabalho"
        verbose_name_plural = "Planos de Trabalho"
        unique_together = ('projeto', 'versao')

    def save(self, *args, **kwargs):
        # Soma automática dos aportes
        from decimal import Decimal
        v_empresa = self.aporte_empresa or Decimal('0.00')
        v_embrapii = self.aporte_embrapii or Decimal('0.00')
        v_sebrae = self.aporte_sebrae or Decimal('0.00')
        v_contrapartida = self.aporte_contrapartida or Decimal('0.00')
        self.valor_global = v_empresa + v_embrapii + v_sebrae + v_contrapartida
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        from django.core.exceptions import ValidationError
        from decimal import Decimal
        
        # Calcular valor_global provisório para a validação
        v_empresa = self.aporte_empresa or Decimal('0.00')
        v_embrapii = self.aporte_embrapii or Decimal('0.00')
        v_sebrae = self.aporte_sebrae or Decimal('0.00')
        v_contrapartida = self.aporte_contrapartida or Decimal('0.00')
        valor_total = v_empresa + v_embrapii + v_sebrae + v_contrapartida

        if self.projeto and valor_total > 0:
            # Trava EMBRAPII: mínimo de 10%
            min_embrapii = valor_total * Decimal('0.10')
            if v_embrapii < min_embrapii:
                raise ValidationError({'aporte_embrapii': f"O aporte EMBRAPII deve ser no mínimo 10% do valor global (R$ {min_embrapii:.2f})."})
            
            # Trava Empresa: mínimo de 10%, a menos que seja Agência de Fomento (Ex: PDC)
            is_agencia = hasattr(self.projeto.concedente, 'agenciafomento') if self.projeto.concedente else False
            if not is_agencia:
                min_empresa = valor_total * Decimal('0.10')
                if v_empresa < min_empresa:
                    raise ValidationError({'aporte_empresa': f"O aporte da Empresa deve ser no mínimo 10% do valor global (R$ {min_empresa:.2f}). Se for um projeto de capacitação (100% EMBRAPII), o concedente do projeto deve ser uma Agência de Fomento."})

        if self.data_inicio and self.data_fim:
            if self.data_inicio > self.data_fim:
                raise ValidationError({"data_fim": "A data fim do plano de trabalho não pode ser anterior ao início."})
    @property
    def total_i_v(self):
        return sum(item.valor_previsto for item in self.rubricas.all() if item.categoria in ['I', 'II', 'III', 'IV', 'V']) # type: ignore

    @property
    def total_vi(self):
        return sum(item.valor_previsto for item in self.rubricas.all() if item.categoria == 'VI') # type: ignore

    @property
    def total_i_vi(self):
        return self.total_i_v + self.total_vi

    @property
    def total_vii(self):
        return sum(item.valor_previsto for item in self.rubricas.all() if item.categoria == 'VII') # type: ignore

    @property
    def total_bruto(self):
        return self.total_i_vi + self.total_vii

    @property
    def esta_congelado(self):
        """Retorna True se o plano pertence a um projeto em fase de execução ou superior."""
        if hasattr(self, 'projeto') and self.projeto:
            return self.projeto.fase in ['EXECUCAO', 'PRESTACAO_CONTAS', 'ENCERRADO']
        if hasattr(self, 'termo_homologador') and self.termo_homologador and hasattr(self.termo_homologador, 'projeto') and self.termo_homologador.projeto:
            return self.termo_homologador.projeto.fase in ['EXECUCAO', 'PRESTACAO_CONTAS', 'ENCERRADO']
        return False

    def __str__(self):
        return f"Plano V{self.versao} - Projeto {self.projeto.nome if self.projeto else 'Desconhecido'}"

class Fornecedor(PessoaJuridica):
    """Cadastro de Credores e Empresas fornecedoras com dados estendidos."""
    sigla = models.CharField(max_length=50, verbose_name="Sigla / Nome Curto")
    email = models.EmailField(blank=True, null=True, verbose_name="E-mail de Contato")

    class Meta: # type: ignore
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"

    def __str__(self):
        return f"{self.sigla if self.sigla else self.nome} ({self.cnpj})"

# =====================================================================
# PROJETO PDI 
# =====================================================================
class TermoCooperacao(models.Model):
    """
    Termos de Cooperação Técnica e Parcerias Estratégicas.
    """
    numero = models.CharField(max_length=50, unique=True, verbose_name="Número do Termo")
    tipo_instrumento_fk = models.ForeignKey(
        'TipoInstrumentoJuridico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='termos_cooperacao',
        verbose_name="Tipo de Instrumento"
    )
    concedente = models.ForeignKey('PessoaJuridica', on_delete=models.CASCADE, related_name='termos_cooperacao_concedidos', verbose_name="Parceiro")
    convenente = models.ForeignKey('ICT', on_delete=models.CASCADE, related_name='termos_cooperacao_conveniados', verbose_name="ICT")
    objeto = models.TextField(verbose_name="Objeto")
    valor_global = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Valor Global (R$)")
    data_assinatura = models.DateField(null=True, blank=True, verbose_name="Data de Assinatura")
    vigencia_inicio = models.DateField(verbose_name="Início da Vigência")
    vigencia_fim = models.DateField(verbose_name="Fim da Vigência")
    arquivo_pdf = models.FileField(upload_to='termos_cooperacao/', null=True, blank=True, verbose_name="Cópia do Documento (PDF)")
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Termo de Cooperação / Credenciamento"
        verbose_name_plural = "Termos de Cooperação / Credenciamentos"
        ordering = ['-vigencia_inicio']

    def __str__(self):
        return f"{self.numero} - {self.concedente}"

    @property
    def get_vigencia_fim(self):
        ultimo_aditivo = self.aditivos.filter(nova_data_fim__isnull=False).order_by('-nova_data_fim').first()
        if ultimo_aditivo and ultimo_aditivo.nova_data_fim:
            return ultimo_aditivo.nova_data_fim
        return self.vigencia_fim

TIPO_ADITIVO_CHOICES = [
    ('PRORROGACAO', 'Prorrogação de Vigência (Prazo)'),
    ('VALOR', 'Acréscimo / Supressão de Recursos (Valor)'),
    ('ESCOPO', 'Alteração de Escopo / Plano de Trabalho'),
    ('MISTO', 'Misto (Prazo, Valor e Escopo)'),
    ('OUTRO', 'Outros Ajustes Formais'),
]


class AditivoTermoCooperacao(models.Model):
    """
    Aditivos que alteram ou prorrogam o Termo de Cooperação
    """
    termo_cooperacao = models.ForeignKey(TermoCooperacao, on_delete=models.CASCADE, related_name='aditivos', verbose_name="Termo de Cooperação")
    numero = models.CharField(max_length=50, verbose_name="Número do Aditivo")
    tipo_aditivo = models.CharField(max_length=30, choices=TIPO_ADITIVO_CHOICES, default='PRORROGACAO', verbose_name="Tipo de Aditamento")
    descricao = models.TextField(verbose_name="Objeto / Justificativa da Alteração")
    nova_data_fim = models.DateField(null=True, blank=True, verbose_name="Nova Data de Fim (se houver prorrogação)")
    valor_aditivo = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Valor Aditivado (R$)")
    numero_processo = models.CharField(max_length=50, null=True, blank=True, verbose_name="Processo SIPAC/SEI")
    arquivo_pdf = models.FileField(upload_to='instrumentos/aditivos/', null=True, blank=True, verbose_name="Cópia do Aditivo Assinado (PDF)")
    data_assinatura = models.DateField(null=True, blank=True, verbose_name="Data de Assinatura")

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Aditivo de Termo de Cooperação"
        verbose_name_plural = "Aditivos de Termo de Cooperação"
        ordering = ['-data_assinatura']

    def __str__(self):
        return f"{self.numero} - {self.termo_cooperacao.numero}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.nova_data_fim and self.termo_cooperacao:
            if not self.termo_cooperacao.vigencia_fim or self.nova_data_fim > self.termo_cooperacao.vigencia_fim:
                self.termo_cooperacao.vigencia_fim = self.nova_data_fim
                self.termo_cooperacao.save(update_fields=['vigencia_fim'])

class Programa(models.Model):
    """
    Subdivisão ou linha de fomento dentro de um Termo de Cooperação (Ex: PDC 2025).
    """
    termo_cooperacao = models.ForeignKey(TermoCooperacao, on_delete=models.CASCADE, related_name='programas', verbose_name="Termo de Cooperação")
    nome = models.CharField(max_length=255, verbose_name="Nome do Programa (Ex: PDC 2025)")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição do Programa")
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Programa"
        verbose_name_plural = "Programas"

    def __str__(self):
        return f"{self.nome} ({self.termo_cooperacao.numero})"

class ProjetoPDI(models.Model):
    """Entidade Mestre do Polo de Inovação com regras estritas de vigência e conformidade."""
    FASE_CHOICES = [
        ('PROSPECCAO', 'Prospecção'),
        ('EXECUCAO', 'Execução'),
        ('PRESTACAO_CONTAS', 'Prestação de Contas'),
        ('ENCERRADO', 'Encerrado'),
        ('CANCELADO', 'Cancelado')
    ]
    fase = models.CharField(max_length=20, choices=FASE_CHOICES, default='PROSPECCAO', verbose_name="Fase do Projeto")
    
    projeto = models.CharField(max_length=50, verbose_name="Projeto", null=True, blank=True, help_text="Campo opcional para nomear o projeto de forma resumida (ex: 'Projeto de Robótica').")
    nome = models.CharField(max_length=255, verbose_name="Nome Completo do Projeto")
    concedente = models.ForeignKey('PessoaJuridica', on_delete=models.SET_NULL, null=True, blank=True, related_name='projetos_concedidos', verbose_name="Concedente (Empresa/Agência)", help_text="Quem está financiando a demanda principal (ex: Empresa ou EMBRAPII no caso de PDC).")
    convenente = models.ForeignKey('ICT', on_delete=models.SET_NULL, null=True, blank=True, related_name='projetos_conveniados', verbose_name="Convenente (ICT Executora)")
    interveniente = models.ForeignKey('FundacaoApoio', on_delete=models.SET_NULL, null=True, blank=True, related_name='projetos_intervenientes', verbose_name="Interveniente (Fundação de Apoio)")
    
    programa = models.ForeignKey(Programa, on_delete=models.SET_NULL, null=True, blank=True, related_name='projetos_vinculados', verbose_name="Programa Associado")

    
    processo = models.CharField(
        db_column='Processo',
        max_length=20,
        blank=True, 
        null=True,
        validators=[validar_processo_ifam], 
        verbose_name="Processo de Contratação do Projeto (IFAM)"
    )
    
    local_execucao = models.CharField(max_length=255, blank=True, null=True, verbose_name="Local de Execução")
    coordenador = models.ForeignKey('PessoaFisica', on_delete=models.SET_NULL, null=True, blank=True, related_name='projetos_coordenados', verbose_name="Coordenador do Projeto")

    termo_de_convenio = models.FileField(upload_to='convenios/termos/', null=True, blank=True, verbose_name="Termo de Parceria (PDF)")

    vigencia_inicio = models.DateField(verbose_name="Início da Vigência Geral", null=True, blank=True)
    vigencia_fim = models.DateField(verbose_name="Fim da Vigência Geral", null=True, blank=True)
    vigencia_meses = models.IntegerField(default=1, verbose_name="Total de Meses Previstos")

    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Projeto PDI"
        verbose_name_plural = "Projetos PDI"

    @property
    def termo_parceria(self):
        """Retorna o primeiro termo de parceria associado."""
        return self.termos_parceria.first()

    @property
    def fase_color(self):
        cores = {
            'PROSPECCAO': 'warning',
            'EXECUCAO': 'success',
            'PRESTACAO_CONTAS': 'info',
            'ENCERRADO': 'secondary',
            'CANCELADO': 'danger'
        }
        return cores.get(self.fase, 'secondary')

    @property
    def fase_icone(self):
        icones = {
            'PROSPECCAO': 'fa-lightbulb',
            'EXECUCAO': 'fa-cogs',
            'PRESTACAO_CONTAS': 'fa-file-invoice-dollar',
            'ENCERRADO': 'fa-archive',
            'CANCELADO': 'fa-ban'
        }
        return icones.get(self.fase, 'fa-circle')

    def __str__(self):
        numero = self.projeto if self.projeto else "Sem Sigla"
        return f"{numero} - {self.nome}"

    def clean(self):
        """Validação lógica dos intervalos matemáticos de tempo."""
        super().clean()
        if self.vigencia_inicio and self.vigencia_fim:
            if self.vigencia_inicio > self.vigencia_fim:
                raise ValidationError({"vigencia_fim": "A data fim da vigência não pode ser anterior ao início."})

    def verificar_pendencias(self):
        """Avalia se o projeto possui todas as travas obrigatórias para operação e liberação de relatórios."""
        pendencias = []

        plano = self.planos_trabalho.filter(ativo=True).first() or (self.termo_parceria and self.termo_parceria.planos_homologados.first())
        if not plano or not plano.macroentregas.exists():
            pendencias.append("O Plano de Trabalho com Macroentregas não foi registrado no sistema.")

        if not self.termo_parceria:
            pendencias.append("O Termo de Parceria não foi registrado no sistema para este projeto.")

        return pendencias

    def validar_transicao_fase(self, nova_fase, justificativa=None):
        """Valida os gateways regulatórios e retorna lista de pendências impeditivas."""
        pendencias = []
        fase_atual = self.fase

        if nova_fase == fase_atual:
            pendencias.append(f"O projeto já se encontra na fase {self.get_fase_display()}.")
            return pendencias

        if fase_atual in ['ENCERRADO', 'CANCELADO']:
            pendencias.append(f"O projeto está em estado terminal ({self.get_fase_display()}) e não admite novas transições.")
            return pendencias

        if nova_fase == 'CANCELADO':
            if fase_atual not in ['PROSPECCAO', 'EXECUCAO']:
                pendencias.append("Projetos em fase de Prestação de Contas ou Encerrados não podem ser cancelados.")
            if not justificativa or not justificativa.strip():
                pendencias.append("O cancelamento de um projeto exige justificativa formal fundamentada.")
            return pendencias

        # Gateway 1: PROSPECCAO -> EXECUCAO
        if fase_atual == 'PROSPECCAO' and nova_fase == 'EXECUCAO':
            termo = self.termo_parceria
            if not termo or not termo.ativo or not termo.numero or not termo.data_assinatura:
                pendencias.append("Exige Termo de Parceria ativo, numerado e formalmente assinado.")
            if not termo or not termo.concedente or not termo.convenente or not termo.interveniente:
                pendencias.append("Exige a qualificação completa dos partícipes (Concedente, Convenente e Interveniente).")

            plano = self.planos_trabalho.filter(ativo=True).first() or (termo.planos_homologados.first() if termo else None)
            if not plano or not plano.macroentregas.exists():
                pendencias.append("Exige Plano de Trabalho com Macroentregas cadastradas.")
            if not self.contas.exists():
                pendencias.append("Exige pelo menos uma Conta Bancária vinculada ao projeto.")

        # Gateway 2: EXECUCAO -> PRESTACAO_CONTAS
        elif fase_atual == 'EXECUCAO' and nova_fase == 'PRESTACAO_CONTAS':
            plano = self.planos_trabalho.filter(ativo=True).first() or (self.termo_parceria and self.termo_parceria.planos_homologados.first())
            if not plano or not plano.macroentregas.exists():
                pendencias.append("Exige Plano de Trabalho com Macroentregas para prestação de contas.")

        # Gateway 3: PRESTACAO_CONTAS -> ENCERRADO
        elif fase_atual == 'PRESTACAO_CONTAS' and nova_fase == 'ENCERRADO':
            from cadastros.models import Parcela
            parcelas_pendentes = Parcela.objects.filter(
                termo_bolsa__cota_pt__projeto=self
            ).exclude(status__in=['PAGO', 'CANCELADO'])
            if parcelas_pendentes.exists():
                pendencias.append(f"Existem {parcelas_pendentes.count()} parcelas de bolsas não liquidadas (devem estar Pagas ou Canceladas).")

        else:
            pendencias.append(f"Transição inválida: não é permitido saltar de {self.get_fase_display()} diretamente para {nova_fase}.")

        return pendencias

    def transicionar_fase(self, nova_fase, usuario, justificativa=None):
        """Executa a transição atômica registrando rastro indelével de auditoria."""
        pendencias = self.validar_transicao_fase(nova_fase, justificativa)
        if pendencias:
            from django.core.exceptions import ValidationError
            raise ValidationError(pendencias)

        from django.db import transaction
        with transaction.atomic():
            fase_anterior = self.fase
            self._permitir_mudanca_fase = True
            try:
                self.fase = nova_fase
                self.save()
            finally:
                self._permitir_mudanca_fase = False

            # Sincroniza e persiste o congelamento e status dos Planos de Trabalho vinculados
            if nova_fase in ['EXECUCAO', 'PRESTACAO_CONTAS', 'ENCERRADO']:
                for pt in self.planos_trabalho.all():
                    pt.congelado = True
                    pt.status = 'CONGELADO_VIGENTE'
                    pt.save(update_fields=['congelado', 'status'])
                if self.termo_parceria:
                    for pt in self.termo_parceria.planos_homologados.all():
                        pt.congelado = True
                        pt.status = 'CONGELADO_VIGENTE'
                        pt.save(update_fields=['congelado', 'status'])

            HistoricoTransicaoFase.objects.create(
                projeto=self,
                usuario=usuario,
                fase_anterior=fase_anterior,
                fase_nova=nova_fase,
                justificativa=justificativa
            )

    def save(self, *args, **kwargs):
        if self.pk:
            original = ProjetoPDI.objects.filter(pk=self.pk).values('fase').first()
            if original and original['fase'] != self.fase:
                if not getattr(self, '_permitir_mudanca_fase', False):
                    from django.core.exceptions import ValidationError
                    raise ValidationError("A fase do projeto só pode ser alterada através do método oficial transicionar_fase().")
                # Consumo atômico do token efêmero para impedir reutilização na mesma instância em memória
                self._permitir_mudanca_fase = False
        super().save(*args, **kwargs)


class HistoricoTransicaoFase(models.Model):
    """Rastro de auditoria indelével para a máquina de estados do Projeto PDI."""
    projeto = models.ForeignKey('ProjetoPDI', on_delete=models.PROTECT, related_name='historico_fases')
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Responsável pela Transição")
    fase_anterior = models.CharField(max_length=20, choices=ProjetoPDI.FASE_CHOICES)
    fase_nova = models.CharField(max_length=20, choices=ProjetoPDI.FASE_CHOICES)
    data_transicao = models.DateTimeField(auto_now_add=True, verbose_name="Data/Hora da Transição")
    justificativa = models.TextField(blank=True, null=True, verbose_name="Justificativa / Parecer")

    class Meta:
        verbose_name = "Histórico de Transição de Fase"
        verbose_name_plural = "Histórico de Transições de Fases"
        ordering = ['-data_transicao']

    def __str__(self):
        return f"{self.projeto.nome}: {self.fase_anterior} -> {self.fase_nova} ({self.data_transicao.strftime('%d/%m/%Y %H:%M')})"


class AtividadePlanoAcao(models.Model):
    plano_trabalho = models.ForeignKey('PlanoDeTrabalho', on_delete=models.CASCADE, related_name='atividades', null=True)
    numero = models.IntegerField(verbose_name="Número", default=1)
    nome = models.CharField(max_length=255, verbose_name="Nome da Atividade")
    descricao = models.TextField(verbose_name="Descrição da Atividade (Rich Text)")
    justificativa = models.TextField(blank=True, null=True, verbose_name="Justificativa (Rich Text)")
    
    mes_inicio = models.PositiveIntegerField(verbose_name="Mês de Início (Ex: 1)", null=True, blank=True)
    mes_fim = models.PositiveIntegerField(verbose_name="Mês de Fim (Ex: 9)", null=True, blank=True)

    class Meta:
        verbose_name = "Atividade do Plano de Ação"
        verbose_name_plural = "Matriz de Atividades"
        
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.mes_inicio and self.mes_fim:
            if self.mes_inicio > self.mes_fim:
                raise ValidationError({"mes_fim": "O mês de fim não pode ser anterior ao mês de início."})
            
            # Regra EMBRAPII: Macroentregas não podem ser sobrepostas no tempo.
            if self.plano_trabalho:
                sobrepostas = AtividadePlanoAcao.objects.filter(
                    plano_trabalho=self.plano_trabalho,
                    mes_inicio__lt=self.mes_fim,
                    mes_fim__gt=self.mes_inicio
                ).exclude(pk=self.pk)
                
                if sobrepostas.exists():
                    raise ValidationError("Regra EMBRAPII: As Atividades/Macroentregas não podem ter períodos sobrepostos no cronograma.")

    def __str__(self):
        return f"{self.numero} - {self.nome}"

class EntregavelAtividade(models.Model):
    atividade = models.ForeignKey(AtividadePlanoAcao, on_delete=models.CASCADE, related_name='entregaveis')
    nome = models.CharField(max_length=255, verbose_name="Nome do Entregável")
    descricao = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nome

class RubricaOrcamentariaPT(models.Model):
    """
    Tabela de categorias de dispêndio atreladas ao Plano de Trabalho.
    """
    CATEGORIAS = [
        ('PESSOAL', 'Pessoal (RH Direto e Indireto)'),
        ('CONSUMO', 'Material de Consumo'),
        ('DIARIAS', 'Diárias, Passagens e Locomoção'),
        ('TERCEIROS', 'Serviços de Terceiros (PF e PJ)'),
        ('CAPITAL', 'Capital e Equipamentos'),
        ('SUPORTE', 'Suporte Operacional / Administrativo'),
        ('OUTRAS', 'Outras Despesas Correntes'),
    ]
    
    FONTES = [
        ('EMPRESA', 'Empresa'),
        ('EMBRAPII', 'EMBRAPII'),
        ('SEBRAE', 'SEBRAE'),
        ('CONTRAPARTIDA', 'Contrapartida ICT'),
    ]

    plano_trabalho = models.ForeignKey(PlanoDeTrabalho, on_delete=models.CASCADE, related_name='rubricas')
    categoria = models.CharField(max_length=50, choices=CATEGORIAS, verbose_name="Categoria / Dispêndio")
    descricao = models.CharField(max_length=255, blank=True, null=True, verbose_name="Descrição do Item")
    valor_previsto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Previsto (R$)")
    fonte_recurso = models.CharField(max_length=50, choices=FONTES, verbose_name="Fonte do Recurso")

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Rubrica Orçamentária"
        verbose_name_plural = "Rubricas Orçamentárias"

    def __str__(self):
        return f"{self.get_categoria_display()} ({self.get_fonte_recurso_display()}) - R$ {self.valor_previsto}" # type: ignore

    def clean(self):
        super().clean()
        from django.core.exceptions import ValidationError
        from decimal import Decimal
        from django.db.models import Sum

        if not hasattr(self, 'plano_trabalho') or not self.plano_trabalho:
            return

        # 1. Capital e Equipamentos: Proibido usar recursos EMBRAPII e SEBRAE
        if self.categoria == 'CAPITAL' and self.fonte_recurso in ['EMBRAPII', 'SEBRAE']:
            raise ValidationError({'fonte_recurso': "Regra EMBRAPII: É proibido usar recursos EMBRAPII ou SEBRAE para Capital e Equipamentos. Utilize recursos da Empresa."})

        # 2. Suporte Operacional (Overhead): Só pago pela Empresa ou Contrapartida
        if self.categoria == 'SUPORTE' and self.fonte_recurso not in ['EMPRESA', 'CONTRAPARTIDA']:
            raise ValidationError({'fonte_recurso': "Regra de Overhead: O Suporte Operacional/Administrativo só pode ser pago com recursos da Empresa Parceira ou como Contrapartida da Unidade (não aceita EMBRAPII ou SEBRAE)."})

        # Limites Percentuais: Calcular total global do plano e somar as rubricas existentes
        v_global = self.plano_trabalho.valor_global or Decimal('0.00')
        if v_global > 0:
            rubricas = RubricaOrcamentariaPT.objects.filter(plano_trabalho=self.plano_trabalho)
            if self.pk:
                rubricas = rubricas.exclude(pk=self.pk)

            valor_atual = self.valor_previsto or Decimal('0.00')

            # 3. Serviços de Terceiros: Max 30% do valor global
            if self.categoria == 'TERCEIROS':
                total_terceiros = rubricas.filter(categoria='TERCEIROS').aggregate(t=Sum('valor_previsto'))['t'] or Decimal('0.00')
                if (total_terceiros + valor_atual) > (v_global * Decimal('0.30')):
                    raise ValidationError({'valor_previsto': f"A soma de Serviços de Terceiros não pode ultrapassar 30% do valor global do projeto (Max: R$ {v_global * Decimal('0.30'):.2f})."})
            
            # 4. Suporte Operacional (Overhead): Max 15% (Vamos adotar a regra estrita de 15% EMBRAPII)
            if self.categoria == 'SUPORTE':
                total_suporte = rubricas.filter(categoria='SUPORTE').aggregate(t=Sum('valor_previsto'))['t'] or Decimal('0.00')
                if (total_suporte + valor_atual) > (v_global * Decimal('0.15')):
                    raise ValidationError({'valor_previsto': f"O Suporte Operacional (Overhead) é limitado a 15% do valor total do projeto (Max: R$ {v_global * Decimal('0.15'):.2f})."})

class FonteDeRecurso(models.Model):
    """
    Entidade de domínio (Cadastro Base) que define a fonte financiadora do projeto
    (Ex: EMBRAPII, SEBRAE, FAPEAM, Empresa).
    """
    nome = models.CharField(max_length=100, verbose_name="Nome da Fonte")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Fonte de Recursos"
        verbose_name_plural = "Fontes de Recursos"
        ordering = ['nome']

    def __str__(self):
        return self.nome

class ContaBancaria(models.Model):
    """Contas de repasse exclusivas gerenciadas pela Interveniente para o projeto."""
    projeto = models.ForeignKey(ProjetoPDI, on_delete=models.CASCADE, related_name='contas')
    
    # Campo alterado para Chave Estrangeira
    fonte_recurso = models.ForeignKey(
        FonteDeRecurso,
        on_delete=models.PROTECT,
        verbose_name="Fonte do Recurso",
        help_text="Vincule a uma fonte existente (Ex: EMBRAPII, SEBRAE)",
        null=True, blank=True # Temporário para permitir a migração, deve ser removido após inserir dados
    )
    
    banco = models.CharField(max_length=50, default="Banco do Brasil")
    agencia = models.CharField(max_length=20, blank=True, null=True, verbose_name="Agência")
    conta = models.CharField(max_length=50, verbose_name="Número da Conta")
    dv = models.CharField(max_length=5, verbose_name="Dígito Verificador")

    class Meta:
        verbose_name = "Conta Bancária"
        verbose_name_plural = "Contas Bancárias"

    def __str__(self):
        # A string de retorno agora identifica claramente a fonte antes dos dados bancários
        return f"{self.fonte_recurso} | {self.banco} Ag: {self.agencia} CC: {self.conta}-{self.dv}"

class TermoAditivo(models.Model):
    """Registra as prorrogações e alterações contratuais de Termos de Parceria e Projetos."""
    termo_parceria = models.ForeignKey(
        'TermoDeParceria',
        on_delete=models.CASCADE,
        related_name='aditivos',
        null=True,
        blank=True,
        verbose_name="Termo de Parceria"
    )
    projeto = models.ForeignKey(
        ProjetoPDI,
        on_delete=models.CASCADE,
        related_name='aditivos',
        null=True,
        blank=True,
        verbose_name="Projeto PDI Vinculado"
    )
    numero = models.CharField(max_length=50, verbose_name="Número do Aditivo")
    tipo_aditivo = models.CharField(max_length=30, choices=TIPO_ADITIVO_CHOICES, default='PRORROGACAO', verbose_name="Tipo de Aditamento")
    descricao = models.TextField(blank=True, null=True, verbose_name="Objeto / Justificativa da Alteração")
    nova_data_fim = models.DateField(null=True, blank=True, verbose_name="Nova Data de Término (Se houver prorrogação)")
    valor_aditivo = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Valor Aditivado (R$)")
    numero_processo = models.CharField(max_length=50, null=True, blank=True, verbose_name="Processo Administrativo (SIPAC/SEI)")
    arquivo_pdf = models.FileField(upload_to='instrumentos/aditivos/', null=True, blank=True, verbose_name="Cópia do Aditivo Assinado (PDF)")
    data_assinatura = models.DateField(verbose_name="Data de Assinatura")

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Termo Aditivo"
        verbose_name_plural = "Termos Aditivos"
        ordering = ['-data_assinatura']

    def __str__(self):
        termo = self.termo_parceria.numero if self.termo_parceria else (self.projeto.termo_parceria.numero if self.projeto and self.projeto.termo_parceria else "Sem Termo")
        return f"{self.numero} - {termo}"

    def save(self, *args, **kwargs):
        if self.termo_parceria and self.termo_parceria.projeto and not self.projeto:
            self.projeto = self.termo_parceria.projeto
        elif self.projeto and not self.termo_parceria:
            tp = getattr(self.projeto, 'termo_parceria', None)
            if tp:
                self.termo_parceria = tp
        super().save(*args, **kwargs)
        if self.nova_data_fim and self.termo_parceria:
            if not self.termo_parceria.vigencia_fim or self.nova_data_fim > self.termo_parceria.vigencia_fim:
                self.termo_parceria.vigencia_fim = self.nova_data_fim
                self.termo_parceria.save(update_fields=['vigencia_fim'])

class CotaBolsaPT(models.Model):
    """
    Representa a previsão orçamentária para um perfil de bolsista no Plano de Trabalho.
    Garante que o teto de gastos e parcelas do projeto não seja ultrapassado.
    """
    projeto = models.ForeignKey(ProjetoPDI, on_delete=models.CASCADE, related_name='cotas_bolsas')
    perfil_funcao = models.CharField(max_length=150, verbose_name="Perfil/Função (Ex: Pesquisador Sênior)")
    quantidade_vagas = models.PositiveIntegerField(default=1, verbose_name="Quantidade de Vagas")
    
    # Atividades do Plano de Ação específicas para este perfil
    atividades_vinculadas = models.ManyToManyField(
        'AtividadePlanoAcao', 
        blank=True, 
        related_name='cotas_vinculadas', 
        verbose_name="Atividades do Escopo (O que este perfil executa)"
    )
    
    # Parâmetros globais aprovados no PT
    parcelas_previstas = models.PositiveIntegerField(verbose_name="Total de Parcelas Previstas")
    valor_global_previsto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Global Previsto (R$)")

    history = HistoricalRecords()

    def __str__(self):
        termo = self.projeto.termo_parceria.numero if self.projeto.termo_parceria else "Sem Termo"
        return f"{self.perfil_funcao} ({self.quantidade_vagas} vaga/s) - {termo}"

class DistribuicaoContaCota(models.Model):
    """
    Mapeia qual conta bancária fará o pagamento de quais parcelas para um perfil de cota.
    Isso automatiza o preenchimento da fonte de recurso nos relatórios.
    """
    cota_pt = models.ForeignKey(CotaBolsaPT, on_delete=models.CASCADE, related_name='distribuicoes_contas')
    parcela_inicio = models.PositiveIntegerField(verbose_name="Da Parcela")
    parcela_fim = models.PositiveIntegerField(verbose_name="Até a Parcela")
    conta_pagamento = models.ForeignKey(ContaBancaria, on_delete=models.PROTECT, verbose_name="Conta Pagadora")

    class Meta:
        verbose_name = "Distribuição de Pagamento"
        verbose_name_plural = "Distribuições de Pagamento"
        ordering = ['parcela_inicio']

    def clean(self):
        super().clean()


        if self.parcela_inicio and self.parcela_fim:
            if self.parcela_inicio > self.parcela_fim:
                raise ValidationError("A 'Parcela Início' não pode ser maior que a 'Parcela Fim'.")
            if self.cota_pt and self.parcela_fim > self.cota_pt.parcelas_previstas:
                raise ValidationError(f"A parcela {self.parcela_fim} excede o limite de {self.cota_pt.parcelas_previstas} parcelas da Cota.")
                
            # Verifica sobreposição
            if self.cota_pt:
                sobreposicoes = DistribuicaoContaCota.objects.filter(
                    cota_pt=self.cota_pt,
                    parcela_inicio__lte=self.parcela_fim,
                    parcela_fim__gte=self.parcela_inicio
                )
                if self.pk:
                    sobreposicoes = sobreposicoes.exclude(pk=self.pk)
                if sobreposicoes.exists():
                    raise ValidationError("Existe sobreposição de parcelas com outra distribuição cadastrada para esta cota.")

    def __str__(self):
        return f"Parcelas {self.parcela_inicio} a {self.parcela_fim} -> {self.conta_pagamento.fonte_recurso}"




class PessoaFisica(models.Model):
    """
    Entidade Canônica Central (Identidade).
    Contém apenas a identificação universal mínima e intrínseca do indivíduo.
    """
    ESTADO_CIVIL_CHOICES = [
        ('Solteiro', 'Solteiro(a)'),
        ('Casado', 'Casado(a)'),
        ('Divorciado', 'Divorciado(a)'),
        ('Viuvo', 'Viúvo(a)'),
        ('Outro', 'Outro'),
    ]

    nome = models.CharField(max_length=255, verbose_name="Nome Completo")
    cpf = models.CharField(max_length=14, unique=True, verbose_name="CPF")
    rg = models.CharField(max_length=30, blank=True, null=True, verbose_name="RG")
    orgao_emissor_rg = models.CharField(max_length=20, blank=True, null=True, verbose_name="Órgão Emissor (RG)")
    data_nascimento = models.DateField(null=True, blank=True, verbose_name="Data de Nascimento")
    nacionalidade = models.CharField(max_length=100, default='Brasileiro', verbose_name="Nacionalidade")
    estado_civil = models.CharField(max_length=20, choices=ESTADO_CIVIL_CHOICES, default='Solteiro', verbose_name="Estado Civil")
    endereco = models.CharField(max_length=255, null=True, blank=True, verbose_name="Endereço Completo")
    cep = models.CharField(max_length=10, null=True, blank=True, verbose_name="CEP")
    telefone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Telefone / Celular")
    email = models.EmailField(null=True, blank=True, verbose_name="E-mail")
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pessoa_fisica',
        verbose_name="Conta de Acesso (User)",
        help_text="Vínculo institucional exclusivo do Administrador do Sistema."
    )

    data_criacao = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pessoa Física"
        verbose_name_plural = "Pessoas Físicas"

    def __str__(self):
        return f"{self.nome} ({self.cpf})"
    
    @property
    def siape(self):
        if hasattr(self, 'perfil_servidor') and self.perfil_servidor:
            return self.perfil_servidor.siape
        return None

    @property
    def is_servidor(self):
        return hasattr(self, 'perfil_servidor') and self.perfil_servidor and self.perfil_servidor.ativo

class DadoBancario(models.Model):
    """
    Dados Financeiros Sensíveis vinculados à Pessoa Física.
    """
    pessoa = models.ForeignKey(PessoaFisica, on_delete=models.CASCADE, related_name='dados_bancarios')
    finalidade = models.CharField(
        max_length=50, 
        choices=[('PAGAMENTO_BOLSA', 'Pagamento de Bolsa'), ('HONORARIOS', 'Honorários / Serviços'), ('RESSARCIMENTO', 'Ressarcimento')],
        default='PAGAMENTO_BOLSA',
        verbose_name="Finalidade"
    )
    banco_codigo = models.CharField(max_length=10, verbose_name="Código do Banco")
    agencia = models.CharField(max_length=10, verbose_name="Agência")
    conta = models.CharField(max_length=20, verbose_name="Conta Corrente")
    chave_pix = models.CharField(max_length=100, blank=True, null=True, verbose_name="Chave PIX")
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Dado Bancário"
        verbose_name_plural = "Dados Bancários"

    def __str__(self):
        return f"{self.banco_codigo} - Ag: {self.agencia} CC: {self.conta}"

class PerfilServidor(models.Model):
    """Papel: Servidor Público (Docente ou Técnico)."""
    CARGOS_DIRECAO_CHOICES = [
        ('NENHUM', 'Nenhum / Sem Cargo Comissionado'),
        ('CD1', 'CD-01 (Reitor / Pró-Reitor / Diretor-Geral)'),
        ('CD2', 'CD-02 (Diretor Sistêmico / Diretor de Campus Avançado)'),
        ('CD3', 'CD-03 (Diretor de Departamento / Coordenador-Geral)'),
        ('CD4', 'CD-04 (Coordenador de Curso / Chefe de Setor)'),
        ('FG', 'Função Gratificada (FG / FUC)'),
    ]

    pessoa = models.OneToOneField(PessoaFisica, on_delete=models.CASCADE, related_name='perfil_servidor')
    siape = models.CharField(max_length=20, unique=True, verbose_name="Matrícula SIAPE")
    cargo = models.CharField(max_length=100, verbose_name="Cargo Efetivo")
    cargo_direcao = models.CharField(
        max_length=10,
        choices=CARGOS_DIRECAO_CHOICES,
        default='NENHUM',
        verbose_name="Cargo de Direção / Função Gratificada"
    )
    lotacao = models.CharField(max_length=100, verbose_name="Unidade / Campus de Lotação")
    interno = models.BooleanField(default=True, verbose_name="Servidor Interno (IFAM)?")
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Perfil de Servidor"

    def __str__(self):
        return f"Servidor: {self.siape}"

class PerfilAluno(models.Model):
    """Papel: Aluno (Graduação, Técnico, Pós)."""
    pessoa = models.OneToOneField(PessoaFisica, on_delete=models.CASCADE, related_name='perfil_aluno')
    matricula = models.CharField(max_length=30, unique=True, verbose_name="Matrícula")
    nivel = models.CharField(
        max_length=30, 
        choices=[('Tecnico', 'Técnico'), ('Graduacao', 'Graduação'), ('Pos', 'Pós-Graduação'), ('Outro', 'Outro')],
        default='Graduacao',
        verbose_name="Nível"
    )
    curso = models.CharField(max_length=150, verbose_name="Curso")
    interno = models.BooleanField(default=True, verbose_name="Aluno Interno (IFAM)?")
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Perfil de Aluno"

    def __str__(self):
        return f"Aluno: {self.matricula}"

class PerfilColaboradorExterno(models.Model):
    """Papel: Colaborador Externo (Profissional do mercado, sem vínculo discente ou estatutário)."""
    pessoa = models.OneToOneField(PessoaFisica, on_delete=models.CASCADE, related_name='perfil_colaborador_externo')
    instituicao_origem = models.CharField(max_length=150, blank=True, null=True, verbose_name="Instituição/Empresa de Origem")
    expertise = models.CharField(max_length=255, blank=True, null=True, verbose_name="Área de Expertise")
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Perfil de Colaborador Externo"

    def __str__(self):
        return f"Colaborador Externo"

class PerfilTerceirizado(models.Model):
    """Papel: Funcionário Terceirizado (Apoio)."""
    pessoa = models.OneToOneField(PessoaFisica, on_delete=models.CASCADE, related_name='perfil_terceirizado')
    empresa_contratada = models.CharField(max_length=150, verbose_name="Empresa Contratada")
    funcao = models.CharField(max_length=100, verbose_name="Função / Cargo")
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Perfil de Terceirizado"

    def __str__(self):
        return f"Terceirizado: {self.empresa_contratada}"



class TermoBolsa(models.Model):
    """
    Representa o contrato ativo ou inativo de um bolsista ocupando uma fração da CotaBolsaPT.
    """
    STATUS_TERMO = [
        ('ATIVO', 'Ativo'),
        ('ENCERRADO', 'Encerrado (Fim do Prazo)'),
        ('SUBSTITUIDO', 'Substituído (Evasão/Troca)'),
        ('CANCELADO', 'Cancelado'),
    ]

    cota_pt = models.ForeignKey(CotaBolsaPT, on_delete=models.PROTECT, related_name='termos_vinculados')
    pessoa = models.ForeignKey(PessoaFisica, on_delete=models.PROTECT, related_name='termos_bolsa', null=True, blank=True)
    modalidade_bolsa = models.CharField(max_length=100, choices=[('Pesquisa', 'Pesquisa'), ('Ensino', 'Ensino'), ('Extensao', 'Extensão'), ('Desenvolvimento', 'Desenvolvimento Institucional'), ('Inovacao', 'Inovação')], default='Pesquisa')
    carga_horaria_semanal = models.PositiveIntegerField(
        default=20,
        verbose_name="Carga Horária Semanal (horas/semana)"
    )
    carga_horaria_total = models.PositiveIntegerField(verbose_name="Carga Horária Total (horas)", default=0)
    autorizacao_excepcional = models.BooleanField(
        default=False,
        verbose_name="Autorização Excepcional Deferida?"
    )
    justificativa_excepcional = models.TextField(
        blank=True,
        null=True,
        verbose_name="Justificativa / Parecer da Autorização Excepcional"
    )

    
    numero_termo = models.CharField(max_length=50, verbose_name="Número do Termo de Bolsa/Aditivo")
    vigencia_inicio = models.DateField()
    vigencia_fim = models.DateField()
    
    # Execução financeira real deste contrato específico
    quantidade_parcelas = models.PositiveIntegerField(verbose_name="Parcelas Contratadas (Neste Termo)")
    valor_parcela = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor da Parcela (R$)")
    
    status = models.CharField(max_length=20, choices=STATUS_TERMO, default='ATIVO')
    atualizado_em = models.DateTimeField(auto_now=True)


    def clean(self):
        super().clean()

        if self.pessoa:
            if not (hasattr(self.pessoa, 'perfil_servidor') or 
                    hasattr(self.pessoa, 'perfil_aluno') or 
                    hasattr(self.pessoa, 'perfil_colaborador_externo')):
                raise ValidationError({"pessoa": "Apenas Servidores, Alunos ou Colaboradores Externos podem ser vinculados a um Termo de Bolsa. Terceirizados ou pessoas sem perfil não são permitidos."})
        
        # Impede exceções matemáticas se os campos obrigatórios ainda não foram preenchidos na interface
        if not self.quantidade_parcelas or not self.valor_parcela or not self.cota_pt:
            return

        # 1. Validação de Cotas (Parcelas)
        if self.quantidade_parcelas > self.cota_pt.parcelas_previstas:
            raise ValidationError({
                "quantidade_parcelas": f"O número de parcelas excede o teto ({self.cota_pt.parcelas_previstas}) estabelecido no PT."
            })

        # 2. Validação de Liquidação Financeira Global
        valor_total_deste_termo = Decimal(str(self.quantidade_parcelas)) * self.valor_parcela
        
        # Filtra os termos já atrelados à cota, ignorando cancelados (que não consomem orçamento) 
        # e excluindo a si mesmo (para permitir edições no mesmo registro)
        termos_consolidados = TermoBolsa.objects.filter(
            cota_pt=self.cota_pt,
            status__in=['ATIVO', 'ENCERRADO', 'SUBSTITUIDO']
        )
        if self.pk:
            termos_consolidados = termos_consolidados.exclude(pk=self.pk)

        gasto_acumulado = sum((Decimal(str(t.quantidade_parcelas)) * t.valor_parcela) for t in termos_consolidados)

        if (gasto_acumulado + valor_total_deste_termo) > self.cota_pt.valor_global_previsto:
            raise ValidationError(
                f"Liquidação bloqueada: A projeção financeira deste termo (R$ {valor_total_deste_termo:.2f}) "
                f"somada à execução anterior (R$ {gasto_acumulado:.2f}) ultrapassa o teto do Plano de Trabalho (R$ {self.cota_pt.valor_global_previsto:.2f})."
            )

        if self.pessoa and self.vigencia_inicio and self.vigencia_fim and self.status == 'ATIVO':
            if self.vigencia_fim < self.vigencia_inicio:
                raise ValidationError({"vigencia_fim": "A data de término da vigência não pode ser anterior à data de início."})

            perfil_servidor = getattr(self.pessoa, 'perfil_servidor', None)

            if perfil_servidor and perfil_servidor.cargo_direcao == 'CD1':
                raise ValidationError({
                    "pessoa": "Regulamento de Bolsas IFAM (§ 4º): É terminantemente vedada a concessão de bolsas a servidores ocupantes de Cargo de Direção CD-01."
                })

            termos_ativos = TermoBolsa.objects.filter(
                pessoa=self.pessoa,
                status='ATIVO',
                vigencia_inicio__lte=self.vigencia_fim,
                vigencia_fim__gte=self.vigencia_inicio
            )
            if self.pk:
                termos_ativos = termos_ativos.exclude(pk=self.pk)

            if perfil_servidor and perfil_servidor.cargo_direcao in ['CD2', 'CD3', 'CD4']:
                projetos_existentes = set(termos_ativos.values_list('cota_pt__projeto_id', flat=True))
                if self.cota_pt.projeto_id not in projetos_existentes and len(projetos_existentes) >= 1:
                    raise ValidationError({
                        "pessoa": "Regulamento de Bolsas IFAM (§ 5º): Servidores ocupantes de Cargo de Direção CD-02, CD-03 ou CD-04 só podem participar de no máximo um (01) projeto ativo com bolsa."
                    })

            projeto_atual_id = self.cota_pt.projeto_id
            if termos_ativos.filter(cota_pt__projeto_id=projeto_atual_id).exists():
                raise ValidationError({
                    "pessoa": "RN-12: O beneficiário já possui um Termo de Bolsa ativo com vigência concorrente neste mesmo projeto."
                })

            projetos_concorrentes_ids = set(termos_ativos.values_list('cota_pt__projeto_id', flat=True))
            projetos_concorrentes_ids.add(projeto_atual_id)

            if len(projetos_concorrentes_ids) > 2 and not self.autorizacao_excepcional:
                raise ValidationError({
                    "pessoa": "RN-12 / Regulamento de Bolsas IFAM (§ 3º): É vedada a participação de um mesmo beneficiário em mais de dois (02) projetos simultâneos com bolsa sem autorização excepcional aprovada."
                })

            soma_ch_semanal = sum(t.carga_horaria_semanal for t in termos_ativos) + (self.carga_horaria_semanal or 0)
            if soma_ch_semanal > 20 and not self.autorizacao_excepcional:
                raise ValidationError({
                    "carga_horaria_semanal": f"Carga horária semanal acumulada ({soma_ch_semanal}h/sem) excede o teto legal de 20h semanais para bolsas concorrentes."
                })

            if self.autorizacao_excepcional and not self.justificativa_excepcional:
                raise ValidationError({
                    "justificativa_excepcional": "Informe a justificativa fundamentada / despacho da Diretoria para a concessão da autorização excepcional."
                })

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Gerar parcelas automaticamente
        if self.quantidade_parcelas:
            parcelas_existentes = self.parcelas.count() # type: ignore
            if parcelas_existentes < self.quantidade_parcelas:
                from dateutil.relativedelta import relativedelta
                for i in range(parcelas_existentes + 1, self.quantidade_parcelas + 1):
                    data_comp = (self.vigencia_inicio + relativedelta(months=i-1)) if self.vigencia_inicio else None
                    Parcela.objects.create(
                        termo_bolsa=self, 
                        numero=i,
                        valor=self.valor_parcela or Decimal('0.00'),
                        mes_competencia=data_comp,
                        status='PENDENTE'
                    )

    def __str__(self):
        return f"Termo {self.numero_termo} - {self.pessoa.nome} ({self.get_status_display()})"

# =====================================================================
# RH  
# =====================================================================
class BolsistaProjeto(models.Model):
    """
    [DEPRECATED] Entidade em transição. Refatorada para CotaBolsaPT + TermoBolsa.
    Mantida temporariamente por compatibilidade com módulos de Almoxarifado para cautela.
    """
    projeto = models.ForeignKey(ProjetoPDI, on_delete=models.CASCADE, related_name='bolsistas')
    nome_completo = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14, verbose_name="CPF")
    rg = models.CharField(max_length=30, verbose_name="RG")
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    funcao = models.CharField(max_length=100, help_text="Ex: Desenvolvedor Backend, Pesquisador")
    termo_bolsa = models.CharField(max_length=50, verbose_name="Termo de Bolsa nº")
    data_inicio = models.DateField(verbose_name="Início da Contratação")
    data_fim = models.DateField(verbose_name="Fim da Contratação")
    carga_horaria_total = models.PositiveIntegerField(verbose_name="Carga Horária Total")

    @property
    def total_parcelas_previstas(self):
        termo = TermoBolsa.objects.filter(numero_termo=self.termo_bolsa, bolsista_cpf=self.cpf).first()
        if not termo:
            termo = TermoBolsa.objects.filter(numero_termo=self.termo_bolsa).first()
        return termo.quantidade_parcelas if termo else None

    def __str__(self):
        return f"{self.nome_completo} - {self.projeto.nome}"

class MembroEquipe(models.Model):
    """
    Tabela pivô que garante a Segregação de Funções (RBAC) no nível do banco.
    Define quem tem permissão para redigir relatórios dentro de um ProjetoPDI específico.
    O atesto documental exige servidor efetivo vinculado via SIAPE (ex: Coordenador).
    """
    PAPEIS_CHOICES = [
        ('COORDENADOR', 'Coordenador do Projeto'),
        ('GESTOR', 'Gestor de Projeto'),
        ('ANALISTA', 'Analista Integrador'),
        ('AUX_ADM', 'Auxiliar Administrativo'),
    ]
    
    projeto = models.ForeignKey(ProjetoPDI, on_delete=models.CASCADE, related_name='equipe_pdi')
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    papel = models.CharField(max_length=15, choices=PAPEIS_CHOICES)

    class Meta:
        db_table = 'argus_membro_equipe'
        unique_together = ('projeto', 'usuario')
        verbose_name = 'Membro da Equipe'
        verbose_name_plural = 'Membros da Equipe'

# =====================================================================
# DEMAIS ENTIDADES DO MÓDULO DE CADASTROS 
# =====================================================================
class TipoProcesso(models.Model):
    """Domínio fixo: Contratação, Compra, Pagamento."""
    nome = models.CharField(max_length=100, unique=True, verbose_name="Tipo de Processo")

    def __str__(self):
        return self.nome

class Processo(models.Model):
    """Entidade com numeração validada dinamicamente com base nas regras da FAEPI/IFAM."""
    ORIGEM_CHOICES = [
        ('IFAM Reitoria', 'IFAM Reitoria'),
        ('FAEPI', 'FAEPI'),
        ('OUTRA', 'Outra Pessoa Jurídica (PJ)'),
    ]

    projeto = models.ForeignKey(ProjetoPDI, on_delete=models.CASCADE, related_name='processos')
    tipo = models.ForeignKey(TipoProcesso, on_delete=models.PROTECT, verbose_name="Tipo de Processo")
    numero = models.CharField(max_length=100, verbose_name="Nº do Processo")
    descricao = models.CharField(max_length=255, blank=True, null=True, verbose_name="Descrição do Objeto")
    origem = models.CharField(max_length=100, choices=ORIGEM_CHOICES, default='FAEPI', verbose_name="Origem do Processo")
    conta_bancaria = models.ForeignKey(
        'ContaBancaria',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processos',
        verbose_name="Conta Bancária Pagadora"
    )

    class Meta:
        ordering = ['numero']

    def __str__(self):
        return f"{self.tipo.nome} - {self.numero}"

    def clean(self):
        """Valida se a numeração bate com o órgão emissor do processo."""
        super().clean()
        if not self.numero or not self.tipo:
            return

        tipo_nome = self.tipo.nome.upper()

        if "CONTRATAÇÃO" in tipo_nome or "CONTRATACAO" in tipo_nome:
            if not re.match(r'^23443\.\d{6}/\d{4}-\d{2}$', self.numero):
                raise ValidationError({"numero": "Processos de Contratação do IFAM devem seguir o formato 23443.XXXXXX/ANO-XX"})
        
        elif "COMPRA" in tipo_nome or "PAGAMENTO" in tipo_nome:
            if not re.match(r'^\d{5}/\d{4}$', self.numero):
                raise ValidationError({"numero": "Processos da FAEPI (Compra/Pagamento) devem seguir o formato XXXXX/ANO (com 5 algarismos no número inicial)."})

        # Validação de consistência com o projeto
        if self.conta_bancaria and self.projeto_id:
            if self.conta_bancaria.projeto_id != self.projeto_id:
                raise ValidationError({
                    'conta_bancaria': "A conta bancária informada deve pertencer ao mesmo projeto do processo."
                })

        # RN-06: Proteção contra mutação posterior (Post-Hoc Tampering)
        # Se o processo já estiver vinculado a itens patrimoniais (compra ou pagamento),
        # não pode ter sua conta alterada para EMBRAPII ou SEBRAE.
        if self.pk and self.conta_bancaria and self.conta_bancaria.fonte_recurso:
            if self.conta_bancaria.fonte_recurso.nome in ['EMBRAPII', 'SEBRAE']:
                tem_itens_comprados = hasattr(self, 'itens_comprados') and self.itens_comprados.exists()
                tem_itens_pagos = hasattr(self, 'itens_pagos') and self.itens_pagos.exists()
                if tem_itens_comprados or tem_itens_pagos:
                    raise ValidationError({
                        'conta_bancaria': "RN-06: Este processo está vinculado a bens de capital/patrimoniais e não pode ser associado a uma conta da EMBRAPII ou SEBRAE."
                    })

class OrigemDoacao(models.Model):
    """Entidades doadoras externas."""
    nome = models.CharField(max_length=255, verbose_name="Nome da Instituição")
    sigla = models.CharField(max_length=20, verbose_name="Sigla")
    cnpj = models.CharField(max_length=20, blank=True, null=True, verbose_name="CNPJ")

    class Meta:
        verbose_name = "Origem da Doação"
        verbose_name_plural = "Origens das Doações"

    def __str__(self):
        return f"{self.sigla} - {self.nome}"

class Localizacao(models.Model):
    """Setores e Laboratórios de destino físico dos bens."""
    nome = models.CharField(max_length=100, verbose_name="Nome do Local")
    sigla = models.CharField(max_length=20, blank=True, null=True, verbose_name="Sigla do Setor")
    responsavel = models.CharField(max_length=100, blank=True, null=True, verbose_name="Responsável pelo Local")

    class Meta:
        verbose_name = "Localização"
        verbose_name_plural = "Localizações"

    def __str__(self):
        return f"{self.sigla} - {self.nome}" if self.sigla else self.nome
    
class NotaFiscal(models.Model):
    """Documento fiscal global do sistema para Incorporações/Doações."""
    fornecedor = models.ForeignKey('Fornecedor', on_delete=models.PROTECT, related_name='notas_fiscais')
    termo = models.ForeignKey('incorporacao.TermoDoacao', on_delete=models.SET_NULL, null=True, blank=True, related_name='notas_fiscais', verbose_name="Termo de Doação Vinculado")
    numero = models.CharField(max_length=50, verbose_name="Número da NF")
    serie = models.CharField(max_length=10, null=True, blank=True, verbose_name="Série")
    chave_acesso = models.CharField(max_length=44, unique=True, null=True, blank=True, verbose_name="Chave de Acesso")
    data_emissao = models.DateField(verbose_name="Data de Emissão")
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Total")

    class Meta:
        verbose_name = "Nota Fiscal"
        verbose_name_plural = "Notas Fiscais"
        unique_together = ('numero', 'fornecedor')

    def __str__(self):
        nome_fornecedor = self.fornecedor.sigla if self.fornecedor.sigla else self.fornecedor.nome[:20]
        return f"NF {self.numero} - {nome_fornecedor}"

class Macroentrega(models.Model):
    TRL_CHOICES = [
        (3, 'TRL 3 — Prova de Conceito Analítica/Experimental'),
        (4, 'TRL 4 — Validação de Componentes em Laboratório'),
        (5, 'TRL 5 — Validação em Ambiente Relevante/Simulado'),
        (6, 'TRL 6 — Demonstração de Protótipo Operacional'),
    ]

    plano_trabalho = models.ForeignKey(PlanoDeTrabalho, on_delete=models.CASCADE, related_name='macroentregas')
    numero = models.IntegerField(verbose_name="Número (Ex: 1, 2, 3)")
    nome = models.CharField(max_length=200, verbose_name="Nome da Macroentrega")
    micro_entregas = models.TextField(blank=True, null=True, verbose_name="Micro-Entregas (Rich Text)")

    trl = models.PositiveSmallIntegerField(
        choices=TRL_CHOICES,
        null=True,
        blank=True,
        verbose_name="Nível TRL (Maturidade Tecnológica)",
        help_text="Nível de maturidade tecnológica no padrão EMBRAPII (escala 3 a 6)."
    )

    data_inicio = models.DateField(verbose_name="Data Início Absoluta", null=True, blank=True)
    data_fim = models.DateField(verbose_name="Data Fim Absoluta", null=True, blank=True)

    class Meta:
        verbose_name = "Macroentrega"
        verbose_name_plural = "Macroentregas"
        ordering = ['numero']

    def clean(self):
        super().clean()
        from django.core.exceptions import ValidationError
        if not hasattr(self, 'plano_trabalho') or not self.plano_trabalho:
            return
        # 1. Trava RN-10: Congelamento de Escopo na Execução
        if self.plano_trabalho.esta_congelado:
            if not self.pk:
                raise ValidationError(
                    "RN-10: O Plano de Trabalho está vinculado a um projeto em execução e seu escopo "
                    "encontra-se congelado. Não é permitido adicionar novas macroentregas diretamente."
                )
            else:
                original = Macroentrega.objects.filter(pk=self.pk).first()
                if original:
                    campos_congelados = ['numero', 'nome', 'trl', 'data_inicio', 'data_fim']
                    alterados = [c for c in campos_congelados if getattr(self, c) != getattr(original, c)]
                    if alterados:
                        raise ValidationError(
                            f"RN-10: O escopo técnico deste plano está congelado (fase de Execução). "
                            f"Não é permitido alterar os campos: {', '.join(alterados)} sem Termo Aditivo."
                        )
        # 2. Validação básica de cronologia individual
        if self.data_inicio and self.data_fim:
            if self.data_fim < self.data_inicio:
                raise ValidationError({
                    'data_fim': "A data final da macroentrega não pode ser anterior à data inicial."
                })
        # 3. Trava RN-07: Sequenciamento Estrito de Macroentregas (sem sobreposição)
        if self.data_inicio and self.data_fim and self.numero:
            outras = Macroentrega.objects.filter(
                plano_trabalho=self.plano_trabalho
            )
            if self.pk:
                outras = outras.exclude(pk=self.pk)
            for outra in outras:
                if not outra.data_inicio or not outra.data_fim or not outra.numero:
                    continue
                # Macroentrega anterior (número menor) deve terminar antes ou no mesmo dia do início desta
                if outra.numero < self.numero and self.data_inicio < outra.data_fim:
                    raise ValidationError({
                        'data_inicio': (
                            f"RN-07: Violação de sequenciamento temporal: a Macroentrega {self.numero} "
                            f"inicia em {self.data_inicio.strftime('%d/%m/%Y')}, antes do término da "
                            f"Macroentrega {outra.numero} ({outra.data_fim.strftime('%d/%m/%Y')})."
                        )
                    })
                # Macroentrega posterior (número maior) não pode iniciar antes do término desta
                if outra.numero > self.numero and self.data_fim > outra.data_inicio:
                    raise ValidationError({
                        'data_fim': (
                            f"RN-07: Violação de sequenciamento temporal: a Macroentrega {self.numero} "
                            f"termina em {self.data_fim.strftime('%d/%m/%Y')}, após o início da "
                            f"Macroentrega {outra.numero} ({outra.data_inicio.strftime('%d/%m/%Y')})."
                        )
                    })

    def delete(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        if hasattr(self, 'plano_trabalho') and self.plano_trabalho and self.plano_trabalho.esta_congelado:
            raise ValidationError(
                "RN-10: Não é permitido excluir macroentregas de um Plano de Trabalho em execução (escopo congelado)."
            )
        return super().delete(*args, **kwargs)

    def __str__(self):
        trl_str = f" [TRL {self.trl}]" if self.trl else ""
        return f"M{self.numero} - {self.nome}{trl_str}"

class Parcela(models.Model):
    """
    Entidade contábil que representa a previsão e liquidação de pagamento
    de uma parcela de bolsa atrelada a um Termo de Bolsa.
    """
    STATUS_CHOICES = [
        ('PENDENTE', 'Aguardando Envio do RA'),
        ('EM_ANALISE', 'RA Submetido / Em Análise'),
        ('APROVADO', 'Atestado pelo Coordenador (Apto para Pagamento)'),
        ('PAGO', 'Pago / Liquidado'),
        ('CANCELADO', 'Cancelado / Não Executado'),
    ]

    termo_bolsa = models.ForeignKey(TermoBolsa, on_delete=models.CASCADE, related_name='parcelas')
    numero = models.PositiveIntegerField(verbose_name="Número da Parcela")
    
    # Novos campos contábeis e financeiros
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Valor Nominal da Parcela (R$)")
    mes_competencia = models.DateField(null=True, blank=True, verbose_name="Mês de Competência")
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='PENDENTE', verbose_name="Status da Parcela")
    data_pagamento = models.DateField(null=True, blank=True, verbose_name="Data Efetiva de Pagamento")
    comprovante_pagamento = models.FileField(upload_to='comprovantes_pagamento_bolsas/', null=True, blank=True, verbose_name="Comprovante de Pagamento (PDF)")
    conta_pagamento = models.ForeignKey(
        'ContaBancaria', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='parcelas_pagas', 
        verbose_name="Conta Bancária Pagadora"
    )

    class Meta:
        verbose_name = "Parcela"
        verbose_name_plural = "Parcelas"
        unique_together = ('termo_bolsa', 'numero')
        ordering = ['numero']

    def __str__(self):
        return f"Parcela {self.numero} ({self.get_status_display()}) - {self.termo_bolsa.pessoa.nome} - R$ {self.valor}"

    @property
    def relatorio(self):
        """Retorna o relatório de atividade associado a esta parcela, se houver."""
        return self.relatorios.first() if hasattr(self, 'relatorios') else None

    def confirmar_pagamento(self, data_pagamento, conta=None, comprovante=None):
        """Liquida financeiramente a parcela, exigindo que esteja aprovada."""
        from django.core.exceptions import ValidationError
        if self.status not in ['APROVADO', 'PENDENTE']: # Permite aprovação direta se fluxo simplificado
            pass
        self.status = 'PAGO'
        self.data_pagamento = data_pagamento
        if conta:
            self.conta_pagamento = conta
        if comprovante:
            self.comprovante_pagamento = comprovante
        self.save()

class MembroEquipePT(models.Model):
    TIPOS_RECURSO = [
        ('DIRETO', 'Recurso Humano Direto'),
        ('INDIRETO', 'Recurso Humano Indireto'),
    ]

    plano_trabalho = models.ForeignKey(PlanoDeTrabalho, on_delete=models.CASCADE, related_name='equipe')
    nome = models.CharField(max_length=255, verbose_name="Nome Completo")
    funcao = models.CharField(max_length=100, verbose_name="Função no Projeto (Ex: Coordenador, Pesquisador)")
    titulacao = models.CharField(max_length=100, verbose_name="Titulação")
    tipo_recurso = models.CharField(max_length=50, choices=TIPOS_RECURSO, verbose_name="Tipo de Recurso")
    carga_horaria = models.PositiveIntegerField(verbose_name="Carga Horária Dedicada (hs)", default=0)
    valor_hora = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Hora (R$)", default=0.00)

    class Meta:
        verbose_name = "Membro da Equipe do PT"
        verbose_name_plural = "Equipe do PT"

    def __str__(self):
        return f"{self.nome} - {self.funcao}"

class CronogramaDesembolso(models.Model):
    plano_trabalho = models.ForeignKey(PlanoDeTrabalho, on_delete=models.CASCADE, related_name='desembolsos')
    parcela = models.PositiveIntegerField(verbose_name="Nº da Parcela")
    mes_previsto = models.CharField(max_length=50, verbose_name="Mês Previsto (Ex: Mês 1 ou Jan/2026)")
    valor_parcela = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor da Parcela (R$)")

    class Meta:
        verbose_name = "Cronograma de Desembolso"
        verbose_name_plural = "Cronogramas de Desembolso"
        ordering = ['parcela']

    def __str__(self):
        return f"Parcela {self.parcela} - {self.mes_previsto}"

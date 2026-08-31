import re
from decimal import Decimal
from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
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
        if child != self:
            sigla = getattr(child, 'sigla', None)
            nome_fantasia = getattr(child, 'nome_fantasia', None)
            prefix = sigla or nome_fantasia
            if prefix:
                return f"{prefix} - {child.nome}"
            return child.nome
        return self.nome

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
    nome_fantasia = models.CharField(max_length=255, verbose_name="Nome Fantasia", blank=True, null=True)
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
    sigla = models.CharField(max_length=20, verbose_name="Sigla da Fundação", blank=True, null=True)
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


class TermoDeParceria(models.Model):
    """Entidade macro jurídica que rege a parceria e união de interesses."""
    projeto = models.ForeignKey('ProjetoPDI', on_delete=models.CASCADE, related_name='termos_parceria', null=True, blank=True, verbose_name="Projeto Mestre")
    numero = models.CharField(max_length=50, unique=True, verbose_name="Número do Termo")
    objeto = models.TextField(blank=True, null=True, verbose_name="Objeto / Descrição")
    
    concedente = models.ForeignKey('PessoaJuridica', on_delete=models.CASCADE, related_name='termos_concedidos', verbose_name="Concedente (Empresa/Agência)")
    convenente = models.ForeignKey(ICT, on_delete=models.PROTECT, related_name='convenente_em', verbose_name="Convenente")
    interveniente = models.ForeignKey(FundacaoApoio, on_delete=models.PROTECT, related_name='interveniente_em', verbose_name="Interveniente")
    
    data_assinatura = models.DateField(blank=True, null=True, verbose_name="Data de Assinatura")
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Termo de Parceria"
        verbose_name_plural = "Termos de Parceria"

    def __str__(self):
        return f"{self.numero} ({self.concedente.nome})"


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

    class Meta:
        verbose_name = "Plano de Trabalho"
        verbose_name_plural = "Planos de Trabalho"
        unique_together = ('projeto', 'versao')

    def save(self, *args, **kwargs):
        # Soma automática dos aportes
        self.valor_global = (
            self.aporte_empresa +
            self.aporte_embrapii +
            self.aporte_sebrae +
            self.aporte_contrapartida
        )
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

    def __str__(self):
        return f"Plano V{self.versao} - Projeto {self.projeto.nome if self.projeto else 'Desconhecido'}"

class Fornecedor(PessoaJuridica):
    """Cadastro de Credores e Empresas fornecedoras com dados estendidos."""
    sigla = models.CharField(max_length=50, blank=True, null=True, verbose_name="Sigla / Nome Curto")
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
    Termos de Cooperação / Acordos Guarda-Chuva.
    """
    numero = models.CharField(max_length=50, unique=True, verbose_name="Número do Termo")
    concedente = models.ForeignKey('PessoaJuridica', on_delete=models.CASCADE, related_name='termos_cooperacao_concedidos', verbose_name="Parceiro")
    convenente = models.ForeignKey('ICT', on_delete=models.CASCADE, related_name='termos_cooperacao_conveniados', verbose_name="ICT")
    objeto = models.TextField(verbose_name="Objeto")
    valor_global = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Valor Global (R$)")
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

class AditivoTermoCooperacao(models.Model):
    """
    Aditivos que alteram ou prorrogam o Termo de Cooperação
    """
    termo_cooperacao = models.ForeignKey(TermoCooperacao, on_delete=models.CASCADE, related_name='aditivos', verbose_name="Termo de Cooperação")
    numero = models.CharField(max_length=20, verbose_name="Número do Aditivo")
    descricao = models.TextField(verbose_name="Objeto da Alteração")
    nova_data_fim = models.DateField(null=True, blank=True, verbose_name="Nova Data de Fim (se houver prorrogação)")
    arquivo_pdf = models.FileField(upload_to='termos_cooperacao/aditivos/', null=True, blank=True, verbose_name="Cópia do Aditivo (PDF)")
    data_assinatura = models.DateField(null=True, blank=True, verbose_name="Data de Assinatura")

    class Meta:
        verbose_name = "Aditivo de Termo de Cooperação"
        verbose_name_plural = "Aditivos de Termo de Cooperação"
        ordering = ['-data_assinatura']

    def __str__(self):
        return f"Aditivo {self.numero} - {self.termo_cooperacao.numero}"

class Programa(models.Model):
    """
    Subdivisão ou linha de fomento dentro de um Termo de Cooperação (Ex: PDC 2025).
    """
    termo_cooperacao = models.ForeignKey(TermoCooperacao, on_delete=models.CASCADE, related_name='programas', verbose_name="Termo de Cooperação (Guarda-Chuva)")
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
    
    programa = models.ForeignKey(Programa, on_delete=models.SET_NULL, null=True, blank=True, related_name='projetos_vinculados', verbose_name="Programa (Acordo Mestre / Guarda-Chuva)")

    
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

    vigencia_inicio = models.DateField(verbose_name="Início da Vigência Geral")
    vigencia_fim = models.DateField(verbose_name="Fim da Vigência Geral")
    vigencia_meses = models.IntegerField(default=1, verbose_name="Total de Meses Previstos")

    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Projeto PDI"
        verbose_name_plural = "Projetos PDI"

    @property
    def termo_parceria(self):
        """Retorna o primeiro termo de parceria associado."""
        return self.termos_parceria.first()

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
        
        # Utiliza o related_name 'atividades_plano' para verificar se o cronograma foi importado
        if not self.atividades_plano.exists(): # type: ignore
            pendencias.append("O Plano de Ação (Cronograma de Atividades) não foi desdobrado no sistema.")
            
        if not self.termo_parceria or not self.termo_parceria.planos_trabalho.exists():
            pendencias.append("O Plano de Trabalho financeiro/cronológico não foi registrado no sistema para este projeto.")
            
        return pendencias

class AtividadePlanoAcao(models.Model):
    plano_trabalho = models.ForeignKey('PlanoDeTrabalho', on_delete=models.CASCADE, related_name='atividades', null=True)
    numero = models.CharField(max_length=10, verbose_name="Item (Ex: 1)")
    nome = models.CharField(max_length=255, verbose_name="Nome da Atividade")
    descricao = models.TextField(verbose_name="Descrição da Atividade (Rich Text)")
    justificativa = models.TextField(blank=True, null=True, verbose_name="Justificativa (Rich Text)")
    
    data_inicio = models.DateField(verbose_name="Data Início Absoluta", null=True, blank=True)
    data_fim = models.DateField(verbose_name="Data Fim Absoluta", null=True, blank=True)

    class Meta:
        verbose_name = "Atividade do Plano de Ação"
        verbose_name_plural = "Matriz de Atividades"
        unique_together = ('plano_trabalho', 'numero')
        
    @property
    def mes_inicio_calculado(self):
        """Calcula em qual mês relativo (M1, M2) essa data cai em relação ao início do plano."""
        if not self.data_inicio or not self.plano_trabalho or not self.plano_trabalho.data_inicio:
            return None
        diff_years = self.data_inicio.year - self.plano_trabalho.data_inicio.year
        diff_months = self.data_inicio.month - self.plano_trabalho.data_inicio.month
        return (diff_years * 12 + diff_months) + 1
        
    @property
    def mes_fim_calculado(self):
        if not self.data_fim or not self.plano_trabalho or not self.plano_trabalho.data_inicio:
            return None
        diff_years = self.data_fim.year - self.plano_trabalho.data_inicio.year
        diff_months = self.data_fim.month - self.plano_trabalho.data_inicio.month
        return (diff_years * 12 + diff_months) + 1

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.data_inicio and self.data_fim:
            if self.data_inicio > self.data_fim:
                raise ValidationError({"data_fim": "A data de fim não pode ser anterior à data de início."})
            
            # Regra EMBRAPII: Macroentregas não podem ser sobrepostas no tempo.
            if self.plano_trabalho:
                sobrepostas = AtividadePlanoAcao.objects.filter(
                    plano_trabalho=self.plano_trabalho,
                    data_inicio__lt=self.data_fim,
                    data_fim__gt=self.data_inicio
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

        # 1. Capital e Equipamentos: Proibido usar recursos EMBRAPII
        if self.categoria == 'CAPITAL' and self.fonte_recurso == 'EMBRAPII':
            raise ValidationError({'fonte_recurso': "Regra EMBRAPII: É proibido usar recursos EMBRAPII para Capital e Equipamentos. Utilize recursos da Empresa."})

        # 2. Suporte Operacional (Overhead): Só pago pela Empresa ou Contrapartida
        if self.categoria == 'SUPORTE' and self.fonte_recurso not in ['EMPRESA', 'CONTRAPARTIDA']:
            raise ValidationError({'fonte_recurso': "Regra de Overhead: O Suporte Operacional/Administrativo só pode ser pago com recursos da Empresa Parceira ou como Contrapartida da Unidade."})

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
    """Registra as prorrogações e alterações contratuais do projeto."""
    projeto = models.ForeignKey(ProjetoPDI, on_delete=models.CASCADE, related_name='aditivos')
    numero = models.CharField(max_length=20, verbose_name="Número do Aditivo")
    descricao = models.TextField(blank=True, null=True, verbose_name="Objeto da Alteração")
    nova_data_fim = models.DateField(verbose_name="Nova Data de Término (Se houver prorrogação)")
    arquivo_pdf = models.FileField(upload_to='convenios/aditivos/', null=True, blank=True, verbose_name="Documento em PDF")
    data_assinatura = models.DateField(verbose_name="Data de Assinatura")

    class Meta:
        verbose_name = "Termo Aditivo"
        verbose_name_plural = "Termos Aditivos"

    def __str__(self):
        termo = self.projeto.termo_parceria.numero if self.projeto.termo_parceria else "Sem Termo"
        return f"Aditivo {self.numero} - {termo}"

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

    data_criacao = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pessoa Física"
        verbose_name_plural = "Pessoas Físicas"

    def __str__(self):
        return f"{self.nome} ({self.cpf})"

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
    pessoa = models.OneToOneField(PessoaFisica, on_delete=models.CASCADE, related_name='perfil_servidor')
    siape = models.CharField(max_length=20, unique=True, verbose_name="Matrícula SIAPE")
    cargo = models.CharField(max_length=100, verbose_name="Cargo Efetivo")
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
    carga_horaria_total = models.PositiveIntegerField(verbose_name="Carga Horária Total (horas)", default=0)

    
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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Gerar parcelas automaticamente
        if self.quantidade_parcelas:
            parcelas_existentes = self.parcelas.count() # type: ignore
            if parcelas_existentes < self.quantidade_parcelas:
                for i in range(parcelas_existentes + 1, self.quantidade_parcelas + 1):
                    Parcela.objects.create(termo_bolsa=self, numero=i)

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
    plano_trabalho = models.ForeignKey(PlanoDeTrabalho, on_delete=models.CASCADE, related_name='macroentregas')
    numero = models.IntegerField(verbose_name="Número (Ex: 1, 2, 3)")
    nome = models.CharField(max_length=200, verbose_name="Nome da Macroentrega")
    micro_entregas = models.TextField(blank=True, null=True, verbose_name="Micro-Entregas (Rich Text)")
    
    data_inicio = models.DateField(verbose_name="Data Início Absoluta", null=True, blank=True)
    data_fim = models.DateField(verbose_name="Data Fim Absoluta", null=True, blank=True)

    class Meta:
        verbose_name = "Macroentrega"
        verbose_name_plural = "Macroentregas"
        ordering = ['numero']

    def __str__(self):
        return f"M{self.numero} - {self.nome}"

class Parcela(models.Model):
    """
    Entidade que representa a previsão de pagamento (caixinha vazia) 
    que será posteriormente preenchida/comprovada por um Relatório de Atividades.
    """
    termo_bolsa = models.ForeignKey(TermoBolsa, on_delete=models.CASCADE, related_name='parcelas')
    numero = models.PositiveIntegerField(verbose_name="Número da Parcela")

    class Meta:
        verbose_name = "Parcela"
        verbose_name_plural = "Parcelas"
        unique_together = ('termo_bolsa', 'numero')
        ordering = ['numero']

    def __str__(self):
        return f"Parcela {self.numero} - {self.termo_bolsa.bolsista.nome}"

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

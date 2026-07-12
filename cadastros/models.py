"""
argus/cadastros/models.py
"""
import re
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from decimal import Decimal

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
class InstituicaoParceira(models.Model):
    """Cadastro global de empresas e órgãos parceiros do Polo."""
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome da Instituição")
    sigla = models.CharField(max_length=20, unique=True)
    cnpj = models.CharField(max_length=18, blank=True, null=True)

    class Meta:
        verbose_name = "Instituição Parceira"
        verbose_name_plural = "Instituições Parceiras"

    def __str__(self):
        return self.sigla


class Convenio(models.Model):
    """Entidade macro jurídica que rege os repasses financeiros e metas."""
    instituicao = models.ForeignKey(InstituicaoParceira, on_delete=models.PROTECT, related_name='convenios')
    numero_convenio = models.CharField(max_length=50, unique=True, verbose_name="Número do Convênio")
    objeto = models.TextField(blank=True, null=True, verbose_name="Objeto / Descrição")
    data_inicio = models.DateField(blank=True, null=True)
    data_fim = models.DateField(blank=True, null=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Convênio"
        verbose_name_plural = "Convênios"

    def __str__(self):
        return f"{self.instituicao.sigla} - {self.numero_convenio}"


# =====================================================================
# PROJETO PDI (Aprimorado com Vínculo Estruturado)
# =====================================================================
class ProjetoPDI(models.Model):
    """Entidade Mestre do Polo de Inovação com regras estritas de vigência."""
    projeto = models.CharField(max_length=50, verbose_name="Projeto", null=True, blank=True, help_text="Campo opcional para nomear o projeto de forma resumida (ex: 'Projeto de Robótica').")
    nome = models.CharField(max_length=255, verbose_name="Nome Completo do Projeto")

    # Campo antigo (preservado temporariamente para não quebrar dados legados)
    convenio = models.CharField(
        max_length=9, 
        validators=[validar_convenio], 
        unique=True, 
        verbose_name="Número do Convênio"
    )
    
    # === A NOVA PONTE PARA O CONVÊNIO GLOBAL ESTRUTURADO ===
    convenio_oficial = models.ForeignKey(
        'Convenio',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projetos_pdi',
        verbose_name="Convênio Oficial (Estruturado)"
    )
    # =======================================================
    
    Processo = models.CharField(
        max_length=20,
        blank=True, 
        null=True,
        validators=[validar_processo_ifam], 
        verbose_name="Processo de Contratação do Projeto (IFAM)"
    )           
    
    termo_de_convenio = models.FileField(upload_to='convenios/termos/', null=True, blank=True, verbose_name="Termo de Convênio (PDF)")
    convenente = models.CharField(max_length=100, default="IFAM", verbose_name="Convenente")
    interveniente = models.CharField(max_length=100, default="FAEPI", verbose_name="Interveniente")
    financiadores = models.TextField(verbose_name="Concedentes / Financiador(es)", help_text="Razão social dos financiadores")

    vigencia_inicio = models.DateField(verbose_name="Início da Vigência Geral")
    vigencia_fim = models.DateField(verbose_name="Fim da Vigência Geral")

    plano_inicio = models.DateField(verbose_name="Início do Plano de Trabalho")
    plano_fim = models.DateField(verbose_name="Fim do Plano de Trabalho")

    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Projeto PDI"
        verbose_name_plural = "Projetos PDI"

    def __str__(self):
        return f"{self.convenio} - {self.nome}"

    def clean(self):
        """Validação lógica dos intervalos matemáticos de tempo."""
        super().clean()
        if self.vigencia_inicio and self.vigencia_fim:
            if self.vigencia_inicio > self.vigencia_fim:
                raise ValidationError({"vigencia_fim": "A data fim da vigência não pode ser anterior ao início."})

        if self.plano_inicio and self.plano_fim:
            if self.plano_inicio > self.plano_fim:
                raise ValidationError({"plano_fim": "A data fim do plano de trabalho não pode ser anterior ao início."})

        if self.vigencia_inicio and self.vigencia_fim and self.plano_inicio and self.plano_fim:
            if self.plano_inicio < self.vigencia_inicio or self.plano_fim > self.vigencia_fim:
                raise ValidationError(
                    "Regra Administrativa: O período do Plano de Trabalho deve estar estritamente contido dentro do intervalo de Vigência Geral do Convênio."
                )


# =====================================================================
# DEMAIS ENTIDADES DO MÓDULO DE CADASTROS (PRESERVADAS INTACTAS)
# =====================================================================
class ContaBancaria(models.Model):
    """Contas de repasse exclusivas gerenciadas pela Interveniente para o projeto."""
    projeto = models.ForeignKey(ProjetoPDI, on_delete=models.CASCADE, related_name='contas')
    banco = models.CharField(max_length=50, default="Banco do Brasil")
    agencia = models.CharField(max_length=20, blank=True, null=True, verbose_name="Agência")
    conta = models.CharField(max_length=50, verbose_name="Número da Conta")
    dv = models.CharField(max_length=5, verbose_name="Dígito Verificador")

    class Meta:
        verbose_name = "Conta Bancária"
        verbose_name_plural = "Contas Bancárias"

    def __str__(self):
        return f"{self.banco}: {self.conta}-{self.dv} (Proj: {self.projeto.convenio})"


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
        return f"Aditivo {self.numero} - {self.projeto.convenio}"


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


class Fornecedor(models.Model):
    """Cadastro de Credores e Empresas fornecedoras com dados estendidos."""
    nome = models.CharField(max_length=255, verbose_name="Razão Social / Nome")
    cnpj = models.CharField(max_length=20, unique=True, verbose_name="CNPJ")
    sigla = models.CharField(max_length=50, blank=True, null=True, verbose_name="Sigla / Nome Curto")
    endereco = models.CharField(max_length=255, blank=True, null=True, verbose_name="Endereço Completo")
    email = models.EmailField(blank=True, null=True, verbose_name="E-mail de Contato")

    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"

    def __str__(self):
        return f"{self.sigla if self.sigla else self.nome} ({self.cnpj})"
    

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
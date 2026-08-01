import re
from decimal import Decimal
from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from dateutil.relativedelta import relativedelta

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

# =====================================================================
# PROJETO PDI 
# =====================================================================
class ProjetoPDI(models.Model):
    """Entidade Mestre do Polo de Inovação com regras estritas de vigência e conformidade."""
    projeto = models.CharField(max_length=50, verbose_name="Projeto", null=True, blank=True, help_text="Campo opcional para nomear o projeto de forma resumida (ex: 'Projeto de Robótica').")
    nome = models.CharField(max_length=255, verbose_name="Nome Completo do Projeto")

    convenio = models.CharField(
        max_length=9, 
        validators=[validar_convenio], 
        unique=True, 
        verbose_name="Número do Convênio"
    )
    
    convenio_oficial = models.ForeignKey(
        'Convenio',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projetos_pdi',
        verbose_name="Convênio Oficial (Estruturado)"
    )
    
    processo = models.CharField(
        db_column='Processo',
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

    def verificar_pendencias(self):
        """Avalia se o projeto possui todas as travas obrigatórias para operação e liberação de relatórios."""
        pendencias = []
        
        # Utiliza o related_name 'atividades_plano' para verificar se o cronograma foi importado
        if not self.atividades_plano.exists(): # type: ignore
            pendencias.append("O Plano de Ação (Cronograma de Atividades) não foi desdobrado no sistema.")
            
        if not hasattr(self, 'planotrabalho'):
            pendencias.append("O Plano de Trabalho financeiro/cronológico não foi registrado no sistema para este projeto.")
            
        return pendencias

class AtividadePlanoAcao(models.Model):
    projeto = models.ForeignKey('ProjetoPDI', on_delete=models.CASCADE, related_name='atividades_plano')
    numero = models.CharField(max_length=10, verbose_name="Item (Ex: 1)")
    nome = models.CharField(max_length=255, verbose_name="Nome da Atividade")
    descricao = models.TextField(verbose_name="Descrição da Atividade")
    justificativa = models.TextField(blank=True, null=True)
    entregaveis = models.TextField(blank=True, null=True)
    
    # Armazenamento do cronograma relativo extraído do .docx
    mes_inicio_relativo = models.PositiveIntegerField(help_text="Mês de início (Ex: 1)")
    mes_fim_relativo = models.PositiveIntegerField(help_text="Mês de fim (Ex: 9)")

    class Meta:
        verbose_name = "Atividade do Plano de Ação"
        verbose_name_plural = "Matriz de Atividades"
        unique_together = ('projeto', 'numero')

    @property
    def data_inicio_real(self):
        """Calcula a data absoluta de início baseada no 'Calendário ARGUS' do projeto."""
        if not hasattr(self.projeto, 'planotrabalho') or not self.projeto.planotrabalho.data_inicio:
            return None
        # Se inicia no Mês 1, a data é a mesma do plano. Se Mês 2, soma 1 mês.
        return self.projeto.planotrabalho.data_inicio + relativedelta(months=(self.mes_inicio_relativo - 1))

    @property
    def data_fim_real(self):
        """Calcula a data absoluta de término. Subtrai 1 dia para não invadir o mês seguinte."""
        if not hasattr(self.projeto, 'planotrabalho') or not self.projeto.planotrabalho.data_inicio:
            return None
        # Se termina no Mês 9, soma 9 meses a partir do início e subtrai 1 dia (último dia do mês 9)
        return self.projeto.planotrabalho.data_inicio + relativedelta(months=self.mes_fim_relativo) - relativedelta(days=1)

    def __str__(self):
        return f"{self.projeto.convenio} | {self.numero}: {self.nome}"

class PlanoTrabalho(models.Model):
    """
    Entidade Mestre do Módulo Financeiro.
    Representa o documento orçamentário e cronológico do projeto.
    """
    projeto = models.OneToOneField(ProjetoPDI, on_delete=models.CASCADE, related_name='planotrabalho')
    versao = models.IntegerField(default=1, verbose_name="Versão do Plano (Aditivos)")
    arquivo_pdf = models.FileField(upload_to='projetos/planos_trabalho/', null=True, blank=True, verbose_name="Plano de Trabalho Vigente (PDF)")
    
    data_inicio = models.DateField(verbose_name="Início do Plano de Trabalho")
    data_fim = models.DateField(verbose_name="Fim do Plano de Trabalho")
    total_meses = models.PositiveIntegerField(verbose_name="Total de Meses do Projeto", default=1)
    
    valor_global = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Valor Global (R$)")
    aporte_empresa = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Aporte Empresa (R$)")
    aporte_embrapii = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Aporte EMBRAPII (R$)")
    aporte_sebrae = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Aporte SEBRAE (R$)")
    aporte_contrapartida = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Contrapartida (R$)")

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
        if self.data_inicio and self.data_fim:
            from django.core.exceptions import ValidationError
            if self.data_inicio > self.data_fim:
                raise ValidationError({"data_fim": "A data fim do plano de trabalho não pode ser anterior ao início."})

        # Verifica se as datas do plano estão dentro da vigência do projeto
        if hasattr(self, 'projeto') and self.projeto.vigencia_inicio and self.projeto.vigencia_fim:
            if self.data_inicio < self.projeto.vigencia_inicio or self.data_fim > self.projeto.vigencia_fim:
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    "Regra Administrativa: O período do Plano de Trabalho deve estar estritamente contido dentro do intervalo de Vigência Geral do Convênio."
                )

    @property
    def total_i_v(self):
        return sum(item.valor_previsto for item in self.rubricas.all() if item.categoria in ['I', 'II', 'III', 'IV', 'V'])

    @property
    def total_vi(self):
        return sum(item.valor_previsto for item in self.rubricas.all() if item.categoria == 'VI')

    @property
    def total_i_vi(self):
        return self.total_i_v + self.total_vi

    @property
    def total_vii(self):
        return sum(item.valor_previsto for item in self.rubricas.all() if item.categoria == 'VII')

    @property
    def total_bruto(self):
        return self.total_i_vi + self.total_vii

    class Meta:
        verbose_name = "Plano de Trabalho"
        verbose_name_plural = "Planos de Trabalho"

    def __str__(self):
        return f"PT V{self.versao} - {self.projeto.convenio}"

class RubricaOrcamentariaPT(models.Model):
    """
    Tabela de categorias de dispêndio atreladas ao Plano de Trabalho.
    """
    CATEGORIAS = [
        ('I', 'I - Programas de Computador ou Equipamentos'),
        ('II', 'II - Aquisição, Implantação, Ampliação ou Modernização de laboratório de P&D'),
        ('III', 'III - Recursos Humanos Diretos e Indiretos'),
        ('IV', 'IV - Serviço de Terceiros Técnicos'),
        ('V', 'V - Material de Consumo'),
        ('VI', 'VI - Outros Dispêndios Correlatos'),
        ('VII', 'VII - Custos Incorridos (DOAS/Reserva)'),
    ]
    
    FONTES = [
        ('EMPRESA', 'Empresa'),
        ('EMBRAPII', 'EMBRAPII'),
        ('SEBRAE', 'SEBRAE'),
        ('CONTRAPARTIDA', 'Contrapartida ICT'),
    ]

    plano_trabalho = models.ForeignKey(PlanoTrabalho, on_delete=models.CASCADE, related_name='rubricas')
    categoria = models.CharField(max_length=50, choices=CATEGORIAS, verbose_name="Categoria / Dispêndio")
    descricao = models.CharField(max_length=255, blank=True, null=True, verbose_name="Descrição do Item")
    valor_previsto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Previsto (R$)")
    fonte_recurso = models.CharField(max_length=50, choices=FONTES, verbose_name="Fonte do Recurso")

    class Meta:
        verbose_name = "Rubrica Orçamentária"
        verbose_name_plural = "Rubricas Orçamentárias"

    def __str__(self):
        return f"{self.get_categoria_display()} ({self.get_fonte_recurso_display()}) - R$ {self.valor_previsto}"

class ContaBancaria(models.Model):
    """Contas de repasse exclusivas gerenciadas pela Interveniente para o projeto."""
    projeto = models.ForeignKey(ProjetoPDI, on_delete=models.CASCADE, related_name='contas')
    
    # Campo adicionado para identificação da origem orçamentária
    fonte_recurso = models.CharField(
        max_length=100, 
        verbose_name="Fonte do Recurso", 
        help_text="Ex: EMBRAPII, SEBRAE, Empresa Parceira"
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
        return f"Aditivo {self.numero} - {self.projeto.convenio}"

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
        return f"{self.perfil_funcao} ({self.quantidade_vagas} vaga/s) - {self.projeto.convenio}"

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
    bolsista_nome = models.CharField(max_length=255) 
    bolsista_cpf = models.CharField(max_length=14)
    
    numero_termo = models.CharField(max_length=50, verbose_name="Número do Termo de Bolsa/Aditivo")
    vigencia_inicio = models.DateField()
    vigencia_fim = models.DateField()
    
    # Execução financeira real deste contrato específico
    quantidade_parcelas = models.PositiveIntegerField(verbose_name="Parcelas Contratadas (Neste Termo)")
    valor_parcela = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor da Parcela (R$)")
    
    status = models.CharField(max_length=20, choices=STATUS_TERMO, default='ATIVO')

    def clean(self):
        super().clean()
        
        # Impede exceções matemáticas se os campos obrigatórios ainda não foram preenchidos na interface
        if not self.quantidade_parcelas or not self.valor_parcela or not self.cota_pt_id:
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

    def __str__(self):
        return f"Termo {self.numero_termo} - {self.bolsista_nome} ({self.get_status_display()})"

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
    plano_trabalho = models.ForeignKey(PlanoTrabalho, on_delete=models.CASCADE, related_name='macroentregas')
    numero = models.IntegerField(verbose_name="Número (Ex: 1, 2, 3)")
    nome = models.CharField(max_length=200, verbose_name="Nome da Macroentrega")
    mes_inicio_relativo = models.PositiveIntegerField(verbose_name="Mês Início")
    mes_fim_relativo = models.PositiveIntegerField(verbose_name="Mês Fim")

    class Meta:
        verbose_name = "Macroentrega"
        verbose_name_plural = "Macroentregas"
        ordering = ['numero']

    def __str__(self):
        return f"M{self.numero} - {self.nome}"
"""
argus/almoxarifado/models.py
"""
import os
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal
from cadastros.models import ProjetoPDI
from django.conf import settings
from django.utils import timezone

class PerfilUsuario(models.Model):
    """
    Estende o usuário nativo do Django com dados institucionais,
    suportando tanto servidores efetivos quanto equipe terceirizada.
    """
    VINCULO_CHOICES = [
        ('SERVIDOR', 'Servidor Público'),
        ('TERCEIRIZADO', 'Colaborador Terceirizado'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    
    vinculo = models.CharField(
        max_length=20, 
        choices=VINCULO_CHOICES, 
        default='SERVIDOR', 
        verbose_name="Tipo de Vínculo"
    )
    
    siape = models.CharField(max_length=15, unique=True, null=True, blank=True, verbose_name="Matrícula SIAPE")
    cpf = models.CharField(max_length=14, unique=True, null=True, blank=True, verbose_name="CPF")
    cargo = models.CharField(max_length=100, verbose_name="Cargo / Função")
    lotacao = models.CharField(max_length=100, default="Polo de Inovação Manaus", verbose_name="Lotação")

    class Meta:
        verbose_name = "Perfil de Usuário"
        verbose_name_plural = "Perfis de Usuários"

    def __str__(self):
        identificacao = f"SIAPE: {self.siape}" if self.vinculo == 'SERVIDOR' else f"Terceirizado"
        return f"{self.user.get_full_name()} ({identificacao})"

class Imposto(models.Model):
    """
    Catálogo central de impostos. O Administrador cadastra aqui as siglas (ex: PIS, COFINS, ICMS) 
    e define a qual esfera elas pertencem.
    """
    ESFERA_CHOICES = [
        ('FEDERAL', 'Federal'),
        ('ESTADUAL', 'Estadual'),
        ('MUNICIPAL', 'Municipal'),
    ]
    
    sigla = models.CharField(max_length=20, unique=True, verbose_name="Sigla do Imposto")
    descricao = models.CharField(max_length=100, blank=True, null=True, verbose_name="Descrição")
    esfera = models.CharField(max_length=15, choices=ESFERA_CHOICES, verbose_name="Esfera Tributária")

    def __str__(self):
        return f"{self.sigla} ({self.get_esfera_display()})" # type: ignore

class ImpostoNota(models.Model):
    """
    Tabela relacional. Vincula um imposto específico a uma nota fiscal e guarda o valor cobrado.
    """
    nota = models.ForeignKey('NotaFiscalAlmoxarifado', on_delete=models.CASCADE, related_name='tributos_reais')
    imposto = models.ForeignKey(Imposto, on_delete=models.PROTECT, related_name='notas_vinculadas')
    valor = models.DecimalField(max_digits=10, decimal_places=4, verbose_name="Valor do Imposto")

    def __str__(self):
        return f"{self.imposto.sigla} - R$ {self.valor} (NF: {self.nota.numero})"

class NotaFiscalAlmoxarifado(models.Model):
    """
    Representa a capa (metadados) da Nota Fiscal Eletrônica.
    """
    numero = models.CharField(max_length=20, verbose_name="Número NF-e")
    serie = models.CharField(max_length=10, verbose_name="Série")
    data_emissao = models.DateField(verbose_name="Data de Emissão")
    data_importacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Importação no Sistema")
    
    # NOVOS CAMPOS FINANCEIROS (Substituindo o antigo valor_total)
    valor_total_produtos = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name="Valor Total dos Produtos"
    )
    valor_desconto = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name="Desconto Aplicado"
    )
    valor_total_nota = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name="Valor Total da Nota"
    )
    valor_frete = models.DecimalField(
        max_digits=12, decimal_places=4, default=Decimal('0.0000'),
        verbose_name='Valor do Frete'
    )
    
    fornecedor = models.ForeignKey(
        'cadastros.Fornecedor', 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True, 
        related_name='notas_almoxarifado',
        verbose_name="Fornecedor Oficial"
    )

    destinatario_nome = models.CharField(max_length=255, verbose_name="Razão Social Destinatário")
    destinatario_cnpj = models.CharField(max_length=20, verbose_name="CNPJ Destinatário")
    
    arquivo_pdf = models.FileField(upload_to='almoxarifado/nfe/', null=True, blank=True, verbose_name="Arquivo Digital (PDF/XML)")

    termo_recebimento_assinado = models.FileField(
        upload_to='almoxarifado/termos_assinados/', 
        null=True, 
        blank=True, 
        verbose_name="Termo de Recebimento Assinado (PDF)"
    )

    # ATRIBUTOS INTEGRADOS PARA AUDITORIA E FÍSICO
    chave_acesso = models.CharField(max_length=44, null=True, blank=True, verbose_name="Chave de Acesso Sefaz")
    data_recebimento = models.DateField(null=True, blank=True, verbose_name="Data de Recebimento Físico")
    
    usuario_recebedor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='notas_recebidas',
        verbose_name="Servidor/Colaborador que Recebeu"
    )

    # VÍNCULO CORRETO COM O PROJETO PDI DO MÓDULO CADASTRADOS
    projeto_vinculado = models.ForeignKey(
        'cadastros.ProjetoPDI', # Ajuste o caminho se a classe estiver importada diretamente
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notas_fiscais_almoxarifado',
        verbose_name="Projeto PDI de Destino"
    )

    class Meta:
        unique_together = ('numero', 'fornecedor')  # Evita duplicidade de NF para o mesmo fornecedor
        verbose_name = "Nota Fiscal de Entrada"
        verbose_name_plural = "Notas Fiscais de Entrada"

    def clean(self):
            super().clean()
            if self.valor_total_nota is not None and self.valor_total_produtos is not None and self.valor_desconto is not None:
                valor_base_esperado = self.valor_total_produtos - self.valor_desconto
                margem_tolerancia = Decimal('0.01')
                
                if self.valor_total_nota < (valor_base_esperado - margem_tolerancia):
                    raise ValidationError({
                        'valor_total_nota': 'Inconsistência fiscal: O Valor Total da Nota não pode ser inferior ao líquido dos produtos.'
                    })

    @property
    def soma_itens_calculada(self):
        """
        Calcula dinamicamente a soma real dos valores de todos os insumos vinculados a esta nota.
        """
        # pyrefly: ignore [missing-import]
        from django.db.models import Sum
        from decimal import Decimal
        


        total = self.produtos.aggregate(soma=Sum('valor_total'))['soma']         # type: ignore
        return total if total else Decimal('0.00')

    @property
    def inconsistencia_produtos(self):
        """
        Retorna True se a soma dos produtos cadastrados for diferente do valor declarado na capa.
        Tolerância de 2 centavos para evitar falsos positivos por arredondamento de dízimas.
        """
        return abs(self.valor_total_produtos - self.soma_itens_calculada) > Decimal('0.02')

    def __str__(self):
        nome_fornecedor = self.fornecedor.sigla if (self.fornecedor and self.fornecedor.sigla) else (self.fornecedor.nome if self.fornecedor else "Sem Fornecedor")
        return f"NF-e #{self.numero} - {nome_fornecedor[:30]}"

class ProdutoAlmoxarifado(models.Model):
    """
    Representa cada item individual vinculado a uma Nota Fiscal.
    """
    class CategoriaMaterial(models.TextChoices):
        CONSUMO = 'CONSUMO', 'Consumo'
        PERMANENTE = 'PERMANENTE', 'Bem Permanente'
        SERVICO = 'SERVICO', 'Serviço / Outros'

    nota_fiscal = models.ForeignKey(
        'NotaFiscalAlmoxarifado', # Como String para evitar erro de importação circular
        on_delete=models.CASCADE, 
        related_name='produtos', 
        verbose_name="Nota Fiscal Origem"
    )
    numero_item = models.PositiveIntegerField(verbose_name="Nº do Item")
    descricao = models.TextField(verbose_name="Descrição do Produto/Insumo")
    categoria = models.CharField(
        max_length=20, 
        choices=CategoriaMaterial.choices, 
        default=CategoriaMaterial.CONSUMO, 
        verbose_name="Classificação Patrimonial"
    )
    
    # ATUALIZAÇÃO PARA DECIMAL
    # Usamos 4 casas decimais para Quantidade e Valor Unitário pois em NF-e 
    # é comum termos valores como 1,5550 kg ou R$ 0,1234 (ex: energia/combustível)
    quantidade = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name="Quantidade Entregue"
    )
    unidade_comercial = models.CharField(max_length=10, verbose_name="Unidade de Medida")
    
    valor_unitario = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name="Valor Unitário"
    )
    
    # Valor Total do Item costuma ter apenas 2 casas (dinheiro final da linha)
    valor_total = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name="Valor Total do Item"
    )

    class Meta:
        verbose_name = "Material Cadastrado"
        verbose_name_plural = "Materiais Cadastrados"

    def __str__(self):
        return f"NF #{self.nota_fiscal.numero} | Item {self.numero_item} - {self.descricao[:30]}"

class FotoProduto(models.Model):
    """
    Armazena o registo fotográfico dos bens no momento do recebimento.
    """
    produto = models.ForeignKey(
        ProdutoAlmoxarifado, 
        on_delete=models.CASCADE, 
        related_name='fotos',
        verbose_name="Produto Associado"
    )
    imagem = models.ImageField(upload_to='almoxarifado/fotos_produtos/', verbose_name="Fotografia do Bem")
    
    descricao = models.CharField(max_length=200, null=True, blank=True, verbose_name="Descrição da Fotografia")

    data_upload = models.DateTimeField(auto_now_add=True, verbose_name="Data da Fotografia")

    class Meta:
        verbose_name = "Foto do Produto"
        verbose_name_plural = "Fotos dos Produtos"

    def __str__(self):
        return f"Foto de {self.produto.descricao}"

class CotaDiariaIA(models.Model):
    """
    Controla o consumo diário de requisições à API da IA.
    """
    data = models.DateField(unique=True, verbose_name="Data de Controle")
    requisicoes_feitas = models.PositiveIntegerField(default=0, verbose_name="Chamadas Executadas")
    limite_diario = models.PositiveIntegerField(default=100, verbose_name="Teto Diário Permitido")

    class Meta:
        verbose_name = "Cota Diária da IA"
        verbose_name_plural = "Cotas Diárias da IA"

    def __str__(self):
        return f"{self.data} ({self.requisicoes_feitas}/{self.limite_diario})"
    
@receiver(post_delete, sender=NotaFiscalAlmoxarifado)
def deletar_arquivos_nota_fiscal(sender, instance, **kwargs):
    """
    Escuta a exclusão de uma Nota Fiscal e apaga os arquivos físicos (PDFs) do disco do servidor.
    """
    # 1. Apaga o PDF original da NFE
    if instance.arquivo_pdf and os.path.isfile(instance.arquivo_pdf.path):
        os.remove(instance.arquivo_pdf.path)
        
    # 2. Apaga o Termo de Recebimento Assinado (se houver)
    if instance.termo_recebimento_assinado and os.path.isfile(instance.termo_recebimento_assinado.path):
        os.remove(instance.termo_recebimento_assinado.path)


@receiver(post_delete, sender=FotoProduto)
def deletar_arquivos_foto_produto(sender, instance, **kwargs):
    """
    Escuta a exclusão de uma FotoProduto (mesmo que em cascata) e apaga a imagem do disco.
    """
    if instance.imagem and os.path.isfile(instance.imagem.path):
        os.remove(instance.imagem.path)


class TermoRME(models.Model):
    """
    Matriz do Recibo de Material e Equipamento.
    Garante a rastreabilidade patrimonial e a auditoria de recebimento.
    """
    STATUS_CHOICES = [
        ('AGUARDANDO_CONFERENCIA', 'Aguardando Conferência Física'),
        ('DIVERGENTE', 'Divergência Encontrada'),
        ('ATESTADO', 'Atestado (Recebido)'),
    ]

    # Identificação Única e Relacionamentos
    numero_termo = models.CharField(max_length=20, unique=True, verbose_name="Número do RME", help_text="Ex: RME-2026/001")
    nota_fiscal = models.OneToOneField('NotaFiscalAlmoxarifado', on_delete=models.PROTECT, related_name='termo_rme')
    processo_sei = models.CharField(max_length=30, blank=True, null=True, verbose_name="Processo SEI Associado")
    
    # Rastreabilidade e Segregação de Funções
    servidor_conferente = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.RESTRICT, 
        related_name='rmes_conferidos',
        verbose_name="Servidor Conferente (SIAPE)"
    )
    
    data_geracao = models.DateTimeField(auto_now_add=True)
    data_ateste = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='AGUARDANDO_CONFERENCIA')
    observacoes = models.TextField(blank=True, null=True, help_text="Anotações sobre avarias ou divergências na entrega.")

    class Meta:
        verbose_name = "Termo de Recebimento (RME)"
        verbose_name_plural = "Termos de Recebimento (RME)"
        ordering = ['-data_geracao']

    def __str__(self):
        return f"{self.numero_termo} - NF: {self.nota_fiscal.numero}" # type: ignore

    def atestar_recebimento(self):
        """Método de negócio para cravar o ateste oficial no banco de dados."""
        self.status = 'ATESTADO'
        self.data_ateste = timezone.now()
        self.save()
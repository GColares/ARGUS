from simple_history.models import HistoricalRecords
# pyrefly: ignore [untyped-import]
from django.db import models
# pyrefly: ignore [untyped-import]
from django.contrib.auth.models import User
from cadastros.models import Fornecedor
from almoxarifado.models import ProdutoAlmoxarifado
import uuid

class Finalidade(models.Model):
    nome = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nome

class Predio(models.Model):
    RISCO_QUIMICO_CHOICES = [
        ('BAIXO', 'Baixo'),
        ('MEDIO', 'Médio'),
        ('ALTO', 'Alto'),
    ]
    RISCO_BIOLOGICO_CHOICES = [
        ('NB1', 'NB-1'),
        ('NB2', 'NB-2'),
        ('NB3', 'NB-3'),
        ('NB4', 'NB-4'),
    ]

    nome = models.CharField(max_length=100)
    sigla = models.CharField(max_length=20, blank=True, null=True)
    
    # Identificação Básica Adicional
    finalidades = models.ManyToManyField(Finalidade, blank=True, related_name='predios', verbose_name="Finalidades do Prédio")
    area_total_m2 = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Área Total (m²)")
    capacidade_pessoas = models.PositiveIntegerField(blank=True, null=True)
    
    # Infraestrutura Crítica
    possui_geracao_solar = models.BooleanField(null=True, blank=True, verbose_name="Possui Geração Solar?")
    capacidade_geracao_solar_kwp = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="Capacidade Solar (kWp)")
    quantidade_placas_solares = models.PositiveIntegerField(blank=True, null=True, verbose_name="Quantidade de Placas Solares")
    
    possui_gerador_emergencia = models.BooleanField(null=True, blank=True, verbose_name="Possui Gerador de Emergência?")
    possui_subestacao_propria = models.BooleanField(null=True, blank=True, verbose_name="Possui Subestação Própria?")
    possui_climatizacao_central = models.BooleanField(null=True, blank=True, verbose_name="Possui Climatização Central?")
    possui_rede_gases_especiais = models.BooleanField(null=True, blank=True, verbose_name="Possui Rede de Gases Especiais?")
    possui_sala_limpa = models.BooleanField(null=True, blank=True, verbose_name="Possui Sala Limpa?")
    
    # Classificação de Riscos
    risco_quimico = models.CharField(max_length=10, choices=RISCO_QUIMICO_CHOICES, blank=True, null=True)
    risco_biologico = models.CharField(max_length=10, choices=RISCO_BIOLOGICO_CHOICES, blank=True, null=True)
    armazena_inflamaveis = models.BooleanField(null=True, blank=True, verbose_name="Armazena Inflamáveis?")
    possui_ete_sanitaria = models.BooleanField(null=True, blank=True, verbose_name="Possui ETE Sanitária?")
    possui_ete_especial = models.BooleanField(null=True, blank=True, verbose_name="Possui ETE Especial/Industrial?")
    
    # Segurança e Licenças
    avcb_numero = models.CharField(max_length=50, blank=True, null=True, verbose_name="Nº AVCB")
    avcb_validade = models.DateField(blank=True, null=True, verbose_name="Validade AVCB")
    avcb_arquivo = models.FileField(upload_to='licencas/avcb/', blank=True, null=True, verbose_name="Arquivo AVCB")
    licenca_ambiental_numero = models.CharField(max_length=50, blank=True, null=True, verbose_name="Nº Licença Ambiental")
    licenca_ambiental_validade = models.DateField(blank=True, null=True, verbose_name="Validade Licença Ambiental")
    licenca_ambiental_arquivo = models.FileField(upload_to='licencas/ambiental/', blank=True, null=True, verbose_name="Arquivo Licença Ambiental")
    licenca_vigilancia_sanitaria_numero = models.CharField(max_length=50, blank=True, null=True, verbose_name="Nº Licença Vig. Sanitária")
    licenca_vigilancia_sanitaria_validade = models.DateField(blank=True, null=True, verbose_name="Validade Vig. Sanitária")
    licenca_vigilancia_sanitaria_arquivo = models.FileField(upload_to='licencas/vigilancia/', blank=True, null=True, verbose_name="Arquivo Vig. Sanitária")
    brigada_incendio_ativa = models.BooleanField(null=True, blank=True, verbose_name="Brigada de Incêndio Ativa?")
    ordem = models.PositiveIntegerField(default=0, verbose_name="Ordem")
    history = HistoricalRecords()

    class Meta:
        ordering = ['ordem']

    # pyrefly: ignore [bad-override]
    def __str__(self):
        return self.nome

class Andar(models.Model):
    predio = models.ForeignKey(Predio, on_delete=models.CASCADE, related_name='andares')
    nome = models.CharField(max_length=50)
    ordem = models.PositiveIntegerField(default=0, verbose_name="Ordem")
    history = HistoricalRecords()

    class Meta:
        ordering = ['ordem']

    def __str__(self):
        return f"{self.predio.sigla or self.predio.nome} - {self.nome}"

class TipoAmbiente(models.Model):
    nome = models.CharField(max_length=100, unique=True, verbose_name="Tipo de Ambiente")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    history = HistoricalRecords()
    
    def __str__(self):
        return self.nome
        
    class Meta:
        verbose_name = "Tipo de Ambiente"
        verbose_name_plural = "Tipos de Ambiente"
        ordering = ['nome']

class Ambiente(models.Model):
    LOCALIZACAO_CHOICES = [
        ('INTERNO', 'Área Interna'),
        ('EXTERNO', 'Área Externa'),
    ]
    predio = models.ForeignKey(Predio, on_delete=models.CASCADE, related_name='ambientes')
    andar = models.ForeignKey(Andar, on_delete=models.SET_NULL, null=True, blank=True, related_name='ambientes', help_text="Deixe em branco para áreas externas")
    nome = models.CharField(max_length=100)
    tipo = models.ForeignKey(TipoAmbiente, on_delete=models.PROTECT, related_name='ambientes')
    localizacao = models.CharField(max_length=10, choices=LOCALIZACAO_CHOICES, default='INTERNO')
    ordem = models.PositiveIntegerField(default=0, verbose_name="Ordem")
    history = HistoricalRecords()

    class Meta:
        ordering = ['ordem']

    def __str__(self):
        if self.andar:
            return f"{self.predio.sigla or self.predio.nome} - {self.andar.nome} - {self.nome}"
        return f"{self.predio.sigla or self.predio.nome} - {self.nome} ({self.get_localizacao_display()})"

class CategoriaElemento(models.Model):
    nome = models.CharField(max_length=100, unique=True, help_text="Ex: Piso, Parede, Janela, Forro")
    
    def __str__(self):
        return self.nome
        
    class Meta:
        verbose_name = "Categoria de Elemento"
        verbose_name_plural = "Categorias de Elementos"
        ordering = ['nome']

class TipoElemento(models.Model):
    categoria = models.ForeignKey(CategoriaElemento, on_delete=models.CASCADE, related_name='tipos')
    nome = models.CharField(max_length=100, help_text="Ex: Piso Frio, Piso Acarpetado, Parede Drywall")
    
    def __str__(self):
        return f"{self.categoria.nome}: {self.nome}"
        
    class Meta:
        verbose_name = "Tipo de Elemento"
        verbose_name_plural = "Tipos de Elementos"
        ordering = ['categoria__nome', 'nome']

class ElementoConstrutivo(models.Model):
    ambiente = models.ForeignKey(Ambiente, on_delete=models.CASCADE, related_name='elementos_construtivos')
    tipo = models.ForeignKey(TipoElemento, on_delete=models.PROTECT)
    area_m2 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Área (m²)")
    detalhes = models.TextField(blank=True, null=True, help_text="Especificações ou detalhes para cálculo da IN 05/2017")
    history = HistoricalRecords()
    
    def __str__(self):
        return f"{self.tipo.nome} - {self.area_m2}m² ({self.ambiente.nome})"

class TipoAtivo(models.Model):
    nome = models.CharField(max_length=100, unique=True, verbose_name="Tipo de Ativo")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    history = HistoricalRecords()

    def __str__(self):
        return self.nome
        
    class Meta:
        verbose_name = "Tipo de Ativo"
        verbose_name_plural = "Tipos de Ativos"
        ordering = ['nome']

class AtivoPredial(models.Model):
    ambiente = models.ForeignKey(Ambiente, on_delete=models.SET_NULL, null=True, blank=True, related_name='ativos', verbose_name="Ambiente")
    tipo = models.ForeignKey(TipoAtivo, on_delete=models.PROTECT, related_name='ativos', null=True, verbose_name="Tipo de Ativo")
    nome_apelido = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nome/Apelido")
    numero_serie = models.CharField(max_length=100, blank=True, null=True, verbose_name="Número de Série")
    patrimonio = models.CharField(max_length=50, blank=True, null=True, verbose_name="Número de Patrimônio")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.nome_apelido or self.tipo} ({self.ambiente})"

class CategoriaServico(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Categoria de Serviço"
        verbose_name_plural = "Categorias de Serviço"

    # pyrefly: ignore [bad-override]
    def __str__(self):
        return self.nome

class OrdemServico(models.Model):
    objects = models.Manager()
    
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('PROGRAMADA', 'Programada'),
        ('INICIADA', 'Iniciada'),
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('SUSPENSA', 'Suspensa'),
        ('CONCLUIDA', 'Concluída'),
        ('CANCELADA', 'Cancelada'),
    ]
    PRIORIDADE_CHOICES = [
        ('BAIXA', 'Baixa'),
        ('MEDIA', 'Média'),
        ('ALTA', 'Alta'),
        ('URGENTE', 'Urgente'),
    ]

    numero = models.CharField(max_length=20, unique=True, editable=False)
    categoria = models.ForeignKey(CategoriaServico, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Categoria")
    solicitante = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='os_solicitadas', verbose_name='Solicitante')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    prioridade = models.CharField(max_length=20, choices=PRIORIDADE_CHOICES, default='MEDIA')
    
    ambiente = models.ForeignKey(Ambiente, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordens_servico', verbose_name="Ambiente")
    ativo_predial = models.ForeignKey(AtivoPredial, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordens_servico')
    
    descricao_problema = models.TextField()
    laudo_tecnico = models.TextField(blank=True, null=True)
    motivo_cancelamento = models.TextField(blank=True, null=True, verbose_name="Motivo do Cancelamento")
    
    data_abertura = models.DateTimeField(auto_now_add=True)
    data_previsao = models.DateField(blank=True, null=True)
    data_conclusao = models.DateTimeField(blank=True, null=True)
    
    fornecedor_responsavel = models.ForeignKey(Fornecedor, on_delete=models.SET_NULL, null=True, blank=True, related_name='os_manutencao')
    servidor_responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='os_manutencao_interna')
    
    estoque_baixado = models.BooleanField(default=False, editable=False)

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = f"OS-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.numero} - {self.get_status_display()}"

class MaterialUtilizado(models.Model):
    ordem_servico = models.ForeignKey(OrdemServico, on_delete=models.CASCADE, related_name='materiais')
    produto_almoxarifado = models.ForeignKey(ProdutoAlmoxarifado, on_delete=models.PROTECT)
    quantidade = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.quantidade}x {self.produto_almoxarifado} na {self.ordem_servico.numero}"

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

@receiver(post_save, sender=OrdemServico)
def dar_baixa_estoque(sender, instance, created, **kwargs):
    # Quando o status muda para CONCLUIDA e o estoque ainda não foi baixado, debita do almoxarifado
    if instance.status == 'CONCLUIDA' and not instance.estoque_baixado:
        for material in instance.materiais.all():
            if material.produto_almoxarifado.quantidade >= material.quantidade:
                material.produto_almoxarifado.quantidade -= material.quantidade
                material.produto_almoxarifado.save()
        
        # Atualiza o banco direto para evitar loop no post_save
        OrdemServico.objects.filter(pk=instance.pk).update(estoque_baixado=True)
        instance.estoque_baixado = True

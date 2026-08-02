# pyrefly: ignore [untyped-import]
from django.db import models
# pyrefly: ignore [untyped-import]
from django.contrib.auth.models import User
from cadastros.models import Fornecedor
from almoxarifado.models import ProdutoAlmoxarifado
import uuid

class Predio(models.Model):
    nome = models.CharField(max_length=100)
    sigla = models.CharField(max_length=20, blank=True, null=True)

    # pyrefly: ignore [bad-override]
    def __str__(self):
        return self.nome

class Andar(models.Model):
    predio = models.ForeignKey(Predio, on_delete=models.CASCADE, related_name='andares')
    nome = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.predio.sigla or self.predio.nome} - {self.nome}"

class Sala(models.Model):
    andar = models.ForeignKey(Andar, on_delete=models.CASCADE, related_name='salas')
    nome = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.andar} - {self.nome}"

class AtivoPredial(models.Model):
    sala = models.ForeignKey(Sala, on_delete=models.SET_NULL, null=True, blank=True, related_name='ativos')
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True, null=True)
    patrimonio = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.nome} ({self.sala})"

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
    
    sala = models.ForeignKey(Sala, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordens_servico')
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

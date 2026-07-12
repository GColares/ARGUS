"""
argus/incorporacao/models.py
"""

from django.db import models
from cadastros.models import OrigemDoacao, ProjetoPDI, ContaBancaria, Processo, Localizacao

class TermoDoacao(models.Model):
    """
    Representa o documento principal (Termo de Doação) recebido pelo Gabinete.
    """
    projeto = models.ForeignKey(ProjetoPDI, on_delete=models.PROTECT, related_name='termos')
    origem = models.ForeignKey(OrigemDoacao, on_delete=models.PROTECT, verbose_name="Entidade de Origem")
    
    numero = models.CharField(max_length=20, verbose_name="Número do Documento")
    ano = models.CharField(max_length=4, verbose_name="Ano")

    data = models.DateField(verbose_name="Data de Formalização")
    
    objeto = models.TextField(
        verbose_name="Objeto da Doação", 
        null=True, 
        blank=True, 
        help_text="O robô ARGUS extrairá este texto automaticamente do PDF."
    )
    
    arquivo_pdf = models.FileField(upload_to='termos_doacao/', null=True, blank=True)
    dados_brutos = models.JSONField(null=True, blank=True) 
    data_importacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Termo de Doação"
        verbose_name_plural = "Termos de Doação"

    def __str__(self):
        return f"Termo {self.numero}/{self.ano} - {self.origem.sigla}"


class ItemPatrimonial(models.Model):
    """
    Itens vinculados a um termo, com rastreabilidade de processos e localização.
    """
    termo = models.ForeignKey(
        TermoDoacao, 
        on_delete=models.CASCADE, 
        related_name='itens_patrimoniais',
    )
    
    # Identificação Básica
    numero_ativo = models.CharField(max_length=50, verbose_name="Nº Patrimônio")
    descricao = models.TextField(verbose_name="Descrição do Bem")
    valor_bem = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Unitário", default=0.00)
    
    # Rastreabilidade de Processos
    processo_compra = models.ForeignKey(
        'cadastros.Processo', 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True, 
        related_name='itens_comprados',
        verbose_name="Processo de Compra"
    )

    processos_pagamento = models.ManyToManyField(
        'cadastros.Processo', 
        related_name='itens_pagos',
        verbose_name="Processos de Pagamento"
    )
    
    # Documentação Fiscal
    nota_fiscal = models.ForeignKey(
        'cadastros.NotaFiscal', # Referência via string para o módulo cadastros
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='itens_vinculados',
        verbose_name="Nota Fiscal"
    )
    
    # Localização Geográfica/Administrativa no IFAM
    localizacao = models.ForeignKey(
        'cadastros.Localizacao', 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True, 
        related_name='itens_alocados',
        verbose_name="Localização Destino"
    )

    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Item Patrimonial"
        verbose_name_plural = "Itens Patrimoniais"

    def __str__(self):
        return f"{self.numero_ativo} - {self.descricao[:30]}"
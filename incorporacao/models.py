"""
argus/incorporacao/models.py
"""

from django.db import models
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.core.exceptions import ValidationError
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

    conta_bancaria = models.ForeignKey(
        'cadastros.ContaBancaria',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='itens_patrimoniais',
        verbose_name="Conta Bancária de Débito"
    )

    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Item Patrimonial"
        verbose_name_plural = "Itens Patrimoniais"

    def clean(self):
        super().clean()

        if self.conta_bancaria and hasattr(self, 'termo') and self.termo and self.termo.projeto_id:
            if self.conta_bancaria.projeto_id != self.termo.projeto_id:
                raise ValidationError({
                    'conta_bancaria': "A conta bancária debitada deve pertencer ao mesmo projeto do Termo de Doação."
                })

        if self.conta_bancaria and self.conta_bancaria.fonte_recurso:
            if self.conta_bancaria.fonte_recurso.nome in ['EMBRAPII', 'SEBRAE']:
                raise ValidationError({
                    'conta_bancaria': "RN-06: Recursos de subvenção da EMBRAPII ou SEBRAE não podem ser utilizados para aquisição de Bens de Capital."
                })

        if self.processo_compra and self.processo_compra.conta_bancaria and self.processo_compra.conta_bancaria.fonte_recurso:
            if self.processo_compra.conta_bancaria.fonte_recurso.nome in ['EMBRAPII', 'SEBRAE']:
                raise ValidationError({
                    'processo_compra': "RN-06: O processo de compra está associado a uma conta EMBRAPII/SEBRAE, o que é vedado para bens patrimoniais."
                })

    def __str__(self):
        return f"{self.numero_ativo} - {self.descricao[:30]}"


@receiver(m2m_changed, sender=ItemPatrimonial.processos_pagamento.through)
def validar_processos_pagamento_item_patrimonial(sender, instance, action, reverse, pk_set, **kwargs):
    """
    RN-06: Impede a vinculação de processos custeados por contas EMBRAPII/SEBRAE a bens patrimoniais.
    Trata tanto a direção direta (item.processos_pagamento.add) quanto a reversa (processo.itens_pagos.add).
    """
    if action == 'pre_add':
        if not pk_set:
            return

        from cadastros.models import Processo

        if not reverse:
            processos_vedados = Processo.objects.filter(
                pk__in=pk_set,
                conta_bancaria__fonte_recurso__nome__in=['EMBRAPII', 'SEBRAE']
            )
            if processos_vedados.exists():
                raise ValidationError(
                    "RN-06: Vedação regulatória: não é permitido associar processos de pagamento "
                    "custeados por contas da EMBRAPII ou SEBRAE a bens de capital."
                )
        else:
            processo = instance
            if processo.conta_bancaria and processo.conta_bancaria.fonte_recurso:
                if processo.conta_bancaria.fonte_recurso.nome in ['EMBRAPII', 'SEBRAE']:
                    raise ValidationError(
                        "RN-06: Vedação regulatória: este processo está vinculado a uma conta "
                        "EMBRAPII/SEBRAE e não pode receber a vinculação de bens patrimoniais."
                    )
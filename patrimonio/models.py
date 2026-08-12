"""
argus/patrimonio/models.py
"""
from django.db import models

class VerificacaoTermo(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente (Novo)'),
        ('EM_CONFERENCIA', 'Em Conferência'),
        ('VALIDADO', 'Validado (Aguardando Aprovação)'),
        ('APROVADO', 'Aprovado (No Inventário)'),
    ]

    numero_termo = models.CharField(max_length=255, null=True, blank=True)
    termo_pdf = models.FileField(upload_to='termos_conferencia/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    
    # --- MEMÓRIA DO ESTÁGIO 1 (JSON) ---
    dados_brutos = models.JSONField(null=True, blank=True)
    
    # --- PARÂMETROS DE CONTROLE ---
    linhas_cabecalho = models.IntegerField(default=5)
    linha_atual = models.IntegerField(default=0)
    
    data_criacao = models.DateTimeField(auto_now_add=True)

    # --- MEMÓRIA DA IMPORTAÇÃO ---
    projeto_em_memoria = models.CharField(max_length=255, blank=True, null=True)
    conta_em_memoria = models.CharField(max_length=50, blank=True, null=True)
    dv_em_memoria = models.CharField(max_length=5, blank=True, null=True)
    documento_em_memoria = models.CharField(max_length=255, blank=True, null=True)
    situacao_em_memoria = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.numero_termo} - {self.status}"


class ItemVerificacao(models.Model):
    """Representa os 16 campos da FAEPI na Quarentena de Validação."""
    verificacao = models.ForeignKey(VerificacaoTermo, on_delete=models.CASCADE, related_name='itens')
    
    numero_ativo = models.CharField(max_length=50, default='pendente')
    descricao = models.TextField(default='pendente')
    processo_compra = models.CharField(max_length=100, default='pendente')
    processo_pagamento = models.CharField(max_length=100, default='pendente')
    cnpj_cpf_fornecedor = models.CharField(max_length=50, default='pendente')
    nome_fornecedor = models.CharField(max_length=255, default='pendente')
    nota_fiscal = models.CharField(max_length=100, default='pendente')
    data_nf = models.CharField(max_length=50, default='pendente')
    valor_bem = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    conta = models.CharField(max_length=50, default='pendente')
    dv = models.CharField(max_length=10, default='pendente')
    projeto = models.CharField(max_length=100, default='pendente')
    localizacao = models.CharField(max_length=255, default='pendente')
    situacao = models.CharField(max_length=100, default='pendente')
    data_movimentacao = models.CharField(max_length=50, default='pendente')
    documento = models.CharField(max_length=255, default='pendente')
    
    erro_leitura = models.BooleanField(default=False)
    validado_por_usuario = models.BooleanField(default=False)

    def __str__(self):
        return f"Item {self.numero_ativo} - {self.verificacao.numero_termo}"


class BemPatrimonial(models.Model):
    """O Inventário Real e Definitivo do Polo de Inovação."""
    patrimonio_ifam = models.CharField(max_length=50, unique=True, null=True, blank=True)
    patrimonio_doador = models.CharField(max_length=50, null=True, blank=True)
    descricao = models.TextField()
    valor = models.DecimalField(max_digits=15, decimal_places=2)
    
    # === A PONTE DEFINITIVA PARA O NÚCLEO DO SISTEMA ===
    projeto = models.ForeignKey('cadastros.ProjetoPDI', on_delete=models.SET_NULL, null=True, blank=True)
    termo_doacao = models.ForeignKey('incorporacao.TermoDoacao', on_delete=models.CASCADE, related_name='bens_patrimoniais', null=True, blank=True)
    ambiente = models.ForeignKey('central_servicos.Ambiente', on_delete=models.SET_NULL, null=True, blank=True, related_name='bens_patrimoniais', verbose_name="Ambiente (Localização)")
    # ===================================================
    
    nota_fiscal = models.CharField(max_length=100, null=True, blank=True)
    
    ESTADO_CHOICES = [('NOVO', 'Novo'), ('BOM', 'Bom'), ('OCIOSO', 'Ocioso'), ('RECUPERAVEL', 'Recuperável'), ('IRRECUPERAVEL', 'Irrecuperável')]
    estado_conservacao = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='NOVO')
    
    status_operacional = models.CharField(max_length=20, default='ATIVO')
    data_incorporacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patrimonio_ifam or self.patrimonio_doador} - {self.descricao[:50]}"


class FiltroImportacao(models.Model):
    termo = models.CharField(max_length=255, unique=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.termo
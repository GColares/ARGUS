"""
argus/gestao_projetos/models.py
"""

from django.db import models
from django.utils import timezone

class InstituicaoParceira(models.Model):
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome da Instituição")
    sigla = models.CharField(max_length=20, unique=True)
    cnpj = models.CharField(max_length=18, blank=True, null=True)

    class Meta:
        verbose_name = "Instituição Parceira"
        verbose_name_plural = "Instituições Parceiras"

    def __str__(self):
        return self.sigla

class Convenio(models.Model):
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

class ProjetoPDI(models.Model):
    convenio = models.ForeignKey(Convenio, on_delete=models.SET_NULL, null=True, blank=True, related_name='projetos')
    nome = models.CharField(max_length=200, unique=True, verbose_name="Nome do Projeto")
    status = models.CharField(max_length=20, choices=[('ATIVO', 'Ativo'), ('FINALIZADO', 'Finalizado')], default='ATIVO')

    class Meta:
        verbose_name = "Projeto PDI"
        verbose_name_plural = "Projetos PDI"

    def __str__(self):
        numero_conv = self.convenio.numero_convenio if self.convenio else "S/C"
        return f"Convênio {numero_conv} - Projeto {self.nome}"

class Pessoa(models.Model):
    nome = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14, unique=True, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.nome

class EquipeProjeto(models.Model):
    FUNCAO_CHOICES = [
        ('CPO', 'Coordenador de Projeto (CPO)'),
        ('GPA', 'Gestor de Programa (GPA)'),
        ('GPO', 'Gestor de Projeto (GPO)'),
        ('PEQ', 'Pesquisador (PEQ)'),
        ('EST', 'Estudante / Bolsista (EST)'),
        ('ADM', 'Apoio Administrativo (ADM)'),
        ('CLE', 'Colaborador Externo (CLE)'),
    ]

    TIPO_BOLSA_CHOICES = [
        ('BP', 'Bolsa de Parceria (BP)'),
        ('BI', 'Bolsa Institucional (BI)'),
        ('SB', 'Sem Bolsa / Contrapartida'),
    ]

    projeto = models.ForeignKey(ProjetoPDI, on_delete=models.CASCADE, related_name='membros_equipe')
    pessoa = models.ForeignKey(Pessoa, on_delete=models.CASCADE, related_name='vinculos')
    funcao = models.CharField(max_length=4, choices=FUNCAO_CHOICES)
    tipo_bolsa = models.CharField(max_length=2, choices=TIPO_BOLSA_CHOICES, default='BP')
    carga_horaria_semanal = models.PositiveIntegerField(default=20)
    data_inicio = models.DateField(default=timezone.now)
    data_fim = models.DateField(blank=True, null=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Membro da Equipe"
        verbose_name_plural = "Membros das Equipes"

    def __str__(self):
        return f"{self.pessoa.nome} - {self.get_funcao_display()}" # type: ignore
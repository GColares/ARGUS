import re

with open(r'c:\ARGUS\cadastros\models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Renomear TermoDeParceria para Convenio
content = content.replace("class TermoDeParceria(InstrumentoJuridicoBase):", "class Convenio(InstrumentoJuridicoBase):")
content = content.replace('verbose_name = "Termo de Parceria"', 'verbose_name = "Convênio"')
content = content.replace('verbose_name_plural = "Termos de Parceria"', 'verbose_name_plural = "Convênios"')
content = content.replace("related_name='termos_parceria'", "related_name='convenios'")

# Fix InstrumentoJuridicoBase abstract
content = content.replace("    class Meta:\n        abstract = True", '    class Meta:\n        verbose_name = "Instrumento Jurídico Base"\n        verbose_name_plural = "Instrumentos Jurídicos Base"')

# 2. Criar AcordoDeParceria
acordo_class = """
class AcordoDeParceria(InstrumentoJuridicoBase):
    \"\"\"Entidade macro jurídica para os novos acordos sob o Marco Legal de CT&I.\"\"\"
    projeto = models.ForeignKey('ProjetoPDI', on_delete=models.CASCADE, related_name='acordos_parceria', null=True, blank=True, verbose_name="Projeto Mestre")
    concedente = models.ForeignKey('PessoaJuridica', on_delete=models.CASCADE, related_name='acordos_concedidos', verbose_name="Concedente (Empresa/Agência)")
    convenente = models.ForeignKey('ICT', on_delete=models.PROTECT, related_name='convenente_em_acordo', verbose_name="Convenente")
    interveniente = models.ForeignKey(FundacaoApoio, on_delete=models.PROTECT, related_name='interveniente_em_acordo', verbose_name="Interveniente")

    class Meta:
        verbose_name = "Acordo de Parceria"
        verbose_name_plural = "Acordos de Parceria"
        constraints = [
            models.UniqueConstraint(
                fields=['tipo_instrumento', 'sequencial', 'ano'],
                condition=models.Q(sequencial__isnull=False, ano__isnull=False),
                name='unique_seq_ano_acordo_parceria'
            )
        ]

    def __str__(self):
        return f"{self.numero or 'Sem Número'} ({self.concedente.sigla or self.concedente.nome_fantasia or self.concedente.nome})"

    @property
    def nome_especie(self):
        return self.tipo_instrumento_fk.nome if self.tipo_instrumento_fk else 'Acordo de Parceria'

    @property
    def nome_especie_plural(self):
        return self.tipo_instrumento_fk.nome if self.tipo_instrumento_fk else 'Acordos de Parceria'

    @property
    def sigla_especie(self):
        return self.tipo_instrumento_fk.sigla if self.tipo_instrumento_fk else 'AP'
"""

content = re.sub(r'(class TermoCooperacao\(models\.Model\):)', lambda m: acordo_class + '\n' + m.group(1), content, count=1, flags=re.DOTALL)

# 3. Refatorar TermoCooperacao
content = content.replace("class TermoCooperacao(models.Model):", "class TermoCooperacao(InstrumentoJuridicoBase):")
content = re.sub(r'    numero = models\.CharField.*?\n', '', content, count=1)
content = re.sub(r'    tipo_instrumento_fk = models\.ForeignKey\([\s\S]*?verbose_name="Tipo de Instrumento \(Parametrizado\)"\n    \)\n', '', content)
content = re.sub(r'    objeto = models\.TextField.*?\n', '', content, count=1)
content = re.sub(r'    data_assinatura = models\.DateField.*?\n', '', content, count=1)
content = re.sub(r'    vigencia_inicio = models\.DateField.*?\n', '', content, count=1)
content = re.sub(r'    vigencia_fim = models\.DateField.*?\n', '', content, count=1)
content = re.sub(r'    ativo = models\.BooleanField.*?\n', '', content, count=1)

# 4. Refatorar TermoAditivo e AditivoTermoCooperacao
# Replace entire classes by splitting on known boundaries, safely!
# AditivoTermoCooperacao ends before `class Programa`
content = re.sub(r'class AditivoTermoCooperacao\(models\.Model\):[\s\S]*?class Programa', 'class Programa', content)
# TermoAditivo is at line 981, ends before class AditivoProjeto? No, let's just replace it where it is.
content = re.sub(r'class TermoAditivo\(models\.Model\):[\s\S]*?(?=class )', '', content, count=1)

new_aditivos = """
class TermoAditivo(models.Model):
    \"\"\"Termo Aditivo unificado para todos os Instrumentos Jurídicos.\"\"\"
    instrumento = models.ForeignKey(InstrumentoJuridicoBase, on_delete=models.CASCADE, related_name='aditivos')
    numero = models.CharField(max_length=50, verbose_name="Número do Aditivo")
    data_assinatura = models.DateField(verbose_name="Data de Assinatura")
    nova_data_fim = models.DateField(blank=True, null=True, verbose_name="Nova Data Fim (Prorrogação)")
    valor_acrescimo = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Valor Acrescido (R$)")
    objeto = models.TextField(verbose_name="Objeto / Justificativa")
    arquivo_pdf = models.FileField(upload_to='aditivos/', blank=True, null=True)

    class Meta:
        verbose_name = "Termo Aditivo"
        verbose_name_plural = "Termos Aditivos"

    def __str__(self):
        return f"Aditivo {self.numero} - {self.instrumento.numero}"

class TermoEncerramento(models.Model):
    \"\"\"Termo de Encerramento unificado para todos os Instrumentos Jurídicos.\"\"\"
    instrumento = models.OneToOneField(InstrumentoJuridicoBase, on_delete=models.CASCADE, related_name='encerramento')
    data_encerramento = models.DateField(verbose_name="Data do Encerramento")
    motivo_rescisao = models.TextField(verbose_name="Motivo / Justificativa")
    oficio_comunicacao = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nº do Ofício")
    arquivo_pdf = models.FileField(upload_to='encerramentos/', blank=True, null=True)

    class Meta:
        verbose_name = "Termo de Encerramento"
        verbose_name_plural = "Termos de Encerramento"

    def __str__(self):
        return f"Encerramento - {self.instrumento.numero}"

"""
# Append new aditivos just before Programa
content = content.replace("class Programa(models.Model):", new_aditivos + "class Programa(models.Model):")

# Properties for ProjetoPDI
content = content.replace("def termo_parceria(self):", "def convenio(self):")
content = content.replace("return self.termos_parceria.first()", "return self.convenios.first()")

prop_acordo = """
    @property
    def acordo_parceria(self):
        \"\"\"Retorna o primeiro acordo de parceria associado.\"\"\"
        return self.acordos_parceria.first()

    @property
    def instrumento_vinculado(self):
        \"\"\"Retorna o acordo de parceria ou convênio principal vinculado a este projeto.\"\"\"
        return self.acordo_parceria or self.convenio
"""
content = re.sub(r'    @property\n    def convenio\(self\):.*?return self\.convenios\.first\(\)', lambda m: m.group(0) + '\n' + prop_acordo, content, flags=re.DOTALL)

# Also fix the PlanoDeTrabalho homologador constraint
content = content.replace("termo_homologador = models.ForeignKey(TermoDeParceria,", "termo_homologador = models.ForeignKey('InstrumentoJuridicoBase',")

with open(r'c:\ARGUS\cadastros\models.py', 'w', encoding='utf-8') as f:
    f.write(content)

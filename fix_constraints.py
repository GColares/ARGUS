import re

with open(r'c:\ARGUS\cadastros\models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove constraints from Convenio
content = re.sub(r'        constraints = \[\s*models\.UniqueConstraint\(\s*fields=\['\''tipo_instrumento'\'', '\''sequencial'\'', '\''ano'\''\],\s*condition=models\.Q\(sequencial__isnull=False, ano__isnull=False\),\s*name='\''unique_sequencial_ano_por_tipo'\''\s*\)\s*\]', '', content)

# Remove constraints from AcordoDeParceria
content = re.sub(r'        constraints = \[\s*models\.UniqueConstraint\(\s*fields=\['\''tipo_instrumento'\'', '\''sequencial'\'', '\''ano'\''\],\s*condition=models\.Q\(sequencial__isnull=False, ano__isnull=False\),\s*name='\''unique_seq_ano_acordo_parceria'\''\s*\)\s*\]', '', content)

# Add constraint to InstrumentoJuridicoBase
base_meta = """    class Meta:
        verbose_name = "Instrumento Jurídico Base"
        verbose_name_plural = "Instrumentos Jurídicos Base"
        constraints = [
            models.UniqueConstraint(
                fields=['tipo_instrumento', 'sequencial', 'ano'],
                condition=models.Q(sequencial__isnull=False, ano__isnull=False),
                name='unique_seq_ano_por_tipo'
            )
        ]"""

content = re.sub(r'    class Meta:\n        verbose_name = "Instrumento Jurídico Base"\n        verbose_name_plural = "Instrumentos Jurídicos Base"', base_meta, content)

with open(r'c:\ARGUS\cadastros\models.py', 'w', encoding='utf-8') as f:
    f.write(content)

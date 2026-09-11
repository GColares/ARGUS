import re

with open(r'c:\ARGUS\cadastros\admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_aditivo = """
@admin.register(TermoAditivo)
class TermoAditivoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'instrumento', 'data_assinatura', 'nova_data_fim', 'valor_acrescimo')
    list_filter = ('instrumento',)
    search_fields = ('numero', 'instrumento__numero')

@admin.register(TermoEncerramento)
class TermoEncerramentoAdmin(admin.ModelAdmin):
    list_display = ('instrumento', 'data_encerramento', 'oficio_comunicacao')
"""

content = re.sub(r'@admin\.register\(TermoAditivo\)[\s\S]*', new_aditivo, content)

with open(r'c:\ARGUS\cadastros\admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

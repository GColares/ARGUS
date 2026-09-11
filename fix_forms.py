import re

with open(r'c:\ARGUS\cadastros\forms.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_aditivo = """
class TermoAditivoForm(forms.ModelForm):
    class Meta:
        model = TermoAditivo
        fields = ['instrumento', 'numero', 'data_assinatura', 'nova_data_fim', 'valor_acrescimo', 'objeto', 'arquivo_pdf']
        widgets = {
            'data_assinatura': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'nova_data_fim': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }

class TermoEncerramentoForm(forms.ModelForm):
    class Meta:
        model = TermoEncerramento
        fields = ['instrumento', 'data_encerramento', 'motivo_rescisao', 'oficio_comunicacao', 'arquivo_pdf']
        widgets = {
            'data_encerramento': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }

class ProjetoPDIForm"""

content = re.sub(r'class TermoAditivoForm[\s\S]*?class ProjetoPDIForm', new_aditivo, content)

with open(r'c:\ARGUS\cadastros\forms.py', 'w', encoding='utf-8') as f:
    f.write(content)

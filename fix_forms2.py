import re

with open(r'c:\ARGUS\cadastros\forms.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_aditivo = """
class TermoAditivoForm(forms.ModelForm):
    class Meta:
        model = TermoAditivo
        fields = ['instrumento', 'numero', 'data_assinatura', 'nova_data_fim', 'valor_acrescimo', 'objeto', 'arquivo_pdf']
        widgets = {
            'data_assinatura': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'nova_data_fim': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
        }

class TermoEncerramentoForm(forms.ModelForm):
    class Meta:
        model = TermoEncerramento
        fields = ['instrumento', 'data_encerramento', 'motivo_rescisao', 'oficio_comunicacao', 'arquivo_pdf']
        widgets = {
            'data_encerramento': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
        }
"""

content = re.sub(r'class TermoAditivoForm.*?class PlanoDeTrabalhoForm', new_aditivo + "\nclass PlanoDeTrabalhoForm", content, flags=re.DOTALL)

with open(r'c:\ARGUS\cadastros\forms.py', 'w', encoding='utf-8') as f:
    f.write(content)

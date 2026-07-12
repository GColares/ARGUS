from django import forms
from .models import TermoDoacao
from cadastros.forms import higienizar_texto_pdf # Importamos o faxineiro lá dos cadastros!

class TermoDoacaoForm(forms.ModelForm):
    class Meta:
        model = TermoDoacao
        fields = ['projeto', 'origem', 'numero', 'ano', 'objeto', 'arquivo_pdf']
        
        widgets = {
            'projeto': forms.Select(attrs={'class': 'form-select form-select-lg fw-bold text-primary'}),
            'origem': forms.Select(attrs={'class': 'form-select'}),
            'numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 005'}),
            'ano': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 2024'}),
            'objeto': forms.Textarea(attrs={
                'class': 'form-control text-muted bg-light', 
                'rows': 3, 
                'placeholder': 'Deixe em branco. A Inteligência Artificial lerá o PDF e preencherá este campo automaticamente.'
            }),
            'arquivo_pdf': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['projeto'].empty_label = "--- Selecione o Projeto ---"
        self.fields['origem'].empty_label = "--- Selecione a Origem ---"

    def clean_objeto(self):
        # Limpa todas as quebras de linha e lixo invisível do PDF
        return higienizar_texto_pdf(self.cleaned_data.get('objeto'))
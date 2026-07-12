# pyrefly: ignore [missing-import]
from django import forms
from .models import NotaFiscalAlmoxarifado
# pyrefly: ignore [missing-import]
from django.core.exceptions import ValidationError

class TermoRecebimentoForm(forms.ModelForm):
    class Meta:
        model = NotaFiscalAlmoxarifado
        fields = ['data_recebimento', 'usuario_recebedor', 'projeto_vinculado', 'chave_acesso']
        widgets = {
            'data_recebimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'usuario_recebedor': forms.Select(attrs={'class': 'form-select'}),
            'projeto_vinculado': forms.Select(attrs={'class': 'form-select'}),
            'chave_acesso': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Chave da Sefaz'}),
        }

    def clean_data_recebimento(self):
        data_recebimento = self.cleaned_data.get('data_recebimento')
        data_emissao = self.instance.data_emissao
        
        if data_recebimento and data_emissao:
            if data_recebimento < data_emissao:
                raise ValidationError("A data de recebimento não pode ser anterior à data de emissão da Nota Fiscal.")
        return data_recebimento

class UploadTermoAssinadoForm(forms.ModelForm):
    class Meta:
        model = NotaFiscalAlmoxarifado
        fields = ['termo_recebimento_assinado']

    def clean_termo_recebimento_assinado(self):
        arquivo = self.cleaned_data.get('termo_recebimento_assinado')
        if arquivo:
            if not arquivo.name.lower().endswith('.pdf'):
                raise ValidationError("O termo assinado deve ser um arquivo PDF.")
        return arquivo

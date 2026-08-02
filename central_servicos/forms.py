from django import forms
from .models import OrdemServico

class OrdemServicoForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = ['categoria', 'prioridade', 'sala', 'ativo_predial', 'descricao_problema']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'prioridade': forms.Select(attrs={'class': 'form-select'}),
            'sala': forms.Select(attrs={'class': 'form-select'}),
            'ativo_predial': forms.Select(attrs={'class': 'form-select'}),
            'descricao_problema': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descreva detalhadamente a sua solicitação...'}),
        }

class OrdemServicoCancelamentoForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = ['motivo_cancelamento']
        widgets = {
            'motivo_cancelamento': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Informe o motivo detalhado do cancelamento...'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['motivo_cancelamento'].required = True

from django import forms
from cadastros.models import AtividadePlanoAcao

class AtividadePlanoAcaoForm(forms.ModelForm):
    class Meta:
        model = AtividadePlanoAcao
        # Excluímos 'projeto' pois será injetado no back-end, e omitimos as datas reais (properties)
        fields = ['numero', 'nome', 'descricao', 'justificativa', 'entregaveis', 'mes_inicio_relativo', 'mes_fim_relativo']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'justificativa': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'entregaveis': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'mes_inicio_relativo': forms.NumberInput(attrs={'class': 'form-control'}),
            'mes_fim_relativo': forms.NumberInput(attrs={'class': 'form-control'}),
        }
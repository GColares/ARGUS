from django import forms
from cadastros.models import AtividadePlanoAcao

class AtividadePlanoAcaoForm(forms.ModelForm):
    class Meta:
        model = AtividadePlanoAcao
        # Excluímos 'plano_trabalho' pois será injetado no back-end
        fields = ['nome', 'descricao', 'justificativa', 'mes_inicio', 'mes_fim']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3, 'class': 'form-control richtext'}),
            'justificativa': forms.Textarea(attrs={'rows': 2, 'class': 'form-control richtext'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'mes_inicio': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'mes_fim': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }
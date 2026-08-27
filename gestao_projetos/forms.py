from django import forms
from cadastros.models import AtividadePlanoAcao

class AtividadePlanoAcaoForm(forms.ModelForm):
    class Meta:
        model = AtividadePlanoAcao
        # Excluímos 'plano_trabalho' pois será injetado no back-end
        fields = ['numero', 'nome', 'descricao', 'justificativa', 'data_inicio', 'data_fim']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3, 'class': 'form-control richtext'}),
            'justificativa': forms.Textarea(attrs={'rows': 2, 'class': 'form-control richtext'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'data_inicio': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'data_fim': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
        }
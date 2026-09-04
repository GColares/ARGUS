from django import forms
from cadastros.models import AtividadePlanoAcao
from .models import TemplateDocumentoConveniar


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


class TemplateDocumentoConveniarForm(forms.ModelForm):
    """Formulário de upload e manutenção de matrizes DOCX do Conveniar."""
    class Meta:
        model = TemplateDocumentoConveniar
        fields = ['nome', 'tipo', 'descricao', 'arquivo_docx', 'versao', 'ativo', 'tags_disponiveis']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'arquivo_docx': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.docx'}),
            'versao': forms.TextInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tags_disponiveis': forms.Textarea(attrs={
                'rows': 4, 'class': 'form-control font-monospace',
                'placeholder': '{{ bolsista_nome }}\n{{ valor }}\n{{ competencia }}'
            }),
        }
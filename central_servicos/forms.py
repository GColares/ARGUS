# pyrefly: ignore [untyped-import]
from django import forms
from .models import OrdemServico, Predio, Ambiente

class OrdemServicoForm(forms.ModelForm):
    ambientes = forms.ModelMultipleChoiceField(
        queryset=Ambiente.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'd-none real-checkboxes'}),
        label="Salas / Ambientes",
        help_text="Selecione os ambientes onde a manutenção será realizada."
    )

    class Meta:
        model = OrdemServico
        fields = ['categoria', 'ambientes', 'ativo_predial', 'descricao_problema']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-select'}),
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

BOOL_CHOICES = [(True, 'Sim'), (False, 'Não'), ('', 'Não Informado')]

class PredioForm(forms.ModelForm):
    class Meta:
        model = Predio
        exclude = ['ordem']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do prédio'}),
            'sigla': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: P1, BIO, etc.'}),
            'finalidades': forms.CheckboxSelectMultiple(attrs={'class': 'btn-check'}),
            'area_total_m2': forms.NumberInput(attrs={'class': 'form-control'}),
            'capacidade_pessoas': forms.NumberInput(attrs={'class': 'form-control'}),
            
            'possui_geracao_solar': forms.RadioSelect(choices=BOOL_CHOICES, attrs={'class': 'form-check-input'}),
            'capacidade_geracao_solar_kwp': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantidade_placas_solares': forms.NumberInput(attrs={'class': 'form-control'}),
            
            'possui_gerador_emergencia': forms.RadioSelect(choices=BOOL_CHOICES, attrs={'class': 'form-check-input'}),
            'possui_subestacao_propria': forms.RadioSelect(choices=BOOL_CHOICES, attrs={'class': 'form-check-input'}),
            'possui_climatizacao_central': forms.RadioSelect(choices=BOOL_CHOICES, attrs={'class': 'form-check-input'}),
            'possui_rede_gases_especiais': forms.RadioSelect(choices=BOOL_CHOICES, attrs={'class': 'form-check-input'}),
            'possui_sala_limpa': forms.RadioSelect(choices=BOOL_CHOICES, attrs={'class': 'form-check-input'}),
            
            'risco_quimico': forms.Select(attrs={'class': 'form-select'}),
            'risco_biologico': forms.Select(attrs={'class': 'form-select'}),
            'armazena_inflamaveis': forms.RadioSelect(choices=BOOL_CHOICES, attrs={'class': 'form-check-input'}),
            'possui_ete_sanitaria': forms.RadioSelect(choices=BOOL_CHOICES, attrs={'class': 'form-check-input'}),
            'possui_ete_especial': forms.RadioSelect(choices=BOOL_CHOICES, attrs={'class': 'form-check-input'}),
            
            'avcb_numero': forms.TextInput(attrs={'class': 'form-control'}),
            'avcb_validade': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'avcb_arquivo': forms.FileInput(attrs={'class': 'form-control'}),
            
            'licenca_ambiental_numero': forms.TextInput(attrs={'class': 'form-control'}),
            'licenca_ambiental_validade': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'licenca_ambiental_arquivo': forms.FileInput(attrs={'class': 'form-control'}),
            
            'licenca_vigilancia_sanitaria_numero': forms.TextInput(attrs={'class': 'form-control'}),
            'licenca_vigilancia_sanitaria_validade': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'licenca_vigilancia_sanitaria_arquivo': forms.FileInput(attrs={'class': 'form-control'}),
            
            'brigada_incendio_ativa': forms.RadioSelect(choices=BOOL_CHOICES, attrs={'class': 'form-check-input'}),
        }

from .models import Andar, Ambiente, TipoAmbiente, CategoriaElemento, TipoElemento, ElementoConstrutivo, TipoAtivo, AtivoPredial, CategoriaServico, Finalidade

class AndarForm(forms.ModelForm):
    class Meta:
        model = Andar
        exclude = ['ordem']
        widgets = {
            'predio': forms.Select(attrs={'class': 'form-select'}),
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do Andar'}),
        }

class AmbienteForm(forms.ModelForm):
    class Meta:
        model = Ambiente
        exclude = ['ordem']
        widgets = {
            'predio': forms.Select(attrs={'class': 'form-select'}),
            'andar': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'localizacao': forms.Select(attrs={'class': 'form-select'}),
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do Ambiente'}),
        }

class AtivoPredialForm(forms.ModelForm):
    class Meta:
        model = AtivoPredial
        fields = '__all__'
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'ambiente': forms.Select(attrs={'class': 'form-select'}),
            'nome_apelido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome/Apelido do Ativo'}),
            'numero_serie': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de Série'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'patrimonio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nº Patrimônio'}),
        }

class AtivoPredialLoteForm(forms.ModelForm):
    ambientes = forms.ModelMultipleChoiceField(
        queryset=Ambiente.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'd-none real-checkboxes'}),
        label="Salas / Ambientes",
        help_text="Selecione um ou mais ambientes onde este ativo será criado."
    )

    class Meta:
        model = AtivoPredial
        fields = ['ambientes', 'tipo', 'nome_apelido', 'descricao']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'nome_apelido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Ar da Janela (Opcional)'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class CategoriaServicoForm(forms.ModelForm):
    class Meta:
        model = CategoriaServico
        fields = '__all__'
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da Categoria'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class FinalidadeForm(forms.ModelForm):
    class Meta:
        model = Finalidade
        fields = '__all__'
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da Finalidade'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class TipoAtivoForm(forms.ModelForm):
    class Meta:
        model = TipoAtivo
        fields = '__all__'
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Ar Condicionado, Porta, Extintor'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class TipoAmbienteForm(forms.ModelForm):
    class Meta:
        model = TipoAmbiente
        fields = '__all__'
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class CategoriaElementoForm(forms.ModelForm):
    class Meta:
        model = CategoriaElemento
        fields = '__all__'
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class TipoElementoForm(forms.ModelForm):
    class Meta:
        model = TipoElemento
        fields = '__all__'
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ElementoConstrutivoForm(forms.ModelForm):
    class Meta:
        model = ElementoConstrutivo
        fields = '__all__'
        widgets = {
            'ambiente': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'area_m2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'detalhes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

import re
from django import forms
from .models import ProjetoPDI, ContaBancaria, Processo, TipoProcesso, TermoBolsa, Bolsista, Fornecedor, FonteDeRecurso

# ==============================================================================
# MOTOR DE LIMPEZA GERAL
# ==============================================================================
def higienizar_texto_pdf(texto):
    """
    Função implacável contra lixo de PDF.
    Remove caracteres invisíveis e padroniza os espaços.
    """
    if not texto:
        return texto
        
    texto = str(texto)
    # 1. Remove caracteres invisíveis (Zero-width spaces e formatações ocultas)
    texto = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', texto)
    
    # 2. Substitui non-breaking spaces (espaços falsos do HTML/PDF) por espaços reais
    texto = texto.replace('\xa0', ' ')
    
    # 3. Substitui quebras de linha (\n), tabs (\t) e múltiplos espaços por um ÚNICO espaço
    texto = re.sub(r'\s+', ' ', texto)
    
    # 4. Remove espaços nas pontas e devolve limpo
    return texto.strip()


# ==============================================================================
# FORMULÁRIOS
# ==============================================================================
class ProjetoPDIForm(forms.ModelForm):
    class Meta:
        model = ProjetoPDI
        fields = ['convenio', 'nome', 'interveniente', 'financiadores', 'vigencia_inicio', 'vigencia_fim']
        
        widgets = {
            'convenio': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Ex: IFAM 2022-010', 'autofocus': True}),
            'nome': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Nome Oficial do Projeto'}),
            'interveniente': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'financiadores': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Empresas separadas por vírgula'}),
            'vigencia_inicio': forms.DateInput(attrs={'class': 'form-control form-control-lg', 'type': 'date'}),
            'vigencia_fim': forms.DateInput(attrs={'class': 'form-control form-control-lg', 'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        for campo, valor in cleaned_data.items():
            if isinstance(valor, str):
                cleaned_data[campo] = higienizar_texto_pdf(valor)
                
        convenio = cleaned_data.get('convenio')
        if convenio and len(convenio) < 3:
            self.add_error('convenio', 'O número do convênio está muito curto ou inválido após a limpeza.')

        return cleaned_data


class FonteDeRecursoForm(forms.ModelForm):
    class Meta:
        model = FonteDeRecurso
        fields = ['nome', 'descricao']
        
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: EMBRAPII, SEBRAE'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detalhes opcionais sobre a fonte'}),
        }

class ContaBancariaForm(forms.ModelForm):
    class Meta:
        model = ContaBancaria
        fields = ['fonte_recurso', 'banco', 'agencia', 'conta', 'dv']
        
        widgets = {
            'fonte_recurso': forms.Select(attrs={'class': 'form-select fw-bold text-primary'}),
            'banco': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Banco do Brasil'}),
            'agencia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1234-5'}),
            'conta': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apenas números'}),
            'dv': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '5', 'placeholder': 'Dígito'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fonte_recurso'].empty_label = "--- Selecione a Fonte ---"
        self.fields['fonte_recurso'].queryset = FonteDeRecurso.objects.all().order_by('nome')
        
    def clean(self):
        cleaned_data = super().clean()
        for campo, valor in cleaned_data.items():
            if isinstance(valor, str):
                cleaned_data[campo] = higienizar_texto_pdf(valor) # Usando o motor de limpeza aqui também!
        return cleaned_data


class ProcessoForm(forms.ModelForm):
    class Meta:
        model = Processo
        fields = ['projeto', 'tipo', 'numero', 'origem', 'descricao']
        
        widgets = {
            'projeto': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select fw-bold text-primary'}),
            'numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 23208.000123/2024-10'}),
            'origem': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional (Ex: Equipamentos de TI)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 1. Força a ordem alfabética no banco de dados especificamente para este campo
        self.fields['tipo'].queryset = TipoProcesso.objects.all().order_by('nome')
        
        # 2. BÔNUS DE UX: Cria uma opção vazia no topo para obrigar o usuário a clicar e escolher
        self.fields['tipo'].empty_label = "--- Selecione o Tipo ---"

    def clean_numero(self):
        numero = self.cleaned_data.get('numero')
        return higienizar_texto_pdf(numero)

    def clean_descricao(self):
        descricao = self.cleaned_data.get('descricao')
        return higienizar_texto_pdf(descricao)
class TermoBolsaForm(forms.ModelForm):
    class Meta:
        model = TermoBolsa
        fields = [
            'cota_pt', 'bolsista', 'modalidade_bolsa', 'numero_termo',
            'vigencia_inicio', 'vigencia_fim', 'quantidade_parcelas', 'carga_horaria_total',
            'valor_parcela', 'status'
        ]
        widgets = {
            'cota_pt': forms.Select(attrs={'class': 'form-select'}),
            'bolsista': forms.Select(attrs={'class': 'form-select'}),
            'modalidade_bolsa': forms.Select(attrs={'class': 'form-select'}),
            'numero_termo': forms.TextInput(attrs={'class': 'form-control'}),
            'vigencia_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'vigencia_fim': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'quantidade_parcelas': forms.NumberInput(attrs={'class': 'form-control'}),
            'carga_horaria_total': forms.NumberInput(attrs={'class': 'form-control'}),
            'valor_parcela': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select fw-bold'}),
        }

class BolsistaForm(forms.ModelForm):
    class Meta:
        model = Bolsista
        fields = [
            'nome', 'cpf', 'rg', 'orgao_emissor_rg', 'data_nascimento',
            'nacionalidade', 'estado_civil', 'endereco', 'cep',
            'telefone', 'email', 'siape'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
            'rg': forms.TextInput(attrs={'class': 'form-control'}),
            'orgao_emissor_rg': forms.TextInput(attrs={'class': 'form-control'}),
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'nacionalidade': forms.TextInput(attrs={'class': 'form-control'}),
            'estado_civil': forms.Select(attrs={'class': 'form-select'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'cep': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-000'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'siape': forms.TextInput(attrs={'class': 'form-control'}),
        }

class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = ['nome', 'cnpj', 'sigla', 'endereco', 'email']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00.000.000/0000-00'}),
            'sigla': forms.TextInput(attrs={'class': 'form-control'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

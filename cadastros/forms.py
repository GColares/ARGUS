import re
from django import forms
from .models import ProjetoPDI, ContaBancaria, Processo, TipoProcesso

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
        fields = ['convenio', 'nome', 'interveniente', 'financiadores']
        
        widgets = {
            'convenio': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Ex: IFAM 2022-010', 'autofocus': True}),
            'nome': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Nome Oficial do Projeto'}),
            'interveniente': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'financiadores': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Empresas separadas por vírgula'}),
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


class ContaBancariaForm(forms.ModelForm):
    class Meta:
        model = ContaBancaria
        fields = ['banco', 'agencia', 'conta', 'dv']
        
        widgets = {
            'banco': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Banco do Brasil'}),
            'agencia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1234-5'}),
            'conta': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apenas números'}),
            'dv': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '5', 'placeholder': 'Dígito'}),
        }
        
    def clean(self):
        cleaned_data = super().clean()
        for campo, valor in cleaned_data.items():
            if isinstance(valor, str):
                cleaned_data[campo] = higienizar_texto_pdf(valor) # Usando o motor de limpeza aqui também!
        return cleaned_data


class ProcessoForm(forms.ModelForm):
    class Meta:
        model = Processo
        fields = ['tipo', 'numero', 'descricao']
        
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select fw-bold text-primary'}),
            'numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 23208.000123/2024-10'}),
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
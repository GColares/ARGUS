import re
from django import forms
from .models import ProjetoPDI, ContaBancaria, Processo, TipoProcesso, TermoBolsa, Fornecedor, FonteDeRecurso, TermoDeParceria, PlanoDeTrabalho, ICT, EmpresaParceira, FundacaoApoio, AgenciaFomento

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
        fields = ['nome', 'vigencia_inicio', 'vigencia_fim', 'vigencia_meses']
        
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Nome Oficial do Projeto', 'autofocus': True}),
            'vigencia_inicio': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control form-control-lg', 'type': 'date'}),
            'vigencia_fim': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control form-control-lg', 'type': 'date'}),
            'vigencia_meses': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'min': '1'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        assert cleaned_data is not None
        for campo, valor in cleaned_data.items():
            if isinstance(valor, str):
                cleaned_data[campo] = higienizar_texto_pdf(valor) # type: ignore
                
        return cleaned_data


class TermoDeParceriaForm(forms.ModelForm):
    class Meta:
        model = TermoDeParceria
        fields = ['numero', 'objeto', 'concedente', 'convenente', 'interveniente', 'data_assinatura']
        widgets = {
            'numero': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Ex: 0001/2026'}),
            'objeto': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Objeto do Termo de Parceria...'}),
            'concedente': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'convenente': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'interveniente': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'data_assinatura': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control form-control-lg', 'type': 'date'}),
        }


class PlanoDeTrabalhoForm(forms.ModelForm):
    class Meta:
        model = PlanoDeTrabalho
        fields = [
            'data_inicio', 'data_fim', 'total_meses', 'arquivo_pdf',
            'aporte_empresa', 'aporte_embrapii', 'aporte_sebrae', 'aporte_contrapartida',
            'abordagem_tecnica', 'abordagem_financeira', 'produto_entregue'
        ]
        widgets = {
            'data_inicio': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'data_fim': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'total_meses': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'arquivo_pdf': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'aporte_empresa': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'aporte_embrapii': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'aporte_sebrae': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'aporte_contrapartida': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'abordagem_tecnica': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descreva a abordagem técnica...'}),
            'abordagem_financeira': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descreva a abordagem financeira...'}),
            'produto_entregue': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descreva o produto esperado/entregue...'}),
        }


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
        self.fields['fonte_recurso'].empty_label = "--- Selecione a Fonte ---" # pyright: ignore
        self.fields['fonte_recurso'].queryset = FonteDeRecurso.objects.all().order_by('nome') # type: ignore
        
    def clean(self):
        cleaned_data = super().clean()
        assert cleaned_data is not None
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
        self.fields['tipo'].queryset = TipoProcesso.objects.all().order_by('nome') # type: ignore
        
        # 2. BÔNUS DE UX: Cria uma opção vazia no topo para obrigar o usuário a clicar e escolher
        self.fields['tipo'].empty_label = "--- Selecione o Tipo ---" # type: ignore

    def clean_numero(self):
        numero = self.cleaned_data.get('numero')
        return higienizar_texto_pdf(numero)

    def clean_descricao(self):
        descricao = self.cleaned_data.get('descricao')
        return higienizar_texto_pdf(descricao)
class TermoBolsaForm(forms.ModelForm):
    class Meta:
        model = TermoBolsa
        fields = ['cota_pt', 'pessoa', 'modalidade_bolsa', 'carga_horaria_total', 'numero_termo', 'vigencia_inicio', 'vigencia_fim', 'quantidade_parcelas', 'valor_parcela', 'status']
        widgets = {
            'cota_pt': forms.Select(attrs={'class': 'form-select'}),
            'pessoa': forms.Select(attrs={'class': 'form-select'}),
            'modalidade_bolsa': forms.Select(attrs={'class': 'form-select'}),
            'numero_termo': forms.TextInput(attrs={'class': 'form-control'}),
            'vigencia_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'vigencia_fim': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'quantidade_parcelas': forms.NumberInput(attrs={'class': 'form-control'}),
            'carga_horaria_total': forms.NumberInput(attrs={'class': 'form-control'}),
            'valor_parcela': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select fw-bold'}),
        }


class ICTForm(forms.ModelForm):
    class Meta:
        model = ICT
        fields = ['nome', 'cnpj', 'natureza_juridica', 'endereco', 'representante_legal', 'cargo_representante', 'sigla', 'campus_unidade', 'nome_nit']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00.000.000/0000-00'}),
            'natureza_juridica': forms.TextInput(attrs={'class': 'form-control', 'value': 'Pública'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'representante_legal': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo_representante': forms.TextInput(attrs={'class': 'form-control'}),
            'sigla': forms.TextInput(attrs={'class': 'form-control'}),
            'campus_unidade': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_nit': forms.TextInput(attrs={'class': 'form-control'}),
        }

class EmpresaParceiraForm(forms.ModelForm):
    class Meta:
        model = EmpresaParceira
        fields = ['nome', 'cnpj', 'natureza_juridica', 'endereco', 'representante_legal', 'cargo_representante', 'porte', 'segmento_atuacao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00.000.000/0000-00'}),
            'natureza_juridica': forms.TextInput(attrs={'class': 'form-control', 'value': 'Privada'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'representante_legal': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo_representante': forms.TextInput(attrs={'class': 'form-control'}),
            'porte': forms.Select(attrs={'class': 'form-select'}),
            'segmento_atuacao': forms.TextInput(attrs={'class': 'form-control'}),
        }

class FundacaoApoioForm(forms.ModelForm):
    class Meta:
        model = FundacaoApoio
        fields = ['nome', 'cnpj', 'natureza_juridica', 'endereco', 'representante_legal', 'cargo_representante', 'registro_mec', 'validade_credenciamento']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00.000.000/0000-00'}),
            'natureza_juridica': forms.TextInput(attrs={'class': 'form-control', 'value': 'Privada sem fins lucrativos'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'representante_legal': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo_representante': forms.TextInput(attrs={'class': 'form-control'}),
            'registro_mec': forms.TextInput(attrs={'class': 'form-control'}),
            'validade_credenciamento': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
        }

class AgenciaFomentoForm(forms.ModelForm):
    class Meta:
        model = AgenciaFomento
        fields = ['nome', 'cnpj', 'natureza_juridica', 'endereco', 'representante_legal', 'cargo_representante', 'esfera', 'sigla']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00.000.000/0000-00'}),
            'natureza_juridica': forms.TextInput(attrs={'class': 'form-control'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'representante_legal': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo_representante': forms.TextInput(attrs={'class': 'form-control'}),
            'esfera': forms.Select(attrs={'class': 'form-select'}),
            'sigla': forms.TextInput(attrs={'class': 'form-control'}),
        }

class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = ['nome', 'cnpj', 'natureza_juridica', 'endereco', 'representante_legal', 'cargo_representante', 'sigla', 'email']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00.000.000/0000-00'}),
            'natureza_juridica': forms.TextInput(attrs={'class': 'form-control', 'value': 'Privada'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'representante_legal': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo_representante': forms.TextInput(attrs={'class': 'form-control'}),
            'sigla': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

import re
from django import forms
from .models import TermoCooperacao, Programa, ProjetoPDI, ContaBancaria, Processo, TipoProcesso, TermoBolsa, Fornecedor, FonteDeRecurso, TermoDeParceria, PlanoDeTrabalho, ICT, EmpresaParceira, FundacaoApoio, AgenciaFomento

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
        fields = ['nome', 'concedente', 'convenente', 'interveniente', 'programa', 'local_execucao', 'coordenador', 'processo', 'vigencia_inicio', 'vigencia_fim', 'vigencia_meses']
        
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome Oficial do Projeto', 'autofocus': True}),
            'concedente': forms.Select(attrs={'class': 'form-select'}),
            'convenente': forms.Select(attrs={'class': 'form-select'}),
            'interveniente': forms.Select(attrs={'class': 'form-select'}),
            'programa': forms.Select(attrs={'class': 'form-select'}),
            'local_execucao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Manaus-AM / Sede da Empresa'}),
            'coordenador': forms.Select(attrs={'class': 'form-select'}),
            'processo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 23200.000000/2026-00'}),
            'vigencia_inicio': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'vigencia_fim': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'vigencia_meses': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from cadastros.models import EmpresaParceira, AgenciaFomento
        
        # O campo concedente deve listar apenas Empresas e Agências de Fomento (nunca ICT ou Fundação),
        # agrupadas usando optgroups na lista.
        empresas = EmpresaParceira.objects.all().order_by('nome')
        agencias = AgenciaFomento.objects.all().order_by('sigla')
        
        choices = [('', 'Selecione a empresa ou agência...')]
        
        if empresas.exists():
            choices.append(
                ('Empresas Parceiras', [(e.pessoajuridica_ptr_id, e.nome) for e in empresas])
            )
            
        if agencias.exists():
            choices.append(
                ('Agências de Fomento', [(a.pessoajuridica_ptr_id, f"{a.sigla} - {a.nome}") for a in agencias])
            )
            
        self.fields['concedente'].choices = choices

        # Configurar valores padrão (IFAM e FAEPI) para evitar cliques desnecessários
        from cadastros.models import ICT, FundacaoApoio
        ifam = ICT.objects.filter(sigla__icontains='IFAM').first()
        faepi = FundacaoApoio.objects.filter(nome__icontains='FAEPI').first()
        if ifam:
            self.fields['convenente'].initial = ifam.pk
        if faepi:
            self.fields['interveniente'].initial = faepi.pk

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import PessoaJuridica, ICT
        # Excluir a ICT Executora (Sede/Polo) da lista de possíveis Concedentes/Parceiros
        executoras_ids = ICT.objects.filter(is_executora=True).values_list('pessoajuridica_ptr_id', flat=True)
        self.fields['concedente'].queryset = PessoaJuridica.objects.exclude(id__in=executoras_ids).order_by('nome')


class PlanoDeTrabalhoForm(forms.ModelForm):
    class Meta:
        model = PlanoDeTrabalho
        exclude = ['projeto', 'termo_homologador', 'status', 'congelado', 'versao', 'ativo', 'data_criacao', 'valor_global']
        widgets = {
            'data_inicio': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'data_fim': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'total_meses': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'arquivo_pdf': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'aporte_empresa': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'aporte_embrapii': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'aporte_sebrae': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'aporte_contrapartida': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            
            # Rich Text Fields (Will be initialized by Javascript/Quill on frontend)
            'motivacao': forms.Textarea(attrs={'class': 'form-control richtext', 'rows': 5}),
            'objetivo_geral': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'objetivos_especificos': forms.Textarea(attrs={'class': 'form-control richtext', 'rows': 5}),
            'escopo_geral': forms.Textarea(attrs={'class': 'form-control richtext', 'rows': 5}),
            'estrutura_analitica': forms.Textarea(attrs={'class': 'form-control richtext', 'rows': 5}),
            'tecnologias_utilizadas': forms.Textarea(attrs={'class': 'form-control richtext', 'rows': 5}),
            'vulnerabilidades': forms.Textarea(attrs={'class': 'form-control richtext', 'rows': 5}),
            'plano_riscos': forms.Textarea(attrs={'class': 'form-control richtext', 'rows': 5}),
            'estrategia': forms.Textarea(attrs={'class': 'form-control richtext', 'rows': 5}),
            'caracteristicas_inovadoras': forms.Textarea(attrs={'class': 'form-control richtext', 'rows': 5}),
            'resultados_esperados': forms.Textarea(attrs={'class': 'form-control richtext', 'rows': 5}),
            'desafios_tecnologicos': forms.Textarea(attrs={'class': 'form-control richtext', 'rows': 5}),
            'solucao_proposta': forms.Textarea(attrs={'class': 'form-control richtext', 'rows': 5}),
            'orcamento_descricao': forms.Textarea(attrs={'class': 'form-control richtext', 'rows': 5}),
            
            'indicadores': forms.SelectMultiple(attrs={'class': 'form-select select2-multiple', 'multiple': 'multiple'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        from decimal import Decimal
        from django.core.exceptions import ValidationError
        from cadastros.models import PessoaJuridica
        
        v_empresa = cleaned_data.get('aporte_empresa') or Decimal('0.00')
        v_embrapii = cleaned_data.get('aporte_embrapii') or Decimal('0.00')
        v_sebrae = cleaned_data.get('aporte_sebrae') or Decimal('0.00')
        v_contrapartida = cleaned_data.get('aporte_contrapartida') or Decimal('0.00')
        
        valor_total = v_empresa + v_embrapii + v_sebrae + v_contrapartida
        
        if valor_total > 0:
            min_embrapii = valor_total * Decimal('0.10')
            if v_embrapii < min_embrapii:
                self.add_error('aporte_embrapii', f"O aporte EMBRAPII deve ser no mínimo 10% do valor global (R$ {min_embrapii:.2f}).")
                
            concedente_id = self.data.get('concedente')
            is_agencia = False
            if concedente_id:
                try:
                    pj = PessoaJuridica.objects.get(id=concedente_id)
                    is_agencia = hasattr(pj, 'agenciafomento')
                except PessoaJuridica.DoesNotExist:
                    pass
                    
            if not is_agencia:
                min_empresa = valor_total * Decimal('0.10')
                if v_empresa < min_empresa:
                    self.add_error('aporte_empresa', f"O aporte da Empresa deve ser no mínimo 10% do valor global (R$ {min_empresa:.2f}). Se for um projeto de capacitação (100% EMBRAPII), o concedente do projeto deve ser uma Agência de Fomento.")
                    
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
        # pyrefly: ignore [missing-attribute]
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


import datetime

class TermoCooperacaoForm(forms.ModelForm):
    numero_sequencial = forms.CharField(
        label="Número", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 17', 'style': 'text-align: right;'})
    )
    ano_termo = forms.ChoiceField(
        label="Ano", 
        choices=[], 
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = TermoCooperacao
        fields = ['concedente', 'convenente', 'objeto', 'valor_global', 'vigencia_inicio', 'vigencia_fim', 'arquivo_pdf', 'ativo']
        widgets = {
            'concedente': forms.Select(attrs={'class': 'form-select'}),
            'convenente': forms.Select(attrs={'class': 'form-select'}),
            'objeto': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descreva o objeto do termo de cooperação'}),
            'valor_global': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'vigencia_inicio': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'vigencia_fim': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate year choices from 2010 to next year
        current_year = datetime.datetime.now().year
        self.fields['ano_termo'].choices = [(str(y), str(y)) for y in range(current_year + 1, 2009, -1)]

        if self.instance and self.instance.numero:
            parts = self.instance.numero.split('/')
            if len(parts) == 2:
                self.fields['numero_sequencial'].initial = parts[0]
                self.fields['ano_termo'].initial = parts[1]

        # Auto-selecionar IFAM como convenente padrão em novos cadastros
        from .models import ICT, PessoaJuridica
        
        if not self.instance.pk:
            ifam = ICT.objects.filter(sigla__icontains="IFAM").first()
            if not ifam:
                ifam = ICT.objects.first()
            if ifam:
                self.fields['convenente'].initial = ifam.pk

        # Excluir a ICT Executora da lista de possíveis Parceiros (concedente)
        executoras_ids = ICT.objects.filter(is_executora=True).values_list('pessoajuridica_ptr_id', flat=True)
        self.fields['concedente'].queryset = PessoaJuridica.objects.exclude(id__in=executoras_ids).order_by('nome')

    def clean(self):
        cleaned_data = super().clean()
        num = cleaned_data.get('numero_sequencial')
        ano = cleaned_data.get('ano_termo')
        if num and ano:
            # We enforce exactly XX/YYYY format conceptually, but basically whatever user inputs for num
            numero_concatenado = f"{num.strip()}/{ano}"
            
            # Check for uniqueness since we excluded it from fields
            qs = TermoCooperacao.objects.filter(numero=numero_concatenado)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                self.add_error('numero_sequencial', 'Já existe um Termo de Cooperação com este número/ano.')
            else:
                self.instance.numero = numero_concatenado
                
        return cleaned_data

class ProgramaForm(forms.ModelForm):
    class Meta:
        model = Programa
        fields = ['termo_cooperacao', 'nome', 'descricao', 'ativo']
        widgets = {
            'termo_cooperacao': forms.Select(attrs={'class': 'form-select'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

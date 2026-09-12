import re
from django import forms
from .models import TermoCooperacao, Programa, ProjetoPDI, ContaBancaria, Processo, TipoProcesso, TermoBolsa, Fornecedor, FonteDeRecurso, Convenio, PlanoDeTrabalho, ICT, EmpresaParceira, FundacaoApoio, AgenciaFomento, TipoInstrumentoJuridico, TermoAditivo, TermoEncerramento
from .models import (
    PessoaFisica, PerfilServidor, PerfilAluno,
    PerfilColaboradorExterno, PerfilTerceirizado, DadoBancario,
)

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
        fields = ['projeto', 'nome', 'concedente', 'convenente', 'interveniente', 'programa', 'local_execucao', 'coordenador', 'processo', 'vigencia_inicio', 'vigencia_fim', 'vigencia_meses']
        
        widgets = {
            'projeto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Bio Caroço'}),
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


class TipoInstrumentoJuridicoForm(forms.ModelForm):
    class Meta:
        model = TipoInstrumentoJuridico
        fields = ['sigla', 'nome', 'fundamentacao_legal', 'descricao', 'exige_fundacao_apoio', 'ativo']
        widgets = {
            'sigla': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: AP, TC, NDA'}),
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Acordo de Parceria para PD&I'}),
            'fundamentacao_legal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Art. 9º da Lei nº 10.973/2004 e Decreto nº 9.283/2018'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição e finalidade do tipo de instrumento...'}),
            'exige_fundacao_apoio': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }



class ConvenioForm(forms.ModelForm):
    class Meta:
        model = Convenio
        fields = ['tipo_instrumento_fk', 'tipo_instrumento', 'numero', 'ano', 'objeto', 'concedente', 'convenente', 'interveniente', 'data_assinatura', 'vigencia_inicio', 'vigencia_fim']
        widgets = {
            'tipo_instrumento_fk': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'tipo_instrumento': forms.Select(attrs={'class': 'form-select'}),
            'numero': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Ex: 1'}),
            'ano': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Ex: 2026'}),
            'objeto': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Objeto do Termo de Parceria...'}),
            'concedente': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'convenente': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'interveniente': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'data_assinatura': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control form-control-lg', 'type': 'date'}),
            'vigencia_inicio': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control form-control-lg', 'type': 'date'}),
            'vigencia_fim': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control form-control-lg', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import PessoaJuridica, ICT
        
        current_year = datetime.datetime.now().year
        year_choices = [(y, str(y)) for y in range(current_year, 2009, -1)]
        self.fields['ano'].widget = forms.Select(choices=year_choices, attrs={'class': 'form-select form-select-lg'})
        
        # Preenche ano corrente em novos formulários se não definido
        if not self.instance.pk and 'ano' not in self.initial:
            self.initial['ano'] = current_year
            
        self.fields['tipo_instrumento'].choices = [
            ('CONVENIO', 'Convênio de PD&I'),
            ('ACORDO_PARCERIA', 'Acordo de Parceria para PD&I (Marco Legal CT&I)'),
        ]
        # Concedentes permitidos: ICT (não executora), EmpresaParceira, AgenciaFomento
        from django.db.models import Q
        executoras_ids = ICT.objects.filter(is_executora=True).values_list('pessoajuridica_ptr_id', flat=True)
        self.fields['concedente'].queryset = PessoaJuridica.objects.filter(
            Q(ict__isnull=False) | Q(empresaparceira__isnull=False) | Q(agenciafomento__isnull=False)
        ).exclude(id__in=executoras_ids).order_by('nome')

    def save(self, commit=True):
        instance = super().save(commit=False)
        sigla = 'CV' if instance.tipo_instrumento == 'CONVENIO' else 'AP'
        tipo_obj = TipoInstrumentoJuridico.objects.filter(sigla=sigla).first()
        if tipo_obj:
            instance.tipo_instrumento_fk = tipo_obj
        if commit:
            instance.save()
            self.save_m2m()
        return instance



class TermoAditivoForm(forms.ModelForm):
    class Meta:
        model = TermoAditivo
        fields = ['instrumento', 'numero', 'data_assinatura', 'nova_data_fim', 'valor_acrescimo', 'objeto', 'arquivo_pdf']
        widgets = {
            'data_assinatura': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'nova_data_fim': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
        }

class TermoEncerramentoForm(forms.ModelForm):
    class Meta:
        model = TermoEncerramento
        fields = ['instrumento', 'data_encerramento', 'motivo_rescisao', 'oficio_comunicacao', 'arquivo_pdf']
        widgets = {
            'data_encerramento': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
        }

class PlanoDeTrabalhoForm(forms.ModelForm):
    class Meta:
        model = PlanoDeTrabalho
        exclude = ['projeto', 'termo_homologador', 'status', 'congelado', 'versao', 'ativo', 'data_criacao', 'valor_global', 'data_inicio', 'data_fim', 'total_meses']
        widgets = {
            'arquivo_pdf': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'aporte_empresa': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'aporte_embrapii': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'aporte_sebrae': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'aporte_contrapartida': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            
            # Rich Text Fields (Will be initialized by Javascript/Quill on frontend)
            'motivacao': forms.Textarea(attrs={'class': 'form-control richtext', 'rows': 5}),
            'objetivo_geral': forms.Textarea(attrs={'class': 'form-control richtext', 'rows': 5}),
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
        fields = [
            'cota_pt', 'pessoa', 'modalidade_bolsa', 'carga_horaria_semanal', 'carga_horaria_total',
            'numero_termo', 'vigencia_inicio', 'vigencia_fim', 'quantidade_parcelas', 'valor_parcela',
            'status', 'autorizacao_excepcional', 'justificativa_excepcional'
        ]
        widgets = {
            'cota_pt': forms.Select(attrs={'class': 'form-select'}),
            'pessoa': forms.Select(attrs={'class': 'form-select'}),
            'modalidade_bolsa': forms.Select(attrs={'class': 'form-select'}),
            'numero_termo': forms.TextInput(attrs={'class': 'form-control'}),
            'vigencia_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'vigencia_fim': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'quantidade_parcelas': forms.NumberInput(attrs={'class': 'form-control'}),
            'carga_horaria_semanal': forms.NumberInput(attrs={'class': 'form-control'}),
            'carga_horaria_total': forms.NumberInput(attrs={'class': 'form-control'}),
            'valor_parcela': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select fw-bold'}),
            'autorizacao_excepcional': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'justificativa_excepcional': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ICTForm(forms.ModelForm):
    class Meta:
        model = ICT
        fields = ['nome', 'cnpj', 'natureza_juridica', 'endereco', 'representante_legal', 'cargo_representante', 'sigla', 'campus_unidade', 'nome_nit']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'sigla': forms.TextInput(attrs={'class': 'form-control'}),
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
        fields = ['nome', 'nome_fantasia', 'cnpj', 'natureza_juridica', 'endereco', 'representante_legal', 'cargo_representante', 'porte', 'segmento_atuacao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_fantasia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Apple, Microsoft...'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control', 'data-mask': '00.000.000/0000-00'}),
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
        fields = ['nome', 'sigla', 'cnpj', 'natureza_juridica', 'endereco', 'representante_legal', 'cargo_representante', 'registro_mec', 'validade_credenciamento']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'sigla': forms.TextInput(attrs={'class': 'form-control'}),
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
            'sigla': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00.000.000/0000-00'}),
            'natureza_juridica': forms.TextInput(attrs={'class': 'form-control', 'value': 'Privada'}),
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
            'sigla': forms.TextInput(attrs={'class': 'form-control'}),
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
    class Meta:
        model = TermoCooperacao
        fields = ['tipo_instrumento_fk', 'numero', 'ano', 'concedente', 'convenente', 'objeto', 'valor_global', 'data_assinatura', 'vigencia_inicio', 'vigencia_fim', 'arquivo_pdf', 'ativo']
        widgets = {
            'tipo_instrumento_fk': forms.HiddenInput(),
            'numero': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 17', 'style': 'text-align: right;'}),
            'ano': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 2026'}),
            'concedente': forms.Select(attrs={'class': 'form-select'}),
            'convenente': forms.Select(attrs={'class': 'form-select'}),
            'objeto': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descreva o objeto do termo de cooperação'}),
            'valor_global': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'data_assinatura': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'vigencia_inicio': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'vigencia_fim': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        current_year = datetime.datetime.now().year
        year_choices = [(y, str(y)) for y in range(current_year, 2009, -1)]
        self.fields['ano'].widget = forms.Select(choices=year_choices, attrs={'class': 'form-select'})
        
        # Preenche ano corrente em novos formulários se não definido
        if not self.instance.pk and 'ano' not in self.initial:
            self.initial['ano'] = current_year

        # Auto-selecionar IFAM como convenente padrão em novos cadastros
        from .models import ICT, PessoaJuridica
        
        if not self.instance.pk:
            ifam = ICT.objects.filter(sigla__icontains="IFAM").first()
            if not ifam:
                ifam = ICT.objects.first()
            if ifam:
                self.fields['convenente'].initial = ifam.pk

        # Concedentes permitidos: ICT (não executora), EmpresaParceira, AgenciaFomento
        from django.db.models import Q
        executoras_ids = ICT.objects.filter(is_executora=True).values_list('pessoajuridica_ptr_id', flat=True)
        self.fields['concedente'].queryset = PessoaJuridica.objects.filter(
            Q(ict__isnull=False) | Q(empresaparceira__isnull=False) | Q(agenciafomento__isnull=False)
        ).exclude(id__in=executoras_ids).order_by('nome')

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


# ==============================================================================
# FASE 6.1 — IDENTIDADE CANÔNICA & GESTÃO DE PESSOAS FÍSICAS (PARTY-ROLE)
# ==============================================================================

def validar_cpf_matematico(cpf_limpo: str) -> bool:
    """
    Validação algorítmica canônica da Receita Federal (Módulo 11).
    Rejeita sequências repetidas e valida os dois dígitos verificadores.
    Truncamento para hash SHA-256 8-char é intencional e adequado ao volume institucional.
    """
    if len(cpf_limpo) != 11 or cpf_limpo == cpf_limpo[0] * 11:
        return False
    # Primeiro dígito verificador
    soma = sum(int(cpf_limpo[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    d1 = 0 if resto == 10 else resto
    if d1 != int(cpf_limpo[9]):
        return False
    # Segundo dígito verificador
    soma = sum(int(cpf_limpo[i]) * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    d2 = 0 if resto == 10 else resto
    return d2 == int(cpf_limpo[10])


class PessoaFisicaForm(forms.ModelForm):
    class Meta:
        model = PessoaFisica
        fields = [
            'nome', 'cpf', 'rg', 'orgao_emissor_rg', 'data_nascimento',
            'nacionalidade', 'estado_civil', 'endereco', 'cep', 'telefone',
            'email', 'user',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome Completo'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
            'rg': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número do RG'}),
            'orgao_emissor_rg': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Órgão Emissor'}),
            'data_nascimento': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'nacionalidade': forms.TextInput(attrs={'class': 'form-control'}),
            'estado_civil': forms.Select(attrs={'class': 'form-select'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Endereço Completo'}),
            'cep': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-000'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(92) 90000-0000'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@institucional.com'}),
            'user': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # R-02: expurga o campo 'user' para qualquer requisitante que não seja superusuário,
        # impedindo injeção de user via POST mesmo que o campo seja enviado manualmente.
        if not current_user or not current_user.is_superuser:
            if 'user' in self.fields:
                del self.fields['user']
        # Campos com default no model não são required no form (evita falha silenciosa no POST)
        self.fields['estado_civil'].required = False
        self.fields['nacionalidade'].required = False

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf', '')
        cpf_limpo = re.sub(r'\D', '', str(cpf))
        if not validar_cpf_matematico(cpf_limpo):
            raise forms.ValidationError("CPF inválido perante o algoritmo oficial da Receita Federal.")
        cpf_formatado = f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
        # R-05: guarda explícita para exclude na edição (instance.pk pode ser None no cadastro)
        qs = PessoaFisica.objects.filter(cpf=cpf_formatado)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Este CPF já está cadastrado para outra pessoa.")
        return cpf_formatado


class PerfilServidorForm(forms.ModelForm):
    ativo = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    interno = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    cargo_direcao = forms.ChoiceField(
        required=False,
        choices=PerfilServidor.CARGOS_DIRECAO_CHOICES,
        initial='NENHUM',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = PerfilServidor
        fields = ['siape', 'cargo', 'cargo_direcao', 'lotacao', 'interno', 'ativo']
        widgets = {
            'siape': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Matrícula SIAPE'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cargo Efetivo'}),
            'lotacao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lotação / Campus'}),
        }

    def clean_cargo_direcao(self):
        valor = self.cleaned_data.get('cargo_direcao')
        return valor or 'NENHUM'


class PerfilAlunoForm(forms.ModelForm):
    ativo = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    interno = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    class Meta:
        model = PerfilAluno
        fields = ['matricula', 'nivel', 'curso', 'interno', 'ativo']
        widgets = {
            'matricula': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Matrícula Discente'}),
            'nivel': forms.Select(attrs={'class': 'form-select'}),
            'curso': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Curso'}),
        }


class PerfilColaboradorExternoForm(forms.ModelForm):
    ativo = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    class Meta:
        model = PerfilColaboradorExterno
        fields = ['instituicao_origem', 'expertise', 'ativo']
        widgets = {
            'instituicao_origem': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Instituição / Empresa de Origem'}),
            'expertise': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Área de Atuação / Expertise'}),
        }


class PerfilTerceirizadoForm(forms.ModelForm):
    ativo = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    class Meta:
        model = PerfilTerceirizado
        fields = ['empresa_contratada', 'funcao', 'ativo']
        widgets = {
            'empresa_contratada': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Empresa Contratada'}),
            'funcao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Função / Atividade'}),
        }


class DadoBancarioForm(forms.ModelForm):
    ativo = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    class Meta:
        model = DadoBancario
        fields = ['finalidade', 'banco_codigo', 'agencia', 'conta', 'chave_pix', 'ativo']
        widgets = {
            'finalidade': forms.Select(attrs={'class': 'form-select'}),
            'banco_codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 001, 237, 104'}),
            'agencia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Agência'}),
            'conta': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Conta com dígito'}),
            'chave_pix': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Chave PIX'}),
        }

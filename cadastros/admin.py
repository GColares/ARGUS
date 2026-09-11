from django.contrib import admin
from .models import Fornecedor, OrigemDoacao, ProjetoPDI, ContaBancaria, TipoProcesso, Processo, AtividadePlanoAcao, PessoaJuridica, ICT, EmpresaParceira, FundacaoApoio, AgenciaFomento, TermoDeParceria, PlanoDeTrabalho, PessoaFisica, PerfilServidor, Parcela, TipoInstrumentoJuridico, TermoAditivo, AditivoTermoCooperacao

@admin.register(TipoInstrumentoJuridico)
class TipoInstrumentoJuridicoAdmin(admin.ModelAdmin):
    list_display = ('sigla', 'nome', 'fundamentacao_legal', 'exige_fundacao_apoio', 'ativo')
    search_fields = ('sigla', 'nome', 'fundamentacao_legal')
    list_filter = ('ativo', 'exige_fundacao_apoio')

class TermoAditivoInline(admin.TabularInline):
    model = TermoAditivo
    extra = 0

class AditivoTermoCooperacaoInline(admin.TabularInline):
    model = AditivoTermoCooperacao
    extra = 0

class AtividadePlanoAcaoInline(admin.TabularInline):
    model = AtividadePlanoAcao
    extra = 1

# Inlines NÃO usam o decorador @admin.register()
class ContaBancariaInline(admin.TabularInline):
    model = ContaBancaria
    extra = 1 # Linha em branco pronta para adicionar uma conta

@admin.register(PessoaJuridica)
class PessoaJuridicaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cnpj', 'natureza_juridica', 'representante_legal')
    search_fields = ('nome', 'cnpj')

@admin.register(ICT)
class ICTAdmin(admin.ModelAdmin):
    list_display = ('sigla', 'nome', 'cnpj', 'nome_nit')
    search_fields = ('sigla', 'nome', 'cnpj')

@admin.register(EmpresaParceira)
class EmpresaParceiraAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cnpj', 'porte')
    search_fields = ('nome', 'cnpj')

@admin.register(FundacaoApoio)
class FundacaoApoioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cnpj', 'validade_credenciamento')
    search_fields = ('nome', 'cnpj')

@admin.register(AgenciaFomento)
class AgenciaFomentoAdmin(admin.ModelAdmin):
    list_display = ('sigla', 'nome', 'esfera')
    search_fields = ('sigla', 'nome')

class PlanoDeTrabalhoInline(admin.TabularInline):
    model = PlanoDeTrabalho
    extra = 1

@admin.register(TermoDeParceria)
class TermoDeParceriaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'concedente', 'convenente', 'data_assinatura', 'vigencia_inicio', 'vigencia_fim', 'ativo')
    search_fields = ('numero',)
    inlines = [PlanoDeTrabalhoInline, TermoAditivoInline]

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "tipo_instrumento":
            kwargs['choices'] = [
                ('CONVENIO', 'Convênio de P&D&I (Legado)'),
                ('ACORDO_PARCERIA', 'Acordo de Parceria para P&D&I (Marco Legal CT&I)'),
            ]
        return super().formfield_for_choice_field(db_field, request, **kwargs)

@admin.register(ProjetoPDI)
class ProjetoPDIAdmin(admin.ModelAdmin):
    list_display = ('fase', 'projeto', 'nome', 'data_cadastro')
    search_fields = ('projeto', 'nome')
    inlines = [ContaBancariaInline]

@admin.register(TipoProcesso)
class TipoProcessoAdmin(admin.ModelAdmin):
    list_display = ('nome',)

@admin.register(Processo)
class ProcessoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'tipo', 'projeto')
    list_filter = ('tipo', 'projeto')

@admin.register(OrigemDoacao)
class OrigemDoacaoAdmin(admin.ModelAdmin):
    list_display = ('sigla', 'nome', 'cnpj')
    search_fields = ('sigla', 'nome', 'cnpj')
    list_filter = ('sigla', 'nome', 'cnpj')

@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ('cnpj', 'nome', 'sigla')
    search_fields = ('cnpj', 'nome', 'sigla')
    list_filter = ('cnpj', 'nome', 'sigla')

from .models import CotaBolsaPT, TermoBolsa, PlanoDeTrabalho, RubricaOrcamentariaPT, DistribuicaoContaCota, MembroEquipePT, CronogramaDesembolso

class RubricaOrcamentariaPTInline(admin.TabularInline):
    model = RubricaOrcamentariaPT
    extra = 1
    fields = ('categoria', 'valor_previsto', 'fonte_recurso')

from .models import Macroentrega

class MacroentregaInline(admin.TabularInline):
    model = Macroentrega
    extra = 1
    fields = ('numero', 'nome', 'trl', 'data_inicio', 'data_fim')

class MembroEquipePTInline(admin.TabularInline):
    model = MembroEquipePT
    extra = 1

class CronogramaDesembolsoInline(admin.TabularInline):
    model = CronogramaDesembolso
    extra = 1

@admin.register(PlanoDeTrabalho)
class PlanoDeTrabalhoAdmin(admin.ModelAdmin):
    list_display = ('projeto', 'versao', 'status', 'congelado', 'data_inicio', 'data_fim')
    search_fields = ('projeto__nome',)
    list_filter = ('versao',)
    readonly_fields = ('valor_global', 'total_i_v', 'total_vi', 'total_i_vi', 'total_vii', 'total_bruto')
    
    fieldsets = (
        ('Dados Gerais do Plano', {
            'fields': ('projeto', 'termo_homologador', 'versao', 'status', 'congelado', 'arquivo_pdf', 'data_inicio', 'data_fim')
        }),
        ('Receitas (Aportes)', {
            'fields': ('aporte_empresa', 'aporte_embrapii', 'aporte_sebrae', 'aporte_contrapartida')
        }),
        ('Resumo Financeiro de Dispêndios (Subtotais)', {
            'fields': ('valor_global', 'total_i_v', 'total_vi', 'total_i_vi', 'total_vii', 'total_bruto'),
            'description': 'Esses totais são calculados automaticamente somando os subitens lançados na tabela abaixo.'
        }),
    )

    inlines = [RubricaOrcamentariaPTInline, MacroentregaInline]

class DistribuicaoContaCotaInline(admin.TabularInline):
    model = DistribuicaoContaCota
    extra = 1

@admin.register(CotaBolsaPT)
class CotaBolsaPTAdmin(admin.ModelAdmin):
    list_display = ('perfil_funcao', 'projeto', 'quantidade_vagas', 'parcelas_previstas', 'valor_global_previsto')
    list_filter = ('projeto',)
    search_fields = ('perfil_funcao', 'projeto__nome', 'projeto__termo_parceria__numero')
    autocomplete_fields = ['projeto']
    inlines = [DistribuicaoContaCotaInline]
    filter_horizontal = ('atividades_vinculadas',)

@admin.register(TermoBolsa)
class TermoBolsaAdmin(admin.ModelAdmin):
    list_display = ('numero_termo', 'pessoa', 'cota_pt', 'modalidade_bolsa', 'status')
    search_fields = ('numero_termo', 'pessoa__nome')
    list_filter = ('status', 'modalidade_bolsa')

@admin.register(Parcela)
class ParcelaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'termo_bolsa', 'valor', 'mes_competencia', 'status', 'data_pagamento', 'conta_pagamento')
    list_filter = ('status', 'conta_pagamento')
    search_fields = ('termo_bolsa__pessoa__nome', 'termo_bolsa__numero_termo', 'numero')
    autocomplete_fields = ['termo_bolsa']


from .models import TermoCooperacao
@admin.register(TermoCooperacao)
class TermoCooperacaoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'concedente', 'convenente', 'data_assinatura', 'vigencia_inicio', 'vigencia_fim', 'ativo')
    list_filter = ('ativo', 'concedente')
    search_fields = ('numero', 'objeto')
    inlines = [AditivoTermoCooperacaoInline]

@admin.register(TermoAditivo)
class TermoAditivoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'tipo_aditivo', 'termo_parceria', 'data_assinatura', 'nova_data_fim', 'valor_aditivo')
    list_filter = ('tipo_aditivo', 'termo_parceria')
    search_fields = ('numero', 'numero_processo', 'termo_parceria__numero')

@admin.register(AditivoTermoCooperacao)
class AditivoTermoCooperacaoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'tipo_aditivo', 'termo_cooperacao', 'data_assinatura', 'nova_data_fim', 'valor_aditivo')
    list_filter = ('tipo_aditivo', 'termo_cooperacao')
    search_fields = ('numero', 'numero_processo', 'termo_cooperacao__numero')

class PerfilServidorInline(admin.StackedInline):
    model = PerfilServidor
    extra = 0

@admin.register(PessoaFisica)
class PessoaFisicaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'user', 'email', 'get_siape')
    search_fields = ('nome', 'cpf', 'email', 'user__username', 'perfil_servidor__siape')
    autocomplete_fields = ['user']
    inlines = [PerfilServidorInline]

    @admin.display(description="SIAPE")
    def get_siape(self, obj):
        return obj.siape

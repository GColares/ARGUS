from django.contrib import admin
from .models import Fornecedor, OrigemDoacao, ProjetoPDI, ContaBancaria, TipoProcesso, Processo, AtividadePlanoAcao, PessoaJuridica, ICT, EmpresaParceira, FundacaoApoio, AgenciaFomento, TermoDeParceria, PlanoDeTrabalho

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
    list_display = ('numero', 'concedente', 'convenente', 'interveniente', 'ativo')
    search_fields = ('numero',)
    inlines = [PlanoDeTrabalhoInline]

@admin.register(ProjetoPDI)
class ProjetoPDIAdmin(admin.ModelAdmin):
    list_display = ('termo_parceria', 'projeto', 'nome', 'data_cadastro')
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
    fields = ('numero', 'nome', 'mes_inicio_relativo', 'mes_fim_relativo')

class MembroEquipePTInline(admin.TabularInline):
    model = MembroEquipePT
    extra = 1

class CronogramaDesembolsoInline(admin.TabularInline):
    model = CronogramaDesembolso
    extra = 1

@admin.register(PlanoDeTrabalho)
class PlanoDeTrabalhoAdmin(admin.ModelAdmin):
    list_display = ('termo_parceria', 'versao', 'data_inicio', 'data_fim', 'valor_global')
    search_fields = ('termo_parceria__numero',)
    list_filter = ('versao',)
    readonly_fields = ('valor_global', 'total_i_v', 'total_vi', 'total_i_vi', 'total_vii', 'total_bruto')
    
    fieldsets = (
        ('Dados Gerais do Plano', {
            'fields': ('termo_parceria', 'versao', 'arquivo_pdf', 'data_inicio', 'data_fim')
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

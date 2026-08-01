from django.contrib import admin
from .models import Fornecedor, OrigemDoacao, ProjetoPDI, ContaBancaria, TipoProcesso, Processo, MembroEquipe, BolsistaProjeto, AtividadePlanoAcao

class AtividadePlanoAcaoInline(admin.TabularInline):
    model = AtividadePlanoAcao
    extra = 1

# Inlines NÃO usam o decorador @admin.register()
class ContaBancariaInline(admin.TabularInline):
    model = ContaBancaria
    extra = 1 # Linha em branco pronta para adicionar uma conta

@admin.register(ProjetoPDI)
class ProjetoPDIAdmin(admin.ModelAdmin):
    list_display = ('convenio', 'projeto', 'nome', 'interveniente', 'data_cadastro')
    search_fields = ('convenio', 'projeto', 'nome')
    inlines = [ContaBancariaInline, AtividadePlanoAcaoInline]

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

from .models import CotaBolsaPT, TermoBolsa, PlanoTrabalho, RubricaOrcamentariaPT, DistribuicaoContaCota

class RubricaOrcamentariaPTInline(admin.TabularInline):
    model = RubricaOrcamentariaPT
    extra = 1
    fields = ('categoria', 'valor_previsto', 'fonte_recurso')

from .models import Macroentrega

class MacroentregaInline(admin.TabularInline):
    model = Macroentrega
    extra = 1
    fields = ('numero', 'nome', 'mes_inicio_relativo', 'mes_fim_relativo')

@admin.register(PlanoTrabalho)
class PlanoTrabalhoAdmin(admin.ModelAdmin):
    list_display = ('projeto', 'versao', 'data_inicio', 'data_fim', 'valor_global')
    search_fields = ('projeto__nome', 'projeto__convenio')
    list_filter = ('versao',)
    readonly_fields = ('valor_global', 'total_i_v', 'total_vi', 'total_i_vi', 'total_vii', 'total_bruto')
    
    fieldsets = (
        ('Dados Gerais do Plano', {
            'fields': ('projeto', 'versao', 'arquivo_pdf', 'data_inicio', 'data_fim')
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
    search_fields = ('perfil_funcao', 'projeto__nome', 'projeto__convenio')
    autocomplete_fields = ['projeto']
    inlines = [DistribuicaoContaCotaInline]
    filter_horizontal = ('atividades_vinculadas',)

@admin.register(TermoBolsa)
class TermoBolsaAdmin(admin.ModelAdmin):
    list_display = ('numero_termo', 'bolsista_nome', 'cota_pt', 'quantidade_parcelas', 'status')
    list_filter = ('status', 'cota_pt__projeto')
    search_fields = ('numero_termo', 'bolsista_nome', 'bolsista_cpf')



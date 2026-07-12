from django.contrib import admin
from .models import Fornecedor, OrigemDoacao, ProjetoPDI, ContaBancaria, TipoProcesso, Processo

# Inlines NÃO usam o decorador @admin.register()
class ContaBancariaInline(admin.TabularInline):
    model = ContaBancaria
    extra = 1 # Linha em branco pronta para adicionar uma conta

@admin.register(ProjetoPDI)
class ProjetoPDIAdmin(admin.ModelAdmin):
    list_display = ('convenio', 'projeto', 'nome', 'interveniente', 'data_cadastro')
    search_fields = ('convenio', 'projeto', 'nome')
    inlines = [ContaBancariaInline] # A mágica acontece aqui!

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
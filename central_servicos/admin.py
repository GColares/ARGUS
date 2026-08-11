# pyrefly: ignore [untyped-import]
from django.contrib import admin
from .models import Predio, Andar, Sala, TipoAtivo, AtivoPredial, OrdemServico, MaterialUtilizado, CategoriaServico

class MaterialUtilizadoInline(admin.TabularInline):
    model = MaterialUtilizado
    extra = 1

@admin.register(Predio)
class PredioAdmin(admin.ModelAdmin):
    # pyrefly: ignore [bad-override-mutable-attribute]
    list_display = ('nome', 'sigla')

@admin.register(Andar)
class AndarAdmin(admin.ModelAdmin):
    # pyrefly: ignore [bad-override-mutable-attribute]
    list_display = ('nome', 'predio')
    list_filter = ('predio',)

@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    # pyrefly: ignore [bad-override-mutable-attribute]
    list_display = ('nome', 'andar')
    list_filter = ('andar__predio', 'andar')

@admin.register(TipoAtivo)
class TipoAtivoAdmin(admin.ModelAdmin):
    # pyrefly: ignore [bad-override-mutable-attribute]
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(AtivoPredial)
class AtivoPredialAdmin(admin.ModelAdmin):
    # pyrefly: ignore [bad-override-mutable-attribute]
    list_display = ('tipo', 'nome_apelido', 'patrimonio', 'numero_serie', 'sala')
    list_filter = ('sala__andar__predio', 'tipo')
    search_fields = ('nome_apelido', 'patrimonio', 'numero_serie')

@admin.register(CategoriaServico)
class CategoriaServicoAdmin(admin.ModelAdmin):
    # pyrefly: ignore [bad-override-mutable-attribute]
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(OrdemServico)
class OrdemServicoAdmin(admin.ModelAdmin):
    # pyrefly: ignore [bad-override-mutable-attribute]
    list_display = ('numero', 'categoria', 'solicitante', 'status', 'prioridade', 'ativo_predial', 'sala', 'data_abertura')
    list_filter = ('status', 'categoria', 'prioridade', 'data_abertura')
    search_fields = ('numero', 'descricao_problema')
    # pyrefly: ignore [bad-override-mutable-attribute]
    inlines = [MaterialUtilizadoInline]
    readonly_fields = ('numero', 'data_abertura', 'estoque_baixado')

@admin.register(MaterialUtilizado)
class MaterialUtilizadoAdmin(admin.ModelAdmin):
    # pyrefly: ignore [bad-override-mutable-attribute]
    list_display = ('ordem_servico', 'produto_almoxarifado', 'quantidade')
    list_filter = ('ordem_servico',)
    # pyrefly: ignore [bad-override-mutable-attribute]
    search_fields = ('produto_almoxarifado__nome', 'ordem_servico__numero')
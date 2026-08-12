# pyrefly: ignore [untyped-import]
from django.contrib import admin
from .models import Predio, Andar, Ambiente, TipoAmbiente, CategoriaElemento, TipoElemento, ElementoConstrutivo, TipoAtivo, AtivoPredial, OrdemServico, MaterialUtilizado, CategoriaServico

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

class ElementoConstrutivoInline(admin.TabularInline):
    model = ElementoConstrutivo
    extra = 1

@admin.register(TipoAmbiente)
class TipoAmbienteAdmin(admin.ModelAdmin):
    list_display = ('nome',)

@admin.register(CategoriaElemento)
class CategoriaElementoAdmin(admin.ModelAdmin):
    list_display = ('nome',)

@admin.register(TipoElemento)
class TipoElementoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria')
    list_filter = ('categoria',)

@admin.register(Ambiente)
class AmbienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'localizacao', 'predio', 'andar')
    list_filter = ('localizacao', 'predio', 'tipo')
    inlines = [ElementoConstrutivoInline]


@admin.register(TipoAtivo)
class TipoAtivoAdmin(admin.ModelAdmin):
    # pyrefly: ignore [bad-override-mutable-attribute]
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(AtivoPredial)
class AtivoPredialAdmin(admin.ModelAdmin):
    # pyrefly: ignore [bad-override-mutable-attribute]
    list_display = ('tipo', 'nome_apelido', 'patrimonio', 'numero_serie', 'ambiente')
    list_filter = ('ambiente__predio', 'tipo')
    search_fields = ('nome_apelido', 'patrimonio', 'numero_serie')

@admin.register(CategoriaServico)
class CategoriaServicoAdmin(admin.ModelAdmin):
    # pyrefly: ignore [bad-override-mutable-attribute]
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(OrdemServico)
class OrdemServicoAdmin(admin.ModelAdmin):
    # pyrefly: ignore [bad-override-mutable-attribute]
    list_display = ('numero', 'categoria', 'solicitante', 'status', 'prioridade', 'ativo_predial', 'ambiente', 'data_abertura')
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
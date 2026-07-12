from django.contrib import admin
from .models import PerfilUsuario, NotaFiscalAlmoxarifado, ProdutoAlmoxarifado, FotoProduto, CotaDiariaIA, Imposto, ImpostoNota

@admin.register(Imposto)
class ImpostoAdmin(admin.ModelAdmin):
    list_display = ('sigla', 'esfera', 'descricao')
    list_filter = ('esfera',)
    search_fields = ('sigla', 'descricao')
    ordering = ('esfera', 'sigla')

class ImpostoNotaInline(admin.TabularInline):
    model = ImpostoNota
    extra = 0  # Não mostra linhas vazias extras por padrão
    autocomplete_fields = ['imposto'] # Adiciona uma barra de pesquisa para facilitar

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'vinculo', 'siape', 'cpf', 'cargo', 'lotacao')
    search_fields = ('user', 'vinculo', 'siape', 'cpf', 'cargo', 'lotacao')
    list_filter = ('user', 'vinculo', 'siape', 'cpf', 'cargo', 'lotacao')

@admin.register(NotaFiscalAlmoxarifado)
class NotaFiscalAlmoxarifadoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'serie', 'data_emissao', 'valor_total_nota', 'valor_desconto', 'valor_total_produtos', 'fornecedor', 'destinatario_nome')
    search_fields = ('numero', 'serie', 'fornecedor__razao_social', 'destinatario_nome')
    list_filter = ('data_emissao', 'fornecedor', 'destinatario_nome')
    inlines = [ImpostoNotaInline]  # Adiciona a inline dos impostos relacionados à nota fiscal

@admin.register(ProdutoAlmoxarifado)
class ProdutoAlmoxarifadoAdmin(admin.ModelAdmin):
    list_display = ('nota_fiscal', 'descricao', 'quantidade', 'valor_unitario')
    search_fields = ('descricao',)
    list_filter = ('nota_fiscal',)


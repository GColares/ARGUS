from django.contrib import admin
from .models import InstituicaoParceira, Convenio, ProjetoPDI, Pessoa, EquipeProjeto

@admin.register(InstituicaoParceira)
class InstituicaoParceiraAdmin(admin.ModelAdmin):
    list_display = ('sigla', 'nome', 'cnpj')
    search_fields = ('sigla', 'nome')

@admin.register(Convenio)
class ConvenioAdmin(admin.ModelAdmin):
    list_display = ('numero_convenio', 'instituicao', 'data_inicio', 'data_fim', 'ativo')
    list_filter = ('instituicao', 'ativo')
    search_fields = ('numero_convenio', 'objeto')

@admin.register(ProjetoPDI)
class ProjetoPDIAdmin(admin.ModelAdmin):
    # Removidos 'codigo' e 'coordenador', pois agora são geridos pelo nome e pela tabela de Equipa
    list_display = ('nome', 'convenio', 'status')
    list_filter = ('status', 'convenio__instituicao', 'convenio')
    search_fields = ('nome',)

@admin.register(Pessoa)
class PessoaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'email')
    search_fields = ('nome', 'cpf')

@admin.register(EquipeProjeto)
class EquipeProjetoAdmin(admin.ModelAdmin):
    list_display = ('pessoa', 'projeto', 'funcao', 'tipo_bolsa', 'ativo')
    list_filter = ('funcao', 'tipo_bolsa', 'ativo', 'projeto')
    search_fields = ('pessoa__nome', 'projeto__nome')
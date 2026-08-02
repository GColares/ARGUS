from django.shortcuts import render
from django.contrib.auth.decorators import login_required
    
@login_required
def home_argus(request):
    """
    Dashboard principal do ARGUS.
    Módulos organizados alfabeticamente.
    """
    modulos = [
        {
            'nome': 'Almoxarifado', 
            'url': 'almoxarifado:home_almoxarifado', 
            'icone': 'fa-dolly', 
            'cor': 'danger',
            'descricao': 'Gestão de entradas e controle de estoque por NF-e.'
        },
        {
            'nome': 'Cadastros', # <--- MÓDULO ADICIONADO
            'url': 'cadastros:home_cadastros', # Ajuste conforme a sua URL de cadastros
            'icone': 'fa-database', 
            'cor': 'success',
            'descricao': 'Gestão de Fornecedores, Projetos e Processos.'
        },
        {
            'nome': 'Incorporação', 
            'url': 'incorporacao:home_incorporacao', 
            'icone': 'fa-folder-plus', 
            'cor': 'primary',
            'descricao': 'Gestão de termos de doação e incorporação patrimonial.'
        },
        {
            'nome': 'Patrimônio', 
            'url': 'patrimonio:home_patrimonio', 
            'icone': 'fa-university', 
            'cor': 'info',
            'descricao': 'Controle de bens tombados e movimentações internas.'
        },
        {
            'nome': 'Central de Serviços: Manutenção, Infraestrutura e Logística', 
            'url': 'central_servicos:dashboard', 
            'icone': 'fa-building', 
            'cor': 'warning',
            'descricao': 'Gestão de infraestrutura, logística e serviços operacionais.'
        },
    ]

    # A ordenação alfabética (sorted) tratará de colocar "Cadastros" logo após "Almoxarifado" automaticamente!
    modulos_ordenados = sorted(modulos, key=lambda x: x['nome'])

    return render(request, 'home_geral.html', {'modulos': modulos_ordenados})
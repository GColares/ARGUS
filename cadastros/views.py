from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from pydantic import ValidationError
from .models import Fornecedor, ProjetoPDI, ContaBancaria, Processo, TipoProcesso, FonteDeRecurso
from .forms import ProjetoPDIForm, ContaBancariaForm, ProcessoForm, FornecedorForm, FonteDeRecursoForm
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required
def home_cadastros(request):
    return render(request, 'cadastros/home_cadastros.html')

@login_required
def listar_projetos(request):
    projetos = ProjetoPDI.objects.all().order_by('-data_cadastro')
    return render(request, 'cadastros/listar_projetos.html', {'projetos': projetos})

@login_required
def listar_fornecedores_global(request):
    fornecedores = Fornecedor.objects.all().order_by('nome')
    return render(request, 'cadastros/listar_fornecedores_global.html', {'fornecedores': fornecedores})

@login_required
def listar_processos_global(request):
    processos = Processo.objects.select_related('projeto').all().order_by('-id')
    return render(request, 'cadastros/listar_processos_global.html', {'processos': processos})
@login_required
def novo_projeto(request):
    if request.method == 'POST':
        form = ProjetoPDIForm(request.POST)
        if form.is_valid():
            projeto = form.save()
            messages.success(request, f"Projeto '{projeto.convenio}' cadastrado com sucesso no sistema!")
            return redirect('cadastros:listar_projetos')
        else:
            messages.error(request, "Erro ao cadastrar. Por favor, verifique os campos em vermelho.")
    else:
        form = ProjetoPDIForm()

    return render(request, 'cadastros/form_projeto.html', {'form': form})

@login_required
def visualizar_projeto(request, projeto_id):
    from cadastros.models import CotaBolsaPT
    projeto = get_object_or_404(ProjetoPDI, id=projeto_id)
    processos = projeto.processos.all().order_by('-id')
    cotas = CotaBolsaPT.objects.filter(projeto=projeto).order_by('perfil_funcao')
    
    contexto = {
        'projeto': projeto,
        'processos': processos,
        'cotas': cotas
    }
    return render(request, 'cadastros/visualizar_projeto.html', contexto)

@login_required
def editar_projeto(request, projeto_id):
    projeto = get_object_or_404(ProjetoPDI, id=projeto_id)
    if request.method == 'POST':
        form = ProjetoPDIForm(request.POST, instance=projeto)
        if form.is_valid():
            form.save()
            messages.success(request, f"Projeto '{projeto.convenio}' atualizado com sucesso!")
            return redirect('cadastros:listar_projetos')
    else:
        form = ProjetoPDIForm(instance=projeto)
    return render(request, 'cadastros/form_projeto.html', {'form': form, 'projeto': projeto})

@login_required
def excluir_projeto(request, projeto_id):
    projeto = get_object_or_404(ProjetoPDI, id=projeto_id)
    if request.method == 'POST':
        projeto.delete()
        messages.success(request, "Projeto excluído com sucesso!")
        return redirect('cadastros:listar_projetos')
    return render(request, 'cadastros/confirmar_exclusao_projeto.html', {'projeto': projeto})

@login_required
def gerenciar_contas(request, projeto_id):
    projeto = get_object_or_404(ProjetoPDI, id=projeto_id)
    contas_cadastradas = projeto.contas.all()
    
    if request.method == 'POST':
        form = ContaBancariaForm(request.POST)
        if form.is_valid():
            nova_conta = form.save(commit=False)
            nova_conta.projeto = projeto 
            nova_conta.save()
            messages.success(request, f"Conta {nova_conta.conta}-{nova_conta.dv} vinculada ao projeto com sucesso!")
            return redirect('cadastros:gerenciar_contas', projeto_id=projeto.id)
    else:
        form = ContaBancariaForm()

    contexto = {
        'projeto': projeto,
        'contas': contas_cadastradas,
        'form': form
    }
    return render(request, 'cadastros/gerenciar_contas.html', contexto)

@login_required
def cadastrar_processo(request):
    """
    Cadastra um novo processo (Compra, Pagamento, etc.) vinculado a um projeto PDI.
    Captura sugestões automáticas via Query String para otimizar o fluxo de clique no botão '+'.
    """
    projeto_sugerido_id = request.GET.get('projeto')
    tipo_sugerido_nome = request.GET.get('tipo', '').strip().upper()
    retorno_termo_id = request.GET.get('retorno_termo')

    tipo_sugerido_id = None
    if tipo_sugerido_nome:
        tipo_obj = TipoProcesso.objects.filter(nome__icontains=tipo_sugerido_nome).first()
        if tipo_obj:
            tipo_sugerido_id = tipo_obj.id

    initial_data = {}
    if projeto_sugerido_id:
        initial_data['projeto'] = projeto_sugerido_id
    if tipo_sugerido_id:
        initial_data['tipo'] = tipo_sugerido_id

    if request.method == 'POST':
        form = ProcessoForm(request.POST)
        if form.is_valid():
            try:
                processo = form.save()
                messages.success(request, f"Processo {processo.numero} cadastrado com sucesso!")
                
                if retorno_termo_id and str(retorno_termo_id).isdigit():
                    return redirect(f"/incorporacao/termo/{retorno_termo_id}/?abrir_modal=1")
                return redirect('cadastros:listar_processos_global')
            except Exception as e:
                messages.error(request, f"Erro operacional ao salvar o processo: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erro no campo [{field}]: {error}")
    else:
        form = ProcessoForm(initial=initial_data)

    context = {
        'form': form,
        'retorno_termo_id': retorno_termo_id,
        'projeto_sugerido_id': projeto_sugerido_id,
        'tipo_sugerido_id': tipo_sugerido_id,
    }
    return render(request, 'cadastros/form_processo.html', context)

@login_required
def editar_processo(request, id):
    processo = get_object_or_404(Processo, id=id)
    if request.method == 'POST':
        form = ProcessoForm(request.POST, instance=processo)
        if form.is_valid():
            form.save()
            messages.success(request, f"Processo '{processo.numero}' atualizado com sucesso!")
            return redirect('cadastros:listar_processos_global')
    else:
        form = ProcessoForm(instance=processo)
    return render(request, 'cadastros/form_processo.html', {'form': form, 'processo': processo})

@login_required
def visualizar_processo(request, id):
    processo = get_object_or_404(Processo, id=id)
    return render(request, 'cadastros/visualizar_processo.html', {'processo': processo})

@login_required
def excluir_processo(request, id):
    processo = get_object_or_404(Processo, id=id)
    if request.method == 'POST':
        processo.delete()
        messages.success(request, "Processo excluído com sucesso!")
        return redirect('cadastros:listar_processos_global')
    return render(request, 'cadastros/confirmar_exclusao_processo.html', {'processo': processo})


@login_required
def gerenciar_processos(request, projeto_id):
    projeto = get_object_or_404(ProjetoPDI, id=projeto_id)
    # Busca os processos já trazendo o nome do tipo para a tela ser rápida
    processos_cadastrados = projeto.processos.all().select_related('tipo').order_by('tipo__nome')

    if request.method == 'POST':
        form = ProcessoForm(request.POST)
        if form.is_valid():
            novo_processo = form.save(commit=False)
            novo_processo.projeto = projeto
            novo_processo.save()
            messages.success(request, f"Processo de {novo_processo.tipo.nome} adicionado com sucesso!")
            return redirect('cadastros:gerenciar_processos', projeto_id=projeto.id)
    else:
        form = ProcessoForm()

    contexto = {
        'projeto': projeto,
        'processos': processos_cadastrados,
        'form': form,
    }
    return render(request, 'cadastros/gerenciar_processos.html', contexto)

@login_required
def listar_processos_projeto(request, projeto_id):
    """Retorna os processos de compra/pagamento vinculados ao projeto para o Select dinâmico."""
    # Filtramos para trazer apenas processos que não sejam do tipo 'Contratação' se achar necessário,
    # ou trazemos todos os processos vinculados àquele projeto:
    processos = Processo.objects.filter(projeto_id=projeto_id).values('id', 'numero', 'tipo__nome')
    
    lista_processos = [
        {
            'id': p['id'],
            'texto': f"{p['tipo__nome']} - {p['numero']}"
        } for p in processos
    ]
    
    return JsonResponse({'processos': lista_processos})

@login_required
def cadastrar_fornecedor(request):
    """
    Cadastra um novo fornecedor (empresa/credor) no sistema ARGUS.
    Captura o CNPJ por Query String para evitar digitação duplicada e gerencia o retorno.
    """
    cnpj_sugerido = request.GET.get('cnpj', '').strip()
    retorno_termo_id = request.GET.get('retorno_termo')

    if request.method == 'POST':
        form = FornecedorForm(request.POST)
        if form.is_valid():
            novo_fornecedor = form.save()
            messages.success(request, f"Fornecedor '{novo_fornecedor.nome}' cadastrado com sucesso!")
            
            if retorno_termo_id:
                return redirect(f"{reverse('central_servicos:editar_termo_bolsa', args=[retorno_termo_id])}?fornecedor={novo_fornecedor.id}")
            return redirect('cadastros:listar_fornecedores_global')
    else:
        form = FornecedorForm(initial={'cnpj': cnpj_sugerido})

    return render(request, 'cadastros/form_fornecedor.html', {
        'form': form,
        'retorno_termo_id': retorno_termo_id
    })

@login_required
def editar_fornecedor(request, id):
    fornecedor = get_object_or_404(Fornecedor, id=id)
    if request.method == 'POST':
        form = FornecedorForm(request.POST, instance=fornecedor)
        if form.is_valid():
            form.save()
            messages.success(request, f"Fornecedor '{fornecedor.nome}' atualizado com sucesso!")
            return redirect('cadastros:listar_fornecedores_global')
    else:
        form = FornecedorForm(instance=fornecedor)
    return render(request, 'cadastros/form_fornecedor.html', {'form': form, 'fornecedor': fornecedor})

@login_required
def visualizar_fornecedor(request, id):
    fornecedor = get_object_or_404(Fornecedor, id=id)
    return render(request, 'cadastros/visualizar_fornecedor.html', {'fornecedor': fornecedor})

@login_required
def excluir_fornecedor(request, id):
    fornecedor = get_object_or_404(Fornecedor, id=id)
    if request.method == 'POST':
        fornecedor.delete()
        messages.success(request, "Fornecedor excluído com sucesso!")
        return redirect('cadastros:listar_fornecedores_global')
    return render(request, 'cadastros/confirmar_exclusao_fornecedor.html', {'fornecedor': fornecedor})

@login_required
def gerenciar_cotas(request, projeto_id):
    from .models import ProjetoPDI, CotaBolsaPT
    projeto = get_object_or_404(ProjetoPDI, id=projeto_id)
    cotas = CotaBolsaPT.objects.filter(projeto=projeto).order_by('perfil_funcao')
    
    return render(request, 'cadastros/gerenciar_cotas.html', {
        'projeto': projeto,
        'cotas': cotas
    })

@login_required
def visualizar_cota(request, cota_id):
    from .models import CotaBolsaPT, AtividadePlanoAcao
    cota = get_object_or_404(CotaBolsaPT, id=cota_id)
    projeto = cota.projeto
    atividades_projeto = AtividadePlanoAcao.objects.filter(projeto=projeto).order_by('numero')
    
    return render(request, 'cadastros/visualizar_cota.html', {
        'cota': cota,
        'projeto': projeto,
        'atividades_projeto': atividades_projeto,
        'atividades_vinculadas': cota.atividades_vinculadas.values_list('id', flat=True)
    })

@login_required
def editar_cota(request, cota_id):
    from .models import CotaBolsaPT, AtividadePlanoAcao
    cota = get_object_or_404(CotaBolsaPT, id=cota_id)
    projeto = cota.projeto
    atividades_projeto = AtividadePlanoAcao.objects.filter(projeto=projeto).order_by('numero')
    
    if request.method == 'POST':
        atividades_ids = request.POST.getlist('atividades')
        # Vincula as atividades (Limpa as antigas e add novas)
        cota.atividades_vinculadas.set(atividades_ids)
        messages.success(request, 'Atividades vinculadas com sucesso!')
        return redirect('cadastros:gerenciar_cotas', projeto_id=projeto.id)
        
    return render(request, 'cadastros/editar_cota.html', {
        'cota': cota,
        'projeto': projeto,
        'atividades_projeto': atividades_projeto,
        'atividades_vinculadas': cota.atividades_vinculadas.values_list('id', flat=True)
    })

# ==========================================
# GESTÃO DE BOLSISTAS (BANCO DE TALENTOS)
# ==========================================

@login_required
def listar_bolsistas(request):
    from .models import Bolsista
    bolsistas = Bolsista.objects.all().order_by('nome')
    return render(request, 'cadastros/listar_bolsistas.html', {'bolsistas': bolsistas})

@login_required
def criar_bolsista(request):
    from .forms import BolsistaForm
    if request.method == 'POST':
        form = BolsistaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bolsista cadastrado com sucesso!')
            return redirect('cadastros:listar_bolsistas')
    else:
        form = BolsistaForm()
    return render(request, 'cadastros/form_bolsista.html', {'form': form, 'titulo': 'Cadastrar Novo Bolsista'})

@login_required
def editar_bolsista(request, id):
    from .models import Bolsista
    from .forms import BolsistaForm
    bolsista = get_object_or_404(Bolsista, id=id)
    if request.method == 'POST':
        form = BolsistaForm(request.POST, instance=bolsista)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bolsista atualizado com sucesso!')
            return redirect('cadastros:listar_bolsistas')
    else:
        form = BolsistaForm(instance=bolsista)
    return render(request, 'cadastros/form_bolsista.html', {'form': form, 'titulo': f'Editar Bolsista: {bolsista.nome}', 'bolsista': bolsista})

@login_required
def visualizar_bolsista(request, id):
    from .models import Bolsista
    bolsista = get_object_or_404(Bolsista, id=id)
    return render(request, 'cadastros/visualizar_bolsista.html', {'bolsista': bolsista})

@login_required
def excluir_bolsista(request, id):
    from .models import Bolsista
    bolsista = get_object_or_404(Bolsista, id=id)
    if request.method == 'POST':
        try:
            bolsista.delete()
            messages.success(request, 'Bolsista excluído com sucesso!')
        except Exception as e:
            messages.error(request, f'Não foi possível excluir o bolsista pois ele está vinculado a um ou mais Termos de Bolsa. Erro: {e}')
        return redirect('cadastros:listar_bolsistas')
    return render(request, 'cadastros/confirmar_exclusao_bolsista.html', {'bolsista': bolsista})

@login_required
def listar_fontes_recurso(request):
    fontes = FonteDeRecurso.objects.all()
    return render(request, 'cadastros/listar_fontes_recurso.html', {'fontes': fontes})

@login_required
def nova_fonte_recurso(request):
    if request.method == 'POST':
        form = FonteDeRecursoForm(request.POST)
        if form.is_valid():
            fonte = form.save()
            messages.success(request, f"Fonte de Recurso '{fonte.nome}' criada com sucesso!")
            return redirect('cadastros:listar_fontes_recurso')
    else:
        form = FonteDeRecursoForm()
    return render(request, 'cadastros/form_fonte_recurso.html', {'form': form, 'titulo': 'Nova Fonte de Recursos'})

@login_required
def editar_fonte_recurso(request, id):
    fonte = get_object_or_404(FonteDeRecurso, id=id)
    if request.method == 'POST':
        form = FonteDeRecursoForm(request.POST, instance=fonte)
        if form.is_valid():
            form.save()
            messages.success(request, f"Fonte de Recurso '{fonte.nome}' atualizada com sucesso!")
            return redirect('cadastros:listar_fontes_recurso')
    else:
        form = FonteDeRecursoForm(instance=fonte)
    return render(request, 'cadastros/form_fonte_recurso.html', {'form': form, 'titulo': f'Editar Fonte: {fonte.nome}', 'fonte': fonte})

@login_required
def visualizar_fonte_recurso(request, id):
    fonte = get_object_or_404(FonteDeRecurso, id=id)
    return render(request, 'cadastros/visualizar_fonte_recurso.html', {'fonte': fonte})

@login_required
def excluir_fonte_recurso(request, id):
    fonte = get_object_or_404(FonteDeRecurso, id=id)
    if request.method == 'POST':
        try:
            fonte.delete()
            messages.success(request, "Fonte de Recurso excluída com sucesso!")
        except Exception as e:
            messages.error(request, f"Não foi possível excluir a fonte pois ela está em uso. Erro: {e}")
        return redirect('cadastros:listar_fontes_recurso')
    return render(request, 'cadastros/confirmar_exclusao_fonte_recurso.html', {'fonte': fonte})

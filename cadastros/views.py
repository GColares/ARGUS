from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from pydantic import ValidationError
from .models import Fornecedor, ProjetoPDI, ContaBancaria, Processo, TipoProcesso
from .forms import ProjetoPDIForm, ContaBancariaForm, ProcessoForm
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required
def home_cadastros(request):
    projetos = ProjetoPDI.objects.all().order_by('-data_cadastro')
    return render(request, 'cadastros/home_cadastros.html', {'projetos': projetos})

@login_required
def novo_projeto(request):
    if request.method == 'POST':
        form = ProjetoPDIForm(request.POST)
        if form.is_valid():
            projeto = form.save()
            messages.success(request, f"Projeto '{projeto.convenio}' cadastrado com sucesso no sistema!")
            return redirect('cadastros:home_cadastros')
        else:
            messages.error(request, "Erro ao cadastrar. Por favor, verifique os campos em vermelho.")
    else:
        form = ProjetoPDIForm()

    return render(request, 'cadastros/form_projeto.html', {'form': form})

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
    # 1. Captura parâmetros opcionais vindos da URL (GET) para pré-preenchimento inteligente
    projeto_sugerido_id = request.GET.get('projeto')
    tipo_sugerido_nome = request.GET.get('tipo', '').strip().upper()
    retorno_termo_id = request.GET.get('retorno_termo')

    if request.method == 'POST':
        projeto_id = request.POST.get('projeto')
        tipo_id = request.POST.get('tipo')
        numero = request.POST.get('numero', '').strip()
        origem = request.POST.get('origem')
        descricao = request.POST.get('descricao', '').strip()

        try:
            # Instancia o objeto na memória
            novo_processo = Processo(
                projeto_id=projeto_id,
                tipo_id=tipo_id,
                numero=numero,
                origem=origem,
                descricao=descricao
            )
            
            # Força a execução das validações do clean() do models.py (Regex de máscaras do IFAM/FAEPI)
            novo_processo.full_clean()
            novo_processo.save()

            messages.success(request, f"Processo {numero} cadastrado com sucesso!")
            
            # Fluxo de retorno inteligente: se veio de um termo específico, volta para ele
            if retorno_termo_id and retorno_termo_id.isdigit() :
                return redirect(f"/incorporacao/termo/{retorno_termo_id}/?abrir_modal=1")
            
            return redirect('incorporacao:home_incorporacao')

        except ValidationError as e:
            # Trata erros de validação de formulário/regex de forma amigável para o usuário
            if hasattr(e, 'message_dict'):
                for campo, erros in e.message_dict.items():
                    for erro in erros:
                        messages.error(request, f"Erro no campo [{campo}]: {erro}")
            else:
                messages.error(request, f"Erro de validação: {', '.join(e.messages)}")
        except Exception as e:
            messages.error(request, f"Erro operacional ao salvar o processo: {str(e)}")

    # 2. Tenta mapear o ID do tipo sugerido (COMPRA ou PAGAMENTO) para ajudar o HTML a marcar como 'selected'
    tipo_sugerido_id = None
    if tipo_sugerido_nome:
        tipo_obj = TipoProcesso.objects.filter(nome__icontains=tipo_sugerido_nome).first()
        if tipo_obj:
            tipo_sugerido_id = tipo_obj.id

    # 3. Contexto rico para alimentar os componentes de seleção da View
    context = {
        'projetos': ProjetoPDI.objects.all().order_by('-id'),
        'tipos': TipoProcesso.objects.all().order_by('nome'),
        'origens': Processo.ORIGEM_CHOICES,
        
        # Variáveis de controle de estado para o template
        'projeto_sugerido_id': int(projeto_sugerido_id) if projeto_sugerido_id and projeto_sugerido_id.isdigit() else None,
        'tipo_sugerido_id': tipo_sugerido_id,
        'retorno_termo_id': retorno_termo_id,
    }
    
    return render(request, 'cadastros/form_processo.html', context)

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
        nome = request.POST.get('nome', '').strip()
        cnpj = request.POST.get('cnpj', '').strip()
        sigla = request.POST.get('sigla', '').strip()
        endereco = request.POST.get('endereco', '').strip()
        email = request.POST.get('email', '').strip()

        try:
            # Cria a instância e salva no banco de dados
            novo_fornecedor = Fornecedor.objects.create(
                nome=nome,
                cnpj=cnpj,
                sigla=sigla,
                endereco=endereco,
                email=email
            )

            messages.success(request, f"Fornecedor '{novo_fornecedor.nome}' cadastrado com sucesso!")
            
            # Retorna direto para a tela do termo reabrindo o modal de itens
            if retorno_termo_id and retorno_termo_id.isdigit():
                return redirect(f"/incorporacao/termo/{retorno_termo_id}/?abrir_modal=1")
            
            return redirect('incorporacao:home_incorporacao')

        except Exception as e:
            messages.error(request, f"Erro ao salvar o fornecedor: {str(e)}")

    context = {
        'cnpj_sugerido': cnpj_sugerido,
        'retorno_termo_id': retorno_termo_id,
    }
    return render(request, 'cadastros/form_fornecedor.html', context)
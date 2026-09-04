from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Fornecedor, ProjetoPDI, ContaBancaria, Processo, TipoProcesso, FonteDeRecurso, OrigemDoacao, CotaBolsaPT, MembroEquipePT, TermoDeParceria, PlanoDeTrabalho, AtividadePlanoAcao, Macroentrega, TermoCooperacao, Programa
from .forms import TermoCooperacaoForm, ProgramaForm, ProjetoPDIForm, ContaBancariaForm, ProcessoForm, FornecedorForm, FonteDeRecursoForm, TermoDeParceriaForm, PlanoDeTrabalhoForm
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
def listar_pessoas_juridicas(request):
    from .models import PessoaJuridica, ICT, EmpresaParceira, FundacaoApoio, Fornecedor, AgenciaFomento
    pessoas = PessoaJuridica.objects.all().order_by('nome')
    icts = ICT.objects.all().order_by('nome')
    empresas = EmpresaParceira.objects.all().order_by('nome')
    fundacoes = FundacaoApoio.objects.all().order_by('nome')
    fornecedores = Fornecedor.objects.all().order_by('nome')
    agencias = AgenciaFomento.objects.all().order_by('nome')
    
    context = {
        'pessoas': pessoas,
        'icts': icts,
        'empresas': empresas,
        'fundacoes': fundacoes,
        'fornecedores': fornecedores,
        'agencias': agencias,
    }
    return render(request, 'cadastros/listar_pessoas_juridicas.html', context)

@login_required
def listar_processos_global(request):
    processos = Processo.objects.select_related('projeto').all().order_by('-id')
    return render(request, 'cadastros/listar_processos_global.html', {'processos': processos})

@login_required
def novo_projeto(request):
    if request.method == 'POST':
        form_projeto = ProjetoPDIForm(request.POST)
        form_plano = PlanoDeTrabalhoForm(request.POST)
        
        valid_proj = form_projeto.is_valid()
        valid_plano = form_plano.is_valid()
        
        # FORÇAR VALIDAÇÃO COMPLETA PARA ACUSAR PENDÊNCIAS VISUAIS
        opcionais_proj = ['local_execucao', 'programa']
        opcionais_plano = ['arquivo_pdf', 'orcamento_descricao']
        
        for field_name, field in form_projeto.fields.items():
            if field_name not in opcionais_proj:
                val = form_projeto.cleaned_data.get(field_name)
                if val in [None, '', [], ()]:
                    form_projeto.add_error(field_name, 'Campo obrigatório para Publicação.')
                    valid_proj = False

        for field_name, field in form_plano.fields.items():
            if field_name not in opcionais_plano:
                val = form_plano.cleaned_data.get(field_name)
                # Verifica vazio considerando tags HTML vazias do Quill também
                is_empty = val in [None, '', [], ()] or str(val).strip() in ['<p><br></p>', '<p></p>']
                if is_empty:
                    form_plano.add_error(field_name, 'Campo obrigatório para Publicação.')
                    valid_plano = False

        
        nome = request.POST.get('nome', '').strip()
        
        action = request.POST.get('action', 'salvar')

        # Só bloqueia o salvamento total se nem o Nome foi preenchido (único campo obrigatório no DB para criar)
        if (valid_proj and valid_plano) or nome:
            try:
                with transaction.atomic():
                    if action == 'publicar' and (not valid_proj or not valid_plano):
                        messages.error(request, "Não é possível Publicar: o projeto possui pendências. Ele foi salvo apenas como rascunho.")
                        action = 'salvar'
                    # 1. Salva o Projeto primeiro (Mestre) em modo Rascunho
                    if not valid_proj:
                        erros_proj = form_projeto._errors.copy()
                        form_projeto._errors = {}
                        projeto = form_projeto.save()
                        form_projeto._errors = erros_proj
                    else:
                        projeto = form_projeto.save()
                    
                    # Opcional: Vincular um Termo Existente se houver seleção no Wizard
                    termo_id = request.POST.get('termo_existente')
                    if termo_id:
                        termo = TermoDeParceria.objects.filter(id=termo_id).first()
                        if termo:
                            termo.projeto = projeto
                            termo.save()

                    # 2. Salva o Plano de Trabalho e vincula ao Projeto
                    if not valid_plano:
                        erros_plano = form_plano._errors.copy()
                        form_plano._errors = {}
                        plano = form_plano.save(commit=False)
                        plano.projeto = projeto
                        plano.save()
                        form_plano.save_m2m()
                        form_plano._errors = erros_plano
                    else:
                        plano = form_plano.save(commit=False)
                        plano.projeto = projeto
                        plano.save()
                        form_plano.save_m2m()
                    
                    

                if action == 'publicar':
                    plano.status = 'CONGELADO_VIGENTE'
                    plano.congelado = True
                    plano.save()
                    messages.success(request, f"Projeto '{projeto.nome}' PUBLICADO (Congelado) com sucesso!")
                    return redirect('cadastros:visualizar_projeto', projeto_id=projeto.id)
                elif valid_proj and valid_plano:
                    messages.success(request, f"Projeto '{projeto.nome}' salvo e validado com sucesso (Rascunho)!")
                    return redirect('cadastros:editar_projeto', projeto_id=projeto.id)
                else:
                    messages.warning(request, "Ainda existem pendências no Plano de Trabalho do Projeto")
                    return redirect('cadastros:editar_projeto', projeto_id=projeto.id)
                    
            except Exception as e:
                messages.error(request, f"Erro ao criar projeto: {str(e)}")
        else:
            messages.error(request, "O Nome do Projeto é obrigatório para iniciar o rascunho.")
    else:
        form_projeto = ProjetoPDIForm()
        form_plano = PlanoDeTrabalhoForm()

    return render(request, 'cadastros/form_projeto.html', {
        'form_projeto': form_projeto,
        'form_plano': form_plano
    })


@login_required
def api_termos_por_empresa(request, empresa_id):
    projeto_id = request.GET.get('projeto_id')
    
    from django.db.models import Q
    # Retorna termos sem projeto OU termos vinculados a este projeto específico
    q = Q(concedente_id=empresa_id, projeto__isnull=True)
    if projeto_id:
        q |= Q(concedente_id=empresa_id, projeto_id=projeto_id)
    
    termos = TermoDeParceria.objects.filter(q).distinct()
    data = []
    for termo in termos:
        objeto_texto = termo.objeto or ''
        display = f"Termo {termo.numero} - {objeto_texto}" if termo.numero else f"Termo s/n - {objeto_texto}"
        data.append({'id': termo.id, 'display_name': display})
    
    return JsonResponse({'termos': data})

@login_required
def visualizar_projeto(request, projeto_id):
    from cadastros.models import CotaBolsaPT
    projeto = get_object_or_404(ProjetoPDI, id=projeto_id)
    processos = projeto.processos.all().order_by('-id')
    cotas = CotaBolsaPT.objects.filter(projeto=projeto).order_by('perfil_funcao')
    termo = projeto.termos_parceria.first() # Pega o termo principal (ou o mais recente)
    plano_ativo = projeto.planos_trabalho.filter(ativo=True).first()

    contexto = {
        'projeto': projeto,
        'plano_ativo': plano_ativo,
        'processos': processos,
        'cotas': cotas
    }
    return render(request, 'cadastros/visualizar_projeto.html', contexto)

@login_required
@transaction.atomic
def editar_projeto(request, projeto_id):
    projeto = get_object_or_404(ProjetoPDI, id=projeto_id)
    plano = projeto.planos_trabalho.filter(ativo=True).first()

    if request.method == 'POST':
        form_plano = PlanoDeTrabalhoForm(request.POST, instance=plano)
        form_projeto = ProjetoPDIForm(request.POST, instance=projeto)
        valid_proj = form_projeto.is_valid()
        valid_plano = form_plano.is_valid()
        
        # FORÇAR VALIDAÇÃO COMPLETA PARA ACUSAR PENDÊNCIAS VISUAIS
        opcionais_proj = ['local_execucao', 'programa']
        opcionais_plano = ['arquivo_pdf', 'orcamento_descricao']
        
        for field_name, field in form_projeto.fields.items():
            if field_name not in opcionais_proj:
                val = form_projeto.cleaned_data.get(field_name) if hasattr(form_projeto, 'cleaned_data') else None
                if val in [None, '', [], ()]:
                    form_projeto.add_error(field_name, 'Campo obrigatório para Publicação.')
                    valid_proj = False

        for field_name, field in form_plano.fields.items():
            if field_name not in opcionais_plano:
                val = form_plano.cleaned_data.get(field_name) if hasattr(form_plano, 'cleaned_data') else None
                # Verifica vazio considerando tags HTML vazias do Quill também
                is_empty = val in [None, '', [], ()] or str(val).strip() in ['<p><br></p>', '<p></p>']
                if is_empty:
                    form_plano.add_error(field_name, 'Campo obrigatório para Publicação.')
                    valid_plano = False
        is_prospeccao = projeto.fase == 'PROSPECCAO'
        nome = request.POST.get('nome', '').strip()
        
        action = request.POST.get('action', 'salvar')

        if (valid_plano and valid_proj) or (is_prospeccao and nome):
            try:
                with transaction.atomic():
                    if action == 'publicar' and (not valid_proj or not valid_plano):
                        messages.error(request, "Não é possível Publicar: o projeto possui pendências. Ele foi salvo apenas como rascunho.")
                        action = 'salvar'
                    # Projeto
                    if not valid_proj:
                        erros_proj = form_projeto._errors.copy()
                        form_projeto._errors = {}
                        projeto_salvo = form_projeto.save()
                        form_projeto._errors = erros_proj
                    else:
                        projeto_salvo = form_projeto.save()
                            
                    # Vincula ou atualiza o Termo de Parceria selecionado via AJAX
                    termo_id = request.POST.get('termo_existente')
                    if termo_id:
                        # Remove vínculo antigo se existir (evita duplicatas)
                        TermoDeParceria.objects.filter(projeto=projeto_salvo).exclude(id=termo_id).update(projeto=None)
                        # Aplica o novo vínculo
                        TermoDeParceria.objects.filter(id=termo_id).update(projeto=projeto_salvo)
                    
                    # Plano
                    if not valid_plano:
                        erros_plano = form_plano._errors.copy()
                        form_plano._errors = {}
                        plano_salvo = form_plano.save(commit=False)
                        plano_salvo.projeto = projeto_salvo
                        plano_salvo.save()
                        form_plano.save_m2m()
                        form_plano._errors = erros_plano
                    else:
                        plano_salvo = form_plano.save(commit=False)
                        plano_salvo.projeto = projeto_salvo
                        plano_salvo.save()
                        form_plano.save_m2m()
                    plano = plano_salvo

                    # --- SALVAMENTO DINÂMICO ---
                    # Limpa registros antigos para recriar com os dados atualizados
                    plano.atividades.all().delete()
                    plano.macroentregas.all().delete()
                    plano.rubricas.all().delete()
                    plano.desembolsos.all().delete()
                    
                    # 1. Atividades
                    atividades_nome = request.POST.getlist('atividade_nome[]')
                    atividades_desc = request.POST.getlist('atividade_descricao[]')
                    atividades_just = request.POST.getlist('atividade_justificativa[]')
                    atividades_entreg = request.POST.getlist('atividade_entregaveis[]')
                    atividades_inicio = request.POST.getlist('atividade_mes_inicio[]')
                    atividades_fim = request.POST.getlist('atividade_mes_fim[]')
                    
                    for i in range(len(atividades_nome)):
                        if atividades_nome[i].strip():
                            mes_in = int(atividades_inicio[i]) if atividades_inicio[i].strip() else None
                            mes_out = int(atividades_fim[i]) if atividades_fim[i].strip() else None
                            
                            atividade = AtividadePlanoAcao.objects.create(
                                plano_trabalho=plano,
                                numero=i+1,
                                nome=atividades_nome[i],
                                descricao=atividades_desc[i] if i < len(atividades_desc) else '',
                                justificativa=atividades_just[i] if i < len(atividades_just) else '',
                                mes_inicio=mes_in,
                                mes_fim=mes_out
                            )
                            
                            if i < len(atividades_entreg) and atividades_entreg[i].strip():
                                for nome_entregavel in atividades_entreg[i].split(';'):
                                    if nome_entregavel.strip():
                                        from .models import EntregavelAtividade
                                        EntregavelAtividade.objects.create(
                                            atividade=atividade,
                                            nome=nome_entregavel.strip()
                                        )
                            
                    # 2. Macroentregas
                    macro_titulos = request.POST.getlist('macro_nome[]')
                    if not macro_titulos:
                        macro_titulos = request.POST.getlist('macro_titulo[]')
                    macro_desc = request.POST.getlist('macro_micro_entregas[]')
                    if not macro_desc:
                        macro_desc = request.POST.getlist('macro_descricao[]')
                    macro_inicio = request.POST.getlist('macro_data_inicio[]')
                    if not macro_inicio:
                        macro_inicio = request.POST.getlist('macro_inicio[]')
                    macro_fim = request.POST.getlist('macro_data_fim[]')
                    if not macro_fim:
                        macro_fim = request.POST.getlist('macro_fim[]')
                    
                    for i in range(len(macro_titulos)):
                        if macro_titulos[i].strip():
                            data_in = macro_inicio[i] if i < len(macro_inicio) and macro_inicio[i].strip() else None
                            data_out = macro_fim[i] if i < len(macro_fim) and macro_fim[i].strip() else None
                            
                            Macroentrega.objects.create(
                                plano_trabalho=plano,
                                numero=i+1,
                                nome=macro_titulos[i],
                                micro_entregas=macro_desc[i] if i < len(macro_desc) else '',
                                data_inicio=data_in,
                                data_fim=data_out
                            )
                            
                    # 3. Rubricas
                    rubrica_fontes = request.POST.getlist('rubrica_fonte[]')
                    rubrica_categorias = request.POST.getlist('rubrica_categoria[]')
                    rubrica_desc = request.POST.getlist('rubrica_descricao[]')
                    rubrica_valores = request.POST.getlist('rubrica_valor[]')
                    
                    from .models import RubricaOrcamentariaPT, CronogramaDesembolso
                    for i in range(len(rubrica_fontes)):
                        if rubrica_fontes[i].strip() and rubrica_categorias[i].strip():
                            val_str = rubrica_valores[i].replace('R$', '').replace('.', '').replace(',', '.').strip() if i < len(rubrica_valores) else '0'
                            try:
                                valor_float = float(val_str)
                            except ValueError:
                                valor_float = 0.0
                                
                            RubricaOrcamentariaPT.objects.create(
                                plano_trabalho=plano,
                                fonte_recurso=rubrica_fontes[i],
                                categoria=rubrica_categorias[i],
                                descricao=rubrica_desc[i] if i < len(rubrica_desc) else '',
                                valor=valor_float
                            )
                            
                    # 4. Cronograma Financeiro (Desembolsos)
                    desembolso_mes = request.POST.getlist('desembolso_mes[]')
                    desembolso_valor = request.POST.getlist('desembolso_valor[]')
                    
                    for i in range(len(desembolso_mes)):
                        if desembolso_mes[i].strip():
                            val_str = desembolso_valor[i].replace('R$', '').replace('.', '').replace(',', '.').strip() if i < len(desembolso_valor) else '0'
                            try:
                                valor_float = float(val_str)
                            except ValueError:
                                valor_float = 0.0
                                
                            CronogramaDesembolso.objects.create(
                                plano_trabalho=plano,
                                parcela=i+1,
                                mes_previsto=desembolso_mes[i],
                                valor=valor_float
                            )

                if action == 'publicar':
                    plano_salvo.status = 'CONGELADO_VIGENTE'
                    plano_salvo.congelado = True
                    plano_salvo.save()
                    messages.success(request, f"Projeto '{projeto.nome}' PUBLICADO (Congelado) com sucesso!")
                    return redirect('cadastros:visualizar_projeto', projeto_id=projeto.id)
                elif valid_plano and valid_proj:
                    messages.success(request, f"Projeto '{projeto.nome}' salvo e validado com sucesso (Rascunho)!")
                    return redirect('cadastros:editar_projeto', projeto_id=projeto.id)
                else:
                    messages.warning(request, "Ainda existem pendências no Plano de Trabalho do Projeto")
                    # Não redireciona, cai para o render() no final para exibir os form.errors
            except Exception as e:
                messages.error(request, f"Erro ao salvar rascunho: {str(e)}")
        else:
            if not is_prospeccao:
                messages.error(request, "O projeto não está mais em prospecção e exige preenchimento completo.")
            elif not nome:
                messages.error(request, "O Nome do Projeto é obrigatório.")
                
    else:
        form_plano = PlanoDeTrabalhoForm(instance=plano)
        form_projeto = ProjetoPDIForm(instance=projeto)

    context = {
        'form_projeto': form_projeto,
        'form_plano': form_plano,
        'projeto': projeto,
        'plano_ativo': plano
    }
    return render(request, 'cadastros/form_projeto.html', context)



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
def editar_conta_bancaria(request, conta_id):
    conta = get_object_or_404(ContaBancaria, id=conta_id)
    if request.method == 'POST':
        form = ContaBancariaForm(request.POST, instance=conta)
        if form.is_valid():
            form.save()
            messages.success(request, f"Conta {conta.conta}-{conta.dv} atualizada com sucesso!")
            return redirect('cadastros:gerenciar_contas', projeto_id=conta.projeto.id)
    else:
        form = ContaBancariaForm(instance=conta)
    
    contexto = {
        'form': form,
        'conta': conta,
        'projeto': conta.projeto
    }
    return render(request, 'cadastros/editar_conta_bancaria.html', contexto)

@login_required
def excluir_conta_bancaria(request, conta_id):
    conta = get_object_or_404(ContaBancaria, id=conta_id)
    projeto_id = conta.projeto.id
    if request.method == 'POST':
        conta.delete()
        messages.success(request, "Conta bancária excluída com sucesso!")
        return redirect('cadastros:gerenciar_contas', projeto_id=projeto_id)
    
    contexto = {
        'conta': conta,
        'projeto': conta.projeto
    }
    return render(request, 'cadastros/confirmar_exclusao_conta_bancaria.html', contexto)

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

from .models import PessoaJuridica, ICT, EmpresaParceira, FundacaoApoio, AgenciaFomento, Fornecedor
from .forms import ICTForm, EmpresaParceiraForm, FundacaoApoioForm, AgenciaFomentoForm, FornecedorForm

def get_pj_class_and_form(tipo):
    mapping = {
        'ict': (ICT, ICTForm),
        'empresa': (EmpresaParceira, EmpresaParceiraForm),
        'fundacao': (FundacaoApoio, FundacaoApoioForm),
        'agencia': (AgenciaFomento, AgenciaFomentoForm),
        'fornecedor': (Fornecedor, FornecedorForm)
    }
    return mapping.get(tipo, (None, None))

@login_required
def cadastrar_pessoa_juridica(request):
    tipo = request.GET.get('tipo')
    model_class, form_class = get_pj_class_and_form(tipo)
    
    if not model_class:
        # Se não escolheu o tipo, exibe a tela de escolha
        return render(request, 'cadastros/escolher_tipo_pj.html')

    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            nova_pj = form.save()
            messages.success(request, f"{nova_pj.nome} cadastrado(a) com sucesso!")
            
            # Suporte a retorno para outras telas (ex: edição de termo de bolsa)
            retorno_termo_id = request.GET.get('retorno_termo')
            if retorno_termo_id and tipo == 'fornecedor':
                return redirect(f"{reverse('central_servicos:editar_termo_bolsa', args=[retorno_termo_id])}?fornecedor={nova_pj.id}")
            
            return redirect('cadastros:listar_pessoas_juridicas')
    else:
        form = form_class()

    return render(request, 'cadastros/form_pessoa_juridica.html', {
        'form': form,
        'tipo': tipo,
        'nome_tipo': model_class._meta.verbose_name
    })

@login_required
def editar_pessoa_juridica(request, id):
    pj_base = get_object_or_404(PessoaJuridica, id=id)
    
    # Descobre qual é a subclasse correta
    if hasattr(pj_base, 'ict'): instance, form_class, tipo = pj_base.ict, ICTForm, 'ict' # type: ignore
    elif hasattr(pj_base, 'empresaparceira'): instance, form_class, tipo = pj_base.empresaparceira, EmpresaParceiraForm, 'empresa' # type: ignore
    elif hasattr(pj_base, 'fundacaoapoio'): instance, form_class, tipo = pj_base.fundacaoapoio, FundacaoApoioForm, 'fundacao' # type: ignore
    elif hasattr(pj_base, 'agenciafomento'): instance, form_class, tipo = pj_base.agenciafomento, AgenciaFomentoForm, 'agencia' # type: ignore
    elif hasattr(pj_base, 'fornecedor'): instance, form_class, tipo = pj_base.fornecedor, FornecedorForm, 'fornecedor' # type: ignore
    else: return redirect('cadastros:listar_pessoas_juridicas')

    if request.method == 'POST':
        form = form_class(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"Cadastro de '{instance.nome}' atualizado com sucesso!")
            return redirect('cadastros:listar_pessoas_juridicas')
    else:
        form = form_class(instance=instance)
        
    return render(request, 'cadastros/form_pessoa_juridica.html', {
        'form': form, 'tipo': tipo, 'nome_tipo': instance._meta.verbose_name, 'editando': True, 'pj': instance
    })

@login_required
def excluir_pessoa_juridica(request, id):
    pj = get_object_or_404(PessoaJuridica, id=id)
    if request.method == 'POST':
        pj.delete()
        messages.success(request, "Cadastro excluído com sucesso!")
        return redirect('cadastros:listar_pessoas_juridicas')
    return render(request, 'cadastros/confirmar_exclusao_pj.html', {'pj': pj})

@login_required
def gerenciar_cotas(request, projeto_id):
    from .models import ProjetoPDI, TermoCooperacao, Programa, CotaBolsaPT
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

# --- CADASTRO DE PESSOAS FÍSICAS ---

from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import PessoaFisica

def listar_pessoas_fisicas(request):
    pessoas = PessoaFisica.objects.all().order_by('nome')
    return render(request, 'cadastros/listar_pessoas_fisicas.html', {'pessoas': pessoas})

def cadastrar_pessoa_fisica(request):
    # TODO: Implement form wizard
    messages.info(request, "Interface de cadastro de Pessoa Física em desenvolvimento.")
    return redirect('cadastros:listar_pessoas_fisicas')

def editar_pessoa_fisica(request, id):
    # TODO: Implement form wizard
    messages.info(request, "Interface de edição de Pessoa Física em desenvolvimento.")
    return redirect('cadastros:listar_pessoas_fisicas')

def excluir_pessoa_fisica(request, id):
    pessoa = get_object_or_404(PessoaFisica, id=id)
    if request.method == 'POST':
        pessoa.delete()
        messages.success(request, 'Pessoa Física excluída com sucesso!')
        return redirect('cadastros:listar_pessoas_fisicas')
    return render(request, 'cadastros/confirmar_exclusao_pf.html', {'pessoa': pessoa})


# ==============================================================================
# CRUD TERMO DE COOPERAÇÃO
# ==============================================================================
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

class TermoCooperacaoListView(ListView):
    model = TermoCooperacao
    template_name = 'cadastros/termocooperacao_list.html'
    context_object_name = 'termos'
    
class TermoCooperacaoCreateView(CreateView):
    model = TermoCooperacao
    form_class = TermoCooperacaoForm
    template_name = 'cadastros/termocooperacao_form.html'
    success_url = reverse_lazy('cadastros:listar_termos')

class TermoCooperacaoUpdateView(UpdateView):
    model = TermoCooperacao
    form_class = TermoCooperacaoForm
    template_name = 'cadastros/termocooperacao_form.html'
    success_url = reverse_lazy('cadastros:listar_termos')

class TermoCooperacaoDeleteView(DeleteView):
    model = TermoCooperacao
    template_name = 'cadastros/termocooperacao_confirm_delete.html'
    success_url = reverse_lazy('cadastros:listar_termos')

# ==============================================================================
# CRUD PROGRAMA
# ==============================================================================
class ProgramaListView(ListView):
    model = Programa
    template_name = 'cadastros/programa_list.html'
    context_object_name = 'programas'

class ProgramaCreateView(CreateView):
    model = Programa
    form_class = ProgramaForm
    template_name = 'cadastros/programa_form.html'
    success_url = reverse_lazy('cadastros:listar_programas')

class ProgramaUpdateView(UpdateView):
    model = Programa
    form_class = ProgramaForm
    template_name = 'cadastros/programa_form.html'
    success_url = reverse_lazy('cadastros:listar_programas')

class ProgramaDeleteView(DeleteView):
    model = Programa
    template_name = 'cadastros/programa_confirm_delete.html'
    success_url = reverse_lazy('cadastros:listar_programas')

# CRUD TERMO DE PARCERIA
class TermoDeParceriaListView(ListView):
    model = TermoDeParceria
    template_name = 'cadastros/termo_parceria_list.html'
    context_object_name = 'termos'
    ordering = ['-id']

class TermoDeParceriaDetailView(LoginRequiredMixin, DetailView):
    model = TermoDeParceria
    template_name = 'cadastros/termo_parceria_detail.html'
    context_object_name = 'termo'

class TermoDeParceriaCreateView(CreateView):
    model = TermoDeParceria
    form_class = TermoDeParceriaForm
    template_name = 'cadastros/termo_parceria_form.html'
    success_url = reverse_lazy('cadastros:listar_termos_parceria')

class TermoDeParceriaUpdateView(UpdateView):
    model = TermoDeParceria
    form_class = TermoDeParceriaForm
    template_name = 'cadastros/termo_parceria_form.html'
    success_url = reverse_lazy('cadastros:listar_termos_parceria')

class TermoDeParceriaDeleteView(DeleteView):
    model = TermoDeParceria
    template_name = 'cadastros/termo_parceria_confirm_delete.html'
    success_url = reverse_lazy('cadastros:listar_termos_parceria')

# Trigger restart

# Trigger restart 2

# Trigger restart 3

# Trigger restart 4

# Trigger restart 5

# Trigger restart 6

# Trigger restart 7

# Trigger restart 8

# Trigger restart 9

# Trigger restart 10

# Trigger restart 11

# Trigger restart 12

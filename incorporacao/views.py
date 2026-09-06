import re
from datetime import datetime

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from .models import TermoDoacao, ItemPatrimonial
from .services import extrair_dados_do_termo, extrair_tudo_com_ia
from cadastros.models import Fornecedor, OrigemDoacao, ProjetoPDI, Processo, Localizacao, TipoProcesso, NotaFiscal


def home_incorporacao(request):
    """Lista todos os termos de doação na fila de incorporação."""
    termos = TermoDoacao.objects.all().order_by('-id')
    return render(request, 'incorporacao/home_incorporacao.html', {'termos': termos})


@login_required
def gerar_termo_doacao_projeto(request, projeto_id):
    """
    Gera a minuta oficial do termo de doação dos bens vinculados ao projeto.
    O acesso é restrito ao superusuário ou a membros da equipe do projeto.
    """
    from decimal import Decimal
    from datetime import date
    from django.db.models import Sum
    from cadastros.models import MembroEquipe
    from patrimonio.models import BemPatrimonial

    projeto = get_object_or_404(ProjetoPDI, id=projeto_id)

    if not request.user.is_superuser:
        if not MembroEquipe.objects.filter(projeto=projeto, usuario=request.user).exists():
            return HttpResponseForbidden(
                "Acesso negado: Você não é membro da equipe deste projeto."
            )

    bens = BemPatrimonial.objects.filter(projeto=projeto).select_related(
        'ambiente',
        'termo_doacao',
    )
    total_itens = bens.count()
    valor_total = bens.aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')
    data_emissao = date.today()

    contexto = {
        'projeto': projeto,
        'bens': bens,
        'total_itens': total_itens,
        'valor_total': valor_total,
        'data_emissao': data_emissao,
        'ano_atual': data_emissao.year,
    }
    return render(request, 'incorporacao/minuta_termo_doacao.html', contexto)


def detalhe_termo(request, pk):
    """
    Exibe os detalhes de um termo e processa o cadastro de novos itens via Modal.
    Suporta a associação de múltiplos processos de pagamento.
    """
    termo = get_object_or_404(TermoDoacao, pk=pk)
    processos_projeto = Processo.objects.filter(projeto_id=termo.projeto_id)
    
    if request.method == 'POST':
        numero_ativo = request.POST.get('numero_ativo', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        
        try:
            # 1. Criação do Item com os campos diretos
            novo_item = ItemPatrimonial.objects.create(
                termo=termo,
                numero_ativo=numero_ativo,
                descricao=descricao,
                valor_bem=request.POST.get('valor_bem', '0').replace('.', '').replace(',', '.'),
                # A nova Foreign Key para a Nota Fiscal será adicionada via select no modal nas próximas etapas
                nota_fiscal_id=request.POST.get('nota_fiscal_id') or None, 
                processo_compra_id=request.POST.get('processo_compra') or None,
                localizacao_id=request.POST.get('localizacao') or None,
            )
            
            # 2. Captura múltiplos IDs de processos de pagamento (Lista)
            pagamentos_ids = request.POST.getlist('processo_pagamento')
            
            # 3. Vincula o relacionamento Muitos para Muitos
            if pagamentos_ids:
                novo_item.processos_pagamento.set(pagamentos_ids)

            messages.success(request, f"Item {numero_ativo} cadastrado com sucesso!")
            return redirect('incorporacao:detalhe_termo', pk=pk)
            
        except Exception as e:
            messages.error(request, f"Erro ao salvar item: {str(e)}")

    context = {
        'termo': termo,
        'processos_compra': processos_projeto.filter(tipo__nome__icontains='Compra').order_by('-numero'),
        'processos_pagamento': processos_projeto.filter(tipo__nome__icontains='Pagamento').order_by('-numero'),
        'localizacoes': Localizacao.objects.all().order_by('nome'),
    }
    return render(request, 'incorporacao/detalhe_termo.html', context)


def executar_extracao_argus(request, pk):
    """Aciona o robô ARGUS para extrair o objeto do PDF."""
    termo = get_object_or_404(TermoDoacao, pk=pk)

    if not termo.arquivo_pdf:
        messages.error(request, "Este termo não possui um arquivo PDF anexado.")
        return redirect('incorporacao:detalhe_termo', pk=pk)

    try:
        resultado_extracao = extrair_dados_do_termo(termo.arquivo_pdf.path)
        if resultado_extracao:
            termo.objeto = resultado_extracao
            termo.save()
            messages.success(request, "ARGUS: Extração do objeto concluída!")
        else:
            messages.warning(request, "O ARGUS não identificou o texto do objeto.")
    except Exception as e:
        messages.error(request, f"Erro crítico no processamento ARGUS: {str(e)}")

    return redirect('incorporacao:detalhe_termo', pk=pk)


def cadastrar_termo(request):
    """Criação do termo incluindo o atributo temporal de formalização."""
    if request.method == 'POST':
        projeto_id = request.POST.get('projeto')
        origem_id = request.POST.get('origem')
        numero = request.POST.get('numero')
        ano = request.POST.get('ano')
        data_formalizacao = request.POST.get('data')
        arquivo_pdf = request.FILES.get('arquivo_pdf')

        termo = TermoDoacao.objects.create(
            projeto_id=projeto_id,
            origem_id=origem_id,
            numero=numero,
            ano=ano,
            data=data_formalizacao,
            arquivo_pdf=arquivo_pdf
        )

        if termo.arquivo_pdf:
            try:
                texto_extraido = extrair_dados_do_termo(termo.arquivo_pdf.path)
                if texto_extraido:
                    termo.objeto = texto_extraido
                    termo.save()
                    messages.success(request, "Termo cadastrado e objeto extraído com sucesso!")
            except Exception as e:
                messages.error(request, f"Termo salvo, mas erro na extração: {str(e)}")
        
        return redirect('incorporacao:detalhe_termo', pk=termo.pk)

    context = {
        'projetos': ProjetoPDI.objects.all(),
        'origens': OrigemDoacao.objects.all(),
    }
    return render(request, 'incorporacao/form_termo.html', context)


def excluir_termo(request, pk):
    """Exclui um registro de termo específico."""
    termo = get_object_or_404(TermoDoacao, pk=pk)
    numero = termo.numero
    termo.delete()
    messages.warning(request, f"Termo {numero} removido com sucesso.")
    return redirect('incorporacao:home')


def limpar_registros_incompletos(request):
    """Remove termos sem objeto extraído (utilitário de limpeza)."""
    incompletos = TermoDoacao.objects.filter(Q(objeto__isnull=True) | Q(objeto=""))
    quantidade = incompletos.count()
    
    if quantidade > 0:
        incompletos.delete()
        messages.success(request, f"Limpeza concluída: {quantidade} registros removidos.")
    else:
        messages.info(request, "Não existem registros incompletos.")
        
    return redirect('incorporacao:home')


def cadastrar_processo(request):
    """
    Cadastra um novo processo vinculando-o a um projeto,
    capturando sugestões automáticas via Query String e gerenciando o retorno ao modal.
    """
    projeto_sugerido_id = request.GET.get('projeto')
    tipo_sugerido_nome = request.GET.get('tipo', '').upper()

    if request.method == 'POST':
        projeto_id = request.POST.get('projeto')
        tipo_id = request.POST.get('tipo')
        numero = request.POST.get('numero', '').strip()
        origem_formulario = request.POST.get('origem_processo')
        descricao = request.POST.get('descricao', '').strip()

        try:
            novo_processo = Processo(
                projeto_id=projeto_id,
                tipo_id=tipo_id,
                numero=numero,
                origem=origem_formulario,
                descricao=descricao
            )
            novo_processo.full_clean()
            novo_processo.save()

            messages.success(request, f"Processo {numero} cadastrado com sucesso!")
            
            termo_origem_id = request.GET.get('retorno_termo')
            if termo_origem_id and termo_origem_id.isdigit():
                return redirect(f"/incorporacao/termo/{termo_origem_id}/?abrir_modal=1")
            
            return redirect('incorporacao:home')

        except ValidationError as e:
            for campo, erros in e.message_dict.items():
                for erro in erros:
                    messages.error(request, f"Erro no campo [{campo}]: {erro}")
        except Exception as e:
            messages.error(request, f"Erro operacional ao salvar processo: {str(e)}")

    context = {
        'projetos': ProjetoPDI.objects.all().order_by('-id'),
        'tipos': TipoProcesso.objects.all().order_by('nome'),
        'origens': Processo.ORIGEM_CHOICES,
        'projeto_sugerido_id': int(projeto_sugerido_id) if projeto_sugerido_id and projeto_sugerido_id.isdigit() else None,
        'tipo_sugerido_nome': tipo_sugerido_nome,
    }
    return render(request, 'cadastros/form_processo.html', context)


def buscar_fornecedor_cnpj(request):
    """
    Endpoint que busca um fornecedor pelo CNPJ e retorna dados em JSON.
    Acessado via AJAX/Fetch pelo Modal de Itens.
    """
    cnpj = request.GET.get('cnpj', '').strip()
    cnpj_limpo = re.sub(r'\D', '', cnpj)
    
    if not cnpj_limpo:
        return JsonResponse({'sucesso': False, 'mensagem': 'CNPJ não fornecido.'}, status=400)
    
    fornecedor = Fornecedor.objects.filter(cnpj=cnpj_limpo).first() or Fornecedor.objects.filter(cnpj=cnpj).first()
    
    if fornecedor:
        return JsonResponse({
            'sucesso': True,
            'existe': True,
            'nome': fornecedor.nome,
            'sigla': fornecedor.sigla if hasattr(fornecedor, 'sigla') else '',
        })
    
    return JsonResponse({
        'sucesso': True,
        'existe': False,
        'mensagem': 'Fornecedor não encontrado no sistema.'
    })


def editar_item(request, pk):
    """Modifica os dados de um item patrimonial existente, suportando múltiplos pagamentos."""
    item = get_object_or_404(ItemPatrimonial, pk=pk)
    termo = item.termo
    
    if request.method == 'POST':
        item.numero_ativo = request.POST.get('numero_ativo', '').strip()
        item.descricao = request.POST.get('descricao', '').strip()
        valor_str = request.POST.get('valor_bem', '0')
        item.valor_bem = valor_str.replace('.', '').replace(',', '.')
        
        item.nota_fiscal_id = request.POST.get('nota_fiscal_id') or None
        item.processo_compra_id = request.POST.get('processo_compra') or None
        item.localizacao_id = request.POST.get('localizacao') or None

        try:
            item.save()
            
            # Captura a lista completa de processos de pagamento na edição
            pagamentos_ids = request.POST.getlist('processo_pagamento')
            
            if pagamentos_ids:
                item.processos_pagamento.set(pagamentos_ids)
            else:
                item.processos_pagamento.clear()

            messages.success(request, f"Item {item.numero_ativo} atualizado com sucesso!")
        except Exception as e:
            messages.error(request, f"Erro ao atualizar o item: {str(e)}")
            
        return redirect('incorporacao:detalhe_termo', pk=termo.id)


@require_POST
def excluir_item(request, pk):
    """Exclui permanentemente um item patrimonial."""
    item = get_object_or_404(ItemPatrimonial, pk=pk)
    termo_id = item.termo.id
    numero_ativo = item.numero_ativo
    
    try:
        item.delete()
        messages.warning(request, f"Item {numero_ativo} removido com sucesso.")
    except Exception as e:
        messages.error(request, f"Erro ao excluir item: {str(e)}")
        
    return redirect('incorporacao:detalhe_termo', pk=termo_id)

def processar_itens_automaticos(request, pk):
    """
    View que aciona a IA, recebe o JSON (Notas Fiscais + Itens Patrimoniais)
    e cadastra tudo no banco normalizado utilizando bloco de transação.
    """
    termo = get_object_or_404(TermoDoacao, pk=pk)

    if not termo.arquivo_pdf:
        messages.error(request, "O termo não possui PDF para análise.")
        return redirect('incorporacao:detalhe_termo', pk=pk)

    try:
        # 1. Chama o serviço atualizado do Gemini
        dados_json = extrair_tudo_com_ia(termo.arquivo_pdf.path)
        
        if not dados_json:
            messages.error(request, "Falha na comunicação com a IA do ARGUS.")
            return redirect('incorporacao:detalhe_termo', pk=pk)

        # 2. Varre o JSON e salva no banco de dados usando Transaction (Tudo ou Nada)
        with transaction.atomic():
            
            # A. Processamento das Notas Fiscais
            notas_criadas_dict = {}
            for nf_data in dados_json.get('notas_fiscais', []):
                cnpj_limpo = re.sub(r'\D', '', nf_data.get('fornecedor_cnpj', ''))
                
                # Previne erro se a IA falhar em capturar o nome do fornecedor
                nome_forn = nf_data.get('fornecedor_nome', 'FORNECEDOR NÃO IDENTIFICADO')[:255]
                
                # Garante que o fornecedor existe no sistema
                fornecedor, _ = Fornecedor.objects.get_or_create(
                    cnpj=cnpj_limpo,
                    defaults={'nome': nome_forn}
                )
                
                # Validação de data segura
                data_emissao = nf_data.get('data_emissao')
                try:
                    datetime.strptime(data_emissao, '%Y-%m-%d')
                except (ValueError, TypeError):
                    data_emissao = datetime.now().date()
                
                # Cria ou recupera a NF
                nota, _ = NotaFiscal.objects.get_or_create(
                    termo=termo,
                    fornecedor=fornecedor,
                    numero=nf_data.get('numero', '')[:50],
                    defaults={
                        'serie': nf_data.get('serie', '')[:10],
                        'chave_acesso': nf_data.get('chave_acesso', '')[:44],
                        'data_emissao': data_emissao,
                        'valor_total': nf_data.get('valor_total') or 0.0
                    }
                )
                # Guarda a referência para vincular aos itens logo abaixo
                notas_criadas_dict[nota.numero] = nota

            # B. Processamento dos Itens Patrimoniais
            itens_salvos = 0
            for dado in dados_json.get('itens', []):
                num_ativo = dado.get('numero_ativo', '')[:50]
                
                # Evita duplicidade checando se o ativo já existe neste termo
                if num_ativo and ItemPatrimonial.objects.filter(termo=termo, numero_ativo=num_ativo).exists():
                    continue
                
                # Faz o Match da NF criada acima usando o número retornado pela IA
                nf_vinculada = notas_criadas_dict.get(dado.get('nota_fiscal_numero'))
                
                ItemPatrimonial.objects.create(
                    termo=termo,
                    numero_ativo=num_ativo,
                    descricao=dado.get('descricao', 'Sem descrição'),
                    valor_bem=dado.get('valor_bem') or 0.0,
                    nota_fiscal=nf_vinculada # Vinculação Limpa (Chave Estrangeira)
                )
                itens_salvos += 1

        if itens_salvos > 0:
            messages.success(request, f"Operação concluída! O ARGUS catalogou {len(notas_criadas_dict)} Notas Fiscais e {itens_salvos} Itens.")
        else:
            messages.info(request, "As informações lidas pela IA já constavam no sistema.")

    except Exception as e:
        messages.error(request, f"Erro crítico no salvamento automatizado: {str(e)}")

    return redirect('incorporacao:detalhe_termo', pk=pk)
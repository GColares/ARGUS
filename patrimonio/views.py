import re
from decimal import Decimal, InvalidOperation
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse  # <--- A MÁGICA DAS URLs DINÂMICAS FOI ADICIONADA AQUI
from django.db.models import Sum
from django.contrib import messages 
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics import renderSVG
from .models import VerificacaoTermo, BemPatrimonial, ItemVerificacao, FiltroImportacao
from cadastros.models import ProjetoPDI, MembroEquipe
from central_servicos.models import Ambiente
from incorporacao.models import TermoDoacao
from .extratores_faepi import extrair_linhas_brutas_faepi, limpar_lixo_digital, limpar_valor
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm


# --- PAINEL PRINCIPAL (DASHBOARD) ---
def home_patrimonio(request):
    total_equipamentos = BemPatrimonial.objects.count()
    valor_total = BemPatrimonial.objects.aggregate(Sum('valor'))['valor__sum'] or 0
    total_projetos = ProjetoPDI.objects.count()
    
    pendentes = VerificacaoTermo.objects.filter(status__in=['PENDENTE', 'EM_CONFERENCIA']).order_by('-id')
    validados = VerificacaoTermo.objects.filter(status='VALIDADO').order_by('-id')
    aprovados = VerificacaoTermo.objects.filter(status='APROVADO').order_by('-id')[:5]
    
    contexto = {
        'total_equipamentos': total_equipamentos,
        'valor_total': valor_total,
        'total_projetos': total_projetos,
        'pendentes': pendentes,
        'validados': validados,
        'aprovados': aprovados,
    }
    return render(request, 'patrimonio/home_patrimonio.html', contexto)


# --- ESTÁGIO 1: LEITURA BRUTA DO PDF ---
def importar_pdf(request):
    if request.method == 'POST':
        arquivo = request.FILES.get('arquivo_pdf')
        cabecalho = request.POST.get('linhas_cabecalho', 5)
        p_inicio = request.POST.get('pagina_inicio', 4)
        p_fim = request.POST.get('pagina_fim', 5)
        
        # 1. Verificamos explicitamente se o arquivo existe
        if not arquivo:
            messages.error(request, "Nenhum arquivo PDF foi selecionado.")
            return render(request, 'patrimonio/importar.html')

        # 2. Criamos o objeto e garantimos que a variável 'verificacao' exista
        try:
            verificacao = VerificacaoTermo.objects.create(
                numero_termo=arquivo.name, 
                termo_pdf=arquivo,
                linhas_cabecalho=int(cabecalho),
                status='PENDENTE'
            )
            
            # 3. Executamos a extração (Estágio 1)
            verificacao.dados_brutos = extrair_linhas_brutas_faepi(
                verificacao.termo_pdf.path, 
                int(cabecalho), 
                int(p_inicio), 
                int(p_fim)
            )
            verificacao.save()
            
            # 4. Redirecionamento seguro usando o namespace
            return redirect('patrimonio:conferir_importacao', verificacao_id=verificacao.id)
            
        except Exception as e:
            messages.error(request, f"Erro ao processar o PDF: {str(e)}")
            return render(request, 'patrimonio/importar.html')

    return render(request, 'patrimonio/importar.html')


# --- ESTÁGIO 2: LINHA DE MONTAGEM (CONFERÊNCIA INDIVIDUAL) ---
def conferir_importacao(request, verificacao_id):
    verificacao = get_object_or_404(VerificacaoTermo, id=verificacao_id)
    linhas_pdf = verificacao.dados_brutos or []

    if not linhas_pdf:
        verificacao.status = 'VALIDADO'
        verificacao.save()
        messages.success(request, "Conferência concluída! O termo está pronto para incorporação final.")
        return redirect('patrimonio:home_patrimonio')

    tamanho_slice = int(request.POST.get('slice', request.GET.get('slice', 3)))

    if request.method == 'POST':
        if verificacao.status == 'PENDENTE':
            verificacao.status = 'EM_CONFERENCIA'

        if 'pular' in request.POST:
            verificacao.dados_brutos = linhas_pdf[1:]
            verificacao.save()
            # CONSTRUÇÃO DINÂMICA DA URL (Fim do erro 404)
            base_url = reverse('patrimonio:conferir_importacao', args=[verificacao.id])
            return redirect(f"{base_url}?slice={tamanho_slice}")
            
        elif 'proximo' in request.POST:
            valor_limpo = limpar_valor(request.POST.get('valor', ''))
            numero_doc = request.POST.get('doc', '').strip()
            if not numero_doc or numero_doc.lower() == 'pendente':
                numero_doc = f"DOA-{verificacao.id}"

            TermoDoacao.objects.get_or_create(
                numero=numero_doc,
                defaults={
                    'projeto_vinculado': request.POST.get('proj', 'PENDENTE'),
                    'arquivo_pdf': verificacao.termo_pdf
                }
            )
            
            ItemVerificacao.objects.create(
                verificacao=verificacao,
                numero_ativo=request.POST.get('ativo', 'pendente'),
                descricao=request.POST.get('descricao', 'pendente'),
                processo_compra=request.POST.get('proc_c', 'pendente'),
                processo_pagamento=request.POST.get('proc_p', 'pendente'),
                cnpj_cpf_fornecedor=request.POST.get('cnpj', 'pendente'),
                nome_fornecedor=request.POST.get('forn', 'pendente'),
                nota_fiscal=request.POST.get('nf', 'pendente'),
                data_nf=request.POST.get('dnf', 'pendente'),
                valor_bem=valor_limpo,
                conta=request.POST.get('conta', 'pendente'),
                dv=request.POST.get('dv', 'pendente'),
                projeto=request.POST.get('proj', 'pendente'),
                localizacao=request.POST.get('loc', 'pendente'),
                situacao=request.POST.get('sit', 'pendente'),
                data_movimentacao=request.POST.get('data', 'pendente'),
                documento=numero_doc,
                erro_leitura=True if valor_limpo <= 0 else False
            )
            
            verificacao.dados_brutos = linhas_pdf[tamanho_slice:]
            verificacao.save()
            
            # CONSTRUÇÃO DINÂMICA DA URL (Fim do erro 404)
            base_url = reverse('patrimonio:conferir_importacao', args=[verificacao.id])
            return redirect(f"{base_url}?slice={tamanho_slice}")

    fatia_atual = linhas_pdf[:tamanho_slice]
    texto_fatia = "\n".join([" | ".join(l) for l in fatia_atual])

    # ---------------------------------------------------------
    # MÓDULO DE INTELIGÊNCIA: CAÇADORES SEMÂNTICOS (REGEX)
    # ---------------------------------------------------------
    
    texto_completo = " ".join([" ".join(linha) for linha in fatia_atual])
    texto_derretido = re.sub(r'[A-Za-z]', '', texto_completo)
    texto_derretido = re.sub(r'\s+', '', texto_derretido)

    # --- CAÇADOR DE ATIVO ---
    match_ativo = re.search(r'\b\d{4,6}\b', texto_completo)
    ativo_inteligente = match_ativo.group(0) if match_ativo else "pendente"

    # --- CAÇADOR DE PROCESSOS ---
    matches_proc = re.findall(r'\d{3,6}/\d{4}', texto_derretido)
    proc_compra_inteligente = matches_proc[0] if len(matches_proc) > 0 else "pendente"
    proc_pagamento_inteligente = matches_proc[1] if len(matches_proc) > 1 else "pendente"

    # --- CAÇADOR DE DESCRIÇÃO ---
    fragmentos_desc = []
    for linha in fatia_atual:
        col0 = ""
        col1 = ""
        if len(linha) > 0:
            col0 = linha[0]
            if ativo_inteligente != "pendente" and ativo_inteligente in col0:
                col0 = col0.replace(ativo_inteligente, "")
        if len(linha) > 1:
            col1 = linha[1]
            if proc_compra_inteligente != "pendente" and proc_compra_inteligente in col1:
                col1 = col1.split(proc_compra_inteligente)[0]
                
        col0_limpa = re.sub(r'[a-zà-ú]', '', col0).strip()
        col1_limpa = re.sub(r'[a-zà-ú]', '', col1).strip()
        linha_junta = col0_limpa + col1_limpa
        
        if linha_junta:
            fragmentos_desc.append(linha_junta)

    descricao_inteligente = "pendente"
    if fragmentos_desc:
        desc_bruta = " ".join(fragmentos_desc)
        descricao_inteligente = re.sub(r'\s+', ' ', desc_bruta).strip()

    # --- CAÇADOR DE CNPJ ---
    match_cnpj = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}[-‐]\d{2}', texto_derretido)
    cnpj_inteligente = match_cnpj.group(0) if match_cnpj else "pendente"

    # --- CAÇADORES DE DATA ---
    datas_encontradas = re.findall(r'\d{2}/\d{2}/\d{4}', texto_derretido)
    data_nf_inteligente = datas_encontradas[0] if len(datas_encontradas) > 0 else "pendente"
    data_movimentacao_inteligente = datas_encontradas[-1] if len(datas_encontradas) > 1 else "pendente"

    # --- CAÇADOR DE NOME DO FORNECEDOR ---
    nome_fornecedor_inteligente = "pendente"
    coluna_ancora = -1

    if cnpj_inteligente != "pendente":
        cauda_cnpj = cnpj_inteligente.split('/')[-1].replace('-', '').replace('‐', '')
        for linha in fatia_atual[:3]:
            for idx, celula in enumerate(linha):
                celula_limpa = re.sub(r'[-‐]', '', celula) 
                if cauda_cnpj in celula_limpa:
                    coluna_ancora = idx
                    break
            if coluna_ancora != -1:
                break

    if coluna_ancora == -1:
        coluna_ancora = 3

    fragmentos_forn = []
    for linha in fatia_atual:
        if len(linha) > coluna_ancora and linha[coluna_ancora].strip():
            fragmentos_forn.append(linha[coluna_ancora].strip())
        if len(linha) > (coluna_ancora + 1) and linha[coluna_ancora + 1].strip():
            fragmentos_forn.append(linha[coluna_ancora + 1].strip())

    if fragmentos_forn:
        texto_vertical_sujo = " ".join(fragmentos_forn)
        texto_sem_lixo = re.sub(r'\s*[\d\.\/]+(?:[-‐][\d\.\/]+)*\s*', '', texto_vertical_sujo)
        nome_limpo = re.sub(r'\s+', ' ', texto_sem_lixo).strip()
        
        palavras_fornecedor = [
            p for p in nome_limpo.split() 
            if len(p) > 1 or p.lower() in ['e', 'd', 'a', 'o', '-', '‐']
        ]
        if palavras_fornecedor:
            nome_fornecedor_inteligente = " ".join(palavras_fornecedor)

    # --- RASTREAMENTO GENÉRICO DA CAUDA DA TABELA ---
    fragmentos_projeto = []
    fragmentos_localizacao = []
    fragmentos_situacao = []
    fragmentos_documento = []

    for linha in fatia_atual:
        if len(linha) > 8 and linha[8].strip():
            fragmentos_projeto.append(linha[8].strip())

        loc_linha = ""
        if len(linha) > 9: loc_linha += linha[9].strip()
        if len(linha) > 10: loc_linha += linha[10].strip()
        if loc_linha:
            fragmentos_localizacao.append(loc_linha)

        if len(linha) > 11 and linha[11].strip():
            fragmentos_situacao.append(linha[11].strip())

        doc_linha = []
        if len(linha) > 12 and linha[12].strip(): doc_linha.append(linha[12].strip())
        if len(linha) > 13 and linha[13].strip(): doc_linha.append(linha[13].strip())
        if doc_linha:
            fragmentos_documento.append(" ".join(doc_linha))

    # --- MONTAGEM DO PROJETO ---
    projeto_inteligente = "pendente"
    if fragmentos_projeto:
        proj_limpo = fragmentos_projeto[0]
        proj_limpo = re.sub(r'^.*?(\d{4}[-‐]\d+)', r'IFAM \1', proj_limpo)
        
        for pedaco in fragmentos_projeto[1:]:
            if not re.search(r'[-‐]\s*$', proj_limpo):
                proj_limpo += " - " + pedaco
            else:
                proj_limpo = re.sub(r'\s*[-‐]\s*$', ' - ', proj_limpo) + pedaco
                
        projeto_inteligente = proj_limpo.replace('‐', '-')

    # --- MONTAGEM DA LOCALIZAÇÃO ---
    localizacao_inteligente = "pendente"
    if fragmentos_localizacao:
        loc_crua = " ".join(fragmentos_localizacao)
        localizacao_inteligente = re.sub(r'^[-‐\s]+', '', loc_crua)

    # --- MONTAGEM DA SITUAÇÃO ---
    situacao_inteligente = "pendente"
    if fragmentos_situacao:
        sit_crua = " ".join(fragmentos_situacao)
        situacao_inteligente = re.sub(r'[\d/]+', '', sit_crua).strip().upper()

    # --- MONTAGEM DO DOCUMENTO ---
    documento_inteligente = "pendente"
    if fragmentos_documento:
        doc_cru = " ".join(fragmentos_documento)
        
        if data_movimentacao_inteligente != "pendente":
            parte_data = data_movimentacao_inteligente.split('/')
            if len(parte_data) == 3:
                doc_cru = doc_cru.replace(f"{parte_data[1]}/{parte_data[2]}", "")
                doc_cru = doc_cru.replace(f"{int(parte_data[1])}/{parte_data[2]}", "")
                
        doc_cru = re.sub(r'(?<=\b\d)\s+(?=\d)', '', doc_cru)
        doc_limpo = re.sub(r'\s+', ' ', doc_cru).strip()
        
        if not re.search(r'nº|n\.|numero', doc_limpo, re.IGNORECASE):
             doc_limpo = re.sub(r'([a-zA-Zã-õç])\s+(\d)', r'\1 nº \2', doc_limpo)
             
        documento_inteligente = doc_limpo 

    # --- CAÇADOR DE NOTA FISCAL ---
    nota_fiscal_inteligente = "pendente"
    if data_nf_inteligente != "pendente":
        match_nf = re.search(fr'\b(\d+)\s+{re.escape(data_nf_inteligente)}', texto_completo)
        if match_nf:
            nota_fiscal_inteligente = match_nf.group(1)

    # --- CAÇADOR DE VALOR MONETÁRIO ---
    texto_limpo_para_valor = texto_derretido
    itens_capturados = datas_encontradas + matches_proc + [cnpj_inteligente]
    for item in itens_capturados:
        if item and item != "pendente":
            texto_limpo_para_valor = texto_limpo_para_valor.replace(item, "|")

    valores_encontrados = re.findall(r'\d{1,3}(?:\.\d{3})*,\d{2}', texto_limpo_para_valor)
    valor_inteligente = valores_encontrados[-1] if valores_encontrados else "0,00"

    # --- CAÇADOR DE CONTA E DV ---
    conta_inteligente = "pendente"
    dv_inteligente = "pendente"
    
    if valor_inteligente != "0,00":
        pos_valor = texto_completo.find(valor_inteligente) + len(valor_inteligente)
        trecho_posterior = texto_completo[pos_valor:].strip()
        
        palavras = trecho_posterior.split()
        fragmentos_conta = []
        
        for p in palavras:
            if p.isalpha() and len(p) > 1:
                break
            fragmentos_conta.append(p)
            
        if fragmentos_conta:
            texto_sujo = "".join(fragmentos_conta)
            texto_limpo = re.sub(r'[A-Za-z\s]', '', texto_sujo) 
            
            if len(texto_limpo) > 1:
                dv_inteligente = texto_limpo[-1]
                conta_inteligente = texto_limpo[:-1]

    # --- ODÔMETRO DE ITENS ---
    # Conta quantos itens já foram validados e salvos no banco para esta importação
    itens_salvos = ItemVerificacao.objects.filter(verificacao=verificacao).count()
    item_atual = itens_salvos + 1 # O item atual é sempre o próximo da fila    
    
    # --- RENDERIZAÇÃO DO DICIONÁRIO ---
    sugestao = {
        'ativo': ativo_inteligente,
        'descricao': descricao_inteligente,
        'proc_c': proc_compra_inteligente,
        'proc_p': proc_pagamento_inteligente,
        'cnpj': cnpj_inteligente,
        'nome_fornecedor': nome_fornecedor_inteligente,
        'data_nf': data_nf_inteligente,
        'data_movimentacao': data_movimentacao_inteligente,
        'valor': valor_inteligente,
        'nota_fiscal': nota_fiscal_inteligente,
        'conta': conta_inteligente,
        'dv': dv_inteligente,
        'proj': projeto_inteligente,
        'loc': localizacao_inteligente,
        'sit': situacao_inteligente,
        'doc': documento_inteligente,
    }

    campos_validacao = [
        {'key': 'ativo', 'label': 'Nº DO ATIVO', 'value': sugestao['ativo']},
        {'key': 'descricao', 'label': 'DESCRIÇÃO', 'value': sugestao['descricao'], 'is_textarea': True},
        {'key': 'proc_c', 'label': 'PROCESSO COMPRA', 'value': sugestao['proc_c']},
        {'key': 'proc_p', 'label': 'PROCESSO PAGAMENTO', 'value': sugestao['proc_p']},
        {'key': 'cnpj', 'label': 'CNPJ FORNECEDOR', 'value': sugestao['cnpj']},
        {'key': 'forn', 'label': 'NOME FORNECEDOR', 'value': sugestao['nome_fornecedor']},
        {'key': 'nf', 'label': 'NOTA FISCAL', 'value': sugestao['nota_fiscal']},
        {'key': 'dnf', 'label': 'DATA NF', 'value': sugestao['data_nf']},
        {'key': 'valor', 'label': 'VALOR DO BEM (R$)', 'value': sugestao['valor']},
        {'key': 'conta', 'label': 'CONTA', 'value': sugestao['conta']},
        {'key': 'dv', 'label': 'DV', 'value': sugestao['dv']},
        {'key': 'proj', 'label': 'PROJETO', 'value': sugestao['proj']},
        {'key': 'loc', 'label': 'LOCALIZAÇÃO', 'value': sugestao['loc']},
        {'key': 'sit', 'label': 'SITUAÇÃO', 'value': sugestao['sit']},
        {'key': 'data', 'label': 'DATA MOVIMENTAÇÃO', 'value': sugestao['data_movimentacao']},
        {'key': 'doc', 'label': 'DOCUMENTO (TERMO)', 'value': sugestao['doc']},
    ]

    return render(request, 'patrimonio/conferencia_itens.html', locals())

def resetar_conferencia(request, verificacao_id):
    verificacao = get_object_or_404(VerificacaoTermo, id=verificacao_id)
    verificacao.itens.all().delete()
    verificacao.dados_brutos = extrair_linhas_brutas_faepi(verificacao.termo_pdf.path, verificacao.linhas_cabecalho)
    verificacao.linha_atual = 0
    verificacao.status = 'PENDENTE'
    verificacao.save()
    messages.info(request, "Contador e Slices resetados com sucesso!")
    return redirect('patrimonio:conferir_importacao', verificacao_id=verificacao.id)

# --- INCORPORAÇÃO DEFINITIVA ---
def confirmar_importacao(request, verificacao_id):
    verificacao = get_object_or_404(VerificacaoTermo, id=verificacao_id)
    
    if verificacao.status == 'APROVADO':
        return redirect('patrimonio:relatorio_geral')

    itens_temporarios = ItemVerificacao.objects.filter(verificacao=verificacao)
    bens_para_criar = []
    
    for item in itens_temporarios:
        projeto = ProjetoPDI.objects.filter(codigo=item.projeto).first() or ProjetoPDI.objects.filter(status='ATIVO').first()
        termo = TermoDoacao.objects.filter(numero=item.documento).first()

        bens_para_criar.append(BemPatrimonial(
            patrimonio_doador=item.numero_ativo,
            descricao=item.descricao,
            valor=item.valor_bem,
            projeto=projeto,
            termo_doacao=termo,
            nota_fiscal=item.nota_fiscal,
            estado_conservacao='NOVO',
            status_operacional='ATIVO'
        ))
    
    BemPatrimonial.objects.bulk_create(bens_para_criar)
    verificacao.status = 'APROVADO'
    verificacao.save()

    messages.success(request, f"Sucesso! {len(bens_para_criar)} itens incorporados.")
    return redirect('patrimonio:relatorio_geral')


# --- HISTÓRICO E DETALHES ---
def detalhe_importacao(request, verificacao_id):
    """Exibe os itens já validados de uma importação específica"""
    verificacao = get_object_or_404(VerificacaoTermo, id=verificacao_id)
    itens = ItemVerificacao.objects.filter(verificacao=verificacao).order_by('id')
    return render(request, 'patrimonio/detalhe_importacao.html', {
        'verificacao': verificacao, 
        'itens': itens, 
        'finalizada': True
    })

# --- UTILITÁRIOS E RELATÓRIOS ---

def relatorio_geral(request):
    bens = BemPatrimonial.objects.select_related('projeto', 'termo_doacao').all().order_by('-valor')
    return render(request, 'patrimonio/relatorio.html', {
        'bens': bens,
        'total_equipamentos': bens.count(),
        'valor_total': bens.aggregate(Sum('valor'))['valor__sum'] or 0,
    })


@login_required
def conferir_bens_projeto(request, projeto_id):
    """
    Exibe a conferência física e a rastreabilidade patrimonial dos bens do projeto.
    O acesso é restrito ao superusuário ou a membros da equipe do projeto.
    """
    projeto = get_object_or_404(ProjetoPDI, id=projeto_id)

    from cadastros.models import MembroEquipe

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
    tombados_ifam = bens.filter(
        patrimonio_ifam__isnull=False,
    ).exclude(patrimonio_ifam='').count()
    pendentes_tombamento = total_itens - tombados_ifam

    contexto = {
        'projeto': projeto,
        'bens': bens,
        'total_itens': total_itens,
        'valor_total': valor_total,
        'tombados_ifam': tombados_ifam,
        'pendentes_tombamento': pendentes_tombamento,
    }
    return render(request, 'patrimonio/conferir_bens_projeto.html', contexto)


def exportar_pdf_conferencia(request, verificacao_id):
    verificacao = get_object_or_404(VerificacaoTermo, id=verificacao_id)
    itens = ItemVerificacao.objects.filter(verificacao=verificacao).order_by('id')
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Conferencia_{verificacao.id}.pdf"'
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=0.5*cm, leftMargin=0.5*cm, topMargin=1*cm, bottomMargin=1*cm)
    elements = []
    styles = getSampleStyleSheet()
    estilo_celula = styles['Normal']
    estilo_celula.fontSize = 6
    estilo_celula.leading = 7
    elements.append(Paragraph(f"Relatório de Conferência - Polo de Inovação", styles['Title']))
    elements.append(Spacer(1, 12))
    data = [['Nº Ativo', 'Descrição', 'Proc. Compra', 'CNPJ Forn.', 'NF', 'Valor', 'Conta', 'Projeto', 'Doc.']]
    for i in itens:
        data.append([
            Paragraph(i.numero_ativo, estilo_celula),
            Paragraph(i.descricao, estilo_celula),
            Paragraph(i.processo_compra, estilo_celula),
            Paragraph(i.cnpj_cpf_fornecedor, estilo_celula),
            Paragraph(i.nota_fiscal, estilo_celula),
            f"R$ {i.valor_bem:.2f}",
            Paragraph(i.conta, estilo_celula),
            Paragraph(i.projeto, estilo_celula),
            Paragraph(i.documento, estilo_celula),
        ])
    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
    ]))
    elements.append(t)
    doc.build(elements)
    response.write(buffer.getvalue())
    buffer.close()
    return response

def limpar_pendentes(request):
    if request.method == 'POST':
        VerificacaoTermo.objects.filter(status__in=['PENDENTE', 'EM_CONFERENCIA']).delete()
        messages.success(request, "Fila de conferência limpa.")
    return redirect('patrimonio:home')

def descartar_importacao(request, verificacao_id):
    get_object_or_404(VerificacaoTermo, id=verificacao_id).delete()
    messages.warning(request, "Importação descartada.")
    return redirect('patrimonio:home')

def adicionar_filtro(request):
    if request.method == 'POST':
        termo = request.POST.get('termo', '').strip().upper()
        if termo: FiltroImportacao.objects.get_or_create(termo=termo)
    return redirect(request.META.get('HTTP_REFERER', 'patrimonio:home'))

def gerenciar_filtros(request):
    filtros = FiltroImportacao.objects.all().order_by('termo')
    return render(request, 'patrimonio/gerenciar_filtros.html', {'filtros': filtros})


# ── FUNÇÕES AUXILIARES E VIEWS DE ETIQUETAS PATRIMONIAIS (Fase 5 / Etapa 5.3) ──

def gerar_qr_code_svg(payload: str, tamanho: int = 90) -> str:
    """
    Gera QR Code vetorial puro em formato SVG usando o backend nativo do ReportLab.
    Não requer Cairo, libpng ou extensões C compiladas.
    Retorna apenas a tag <svg ...>...</svg> para inserção segura no HTML.
    """
    widget = QrCodeWidget(payload)
    widget.barWidth = tamanho
    widget.barHeight = tamanho
    drawing = Drawing(tamanho, tamanho)
    drawing.add(widget)
    svg_raw = renderSVG.drawToString(drawing)
    idx_start = svg_raw.find('<svg')
    if idx_start != -1:
        return svg_raw[idx_start:]
    return svg_raw


def usuario_pode_gerar_etiqueta_bem(user, bem: BemPatrimonial) -> bool:
    """
    Verifica alçada RBAC para emissão da etiqueta de um bem patrimonial:
    - Superusuário ou Staff;
    - Servidor Efetivo com SIAPE ativo (Canônico: PessoaFisica + PerfilServidor);
    - Servidor Efetivo com SIAPE ativo (Legado: PerfilUsuario.vinculo == 'SERVIDOR');
    - Coordenador do Projeto vinculado ao bem;
    - Membro ativo da equipe do projeto.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    # Servidor com SIAPE ativo (Canônico)
    pf = getattr(user, 'pessoa_fisica', None)
    if pf and hasattr(pf, 'perfil_servidor') and pf.perfil_servidor.ativo and pf.perfil_servidor.siape:
        return True
    # Servidor com SIAPE ativo (Legado Almoxarifado)
    perfil_legado = getattr(user, 'perfil', None)
    if perfil_legado and getattr(perfil_legado, 'vinculo', None) == 'SERVIDOR' and getattr(perfil_legado, 'siape', None):
        return True
    # Vínculo com Projeto P&D
    if bem.projeto:
        if bem.projeto.coordenador and bem.projeto.coordenador.user_id == user.id:
            return True
        if MembroEquipe.objects.filter(projeto=bem.projeto, usuario=user).exists():
            return True
    return False


def usuario_pode_gerar_etiquetas_ambiente(user, ambiente: Ambiente) -> bool:
    """
    Verifica alçada RBAC para emissão em lote de etiquetas de um ambiente inteiro:
    - Superusuário ou Staff;
    - Servidor Efetivo com SIAPE ativo (Canônico ou Legado).
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    pf = getattr(user, 'pessoa_fisica', None)
    if pf and hasattr(pf, 'perfil_servidor') and pf.perfil_servidor.ativo and pf.perfil_servidor.siape:
        return True
    perfil_legado = getattr(user, 'perfil', None)
    if perfil_legado and getattr(perfil_legado, 'vinculo', None) == 'SERVIDOR' and getattr(perfil_legado, 'siape', None):
        return True
    return False


@login_required
def gerar_etiqueta_patrimonial(request, bem_id):
    """View para emissão de etiqueta patrimonial individual com QR Code vetorial."""
    bem = get_object_or_404(BemPatrimonial, id=bem_id)
    if not usuario_pode_gerar_etiqueta_bem(request.user, bem):
        raise PermissionDenied("Acesso restrito à gestão patrimonial ou equipe do projeto.")
    identificador = bem.patrimonio_ifam or bem.patrimonio_doador or f"ID-{bem.id}"
    payload_qr = f"ARGUS-BEM:{identificador}|{bem.descricao[:40]}"
    qr_svg = gerar_qr_code_svg(payload_qr)
    itens = [{
        'bem': bem,
        'identificador': identificador,
        'qr_svg': qr_svg,
    }]
    contexto = {
        'itens': itens,
        'titulo': f"Etiqueta Patrimonial - {identificador}",
        'subtitulo': "Impressão individual de etiqueta de tombamento",
        'modo_lote': False,
    }
    return render(request, 'patrimonio/etiqueta_patrimonial.html', contexto)


@login_required
def gerar_etiquetas_ambiente(request, ambiente_id):
    """View para emissão em lote de etiquetas de todos os bens alocados em um ambiente/laboratório."""
    ambiente = get_object_or_404(Ambiente, id=ambiente_id)
    if not usuario_pode_gerar_etiquetas_ambiente(request.user, ambiente):
        raise PermissionDenied("Acesso restrito à equipe técnica ou servidores efetivos.")
    bens = BemPatrimonial.objects.filter(ambiente=ambiente).order_by('id')
    itens = []
    for bem in bens:
        identificador = bem.patrimonio_ifam or bem.patrimonio_doador or f"ID-{bem.id}"
        payload_qr = f"ARGUS-BEM:{identificador}|{bem.descricao[:40]}"
        qr_svg = gerar_qr_code_svg(payload_qr)
        itens.append({
            'bem': bem,
            'identificador': identificador,
            'qr_svg': qr_svg,
        })
    contexto = {
        'itens': itens,
        'ambiente': ambiente,
        'titulo': f"Etiquetas - {ambiente.nome}",
        'subtitulo': f"Lote de etiquetas dos bens alocados no ambiente ({len(itens)} itens)",
        'modo_lote': True,
    }
    return render(request, 'patrimonio/etiqueta_patrimonial.html', contexto)
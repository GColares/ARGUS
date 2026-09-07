# almoxarifado/views.py
import os
import tempfile
from decimal import Decimal
# pyrefly: ignore [untyped-import]
from django.shortcuts import render, redirect, get_object_or_404
# pyrefly: ignore [untyped-import]
from django.contrib.auth.decorators import login_required
# pyrefly: ignore [untyped-import]
from django.contrib import messages
# pyrefly: ignore [untyped-import]
from django.db import transaction
# pyrefly: ignore [untyped-import]
from django.db.models import Q, Count, Sum
# pyrefly: ignore [untyped-import]
from django.utils import timezone
# pyrefly: ignore [untyped-import]
from django.db.models.functions import Length

# Nossos módulos locais do ARGUS
from cadastros.models import Fornecedor
from .models import NotaFiscalAlmoxarifado, ProdutoAlmoxarifado, CotaDiariaIA, FotoProduto, ProjetoPDI
from .documentos import construir_csv_categoria, construir_csv_notas, construir_termo_docx
from .services import processar_nfe_com_gemini
from cadastros.decorators import servidor_efetivo_required
# pyrefly: ignore [untyped-import]
from django.contrib.auth.models import User

# ==============================================================================
# PAINEL (HOME) E LISTAGEM
# ==============================================================================

@login_required
def home_almoxarifado(request):
    """
    Dashboard executivo do Almoxarifado.
    Calcula as métricas financeiras, quantitativas e limites da IA.
    """
    # 1. BLOCO: Indicadores Principais
    # pyrefly: ignore [missing-attribute]
    total_notas = NotaFiscalAlmoxarifado.objects.count()
    # pyrefly: ignore [missing-attribute]
    total_produtos = ProdutoAlmoxarifado.objects.count()

    # O Django Sum retorna None se não houver registros.
    # Usamos agregação múltipla para ir ao banco de dados apenas uma vez (Performance).
    agregados = NotaFiscalAlmoxarifado.objects.aggregate(
        liq=Sum('valor_total_nota'),
        bruto=Sum('valor_total_produtos'),
        desc=Sum('valor_desconto')
    )

    # Blindagem: Converte NoneType para Decimal('0.00')
    v_liq = agregados['liq'] or Decimal('0.00')
    v_bruto = agregados['bruto'] or Decimal('0.00')
    v_desc = agregados['desc'] or Decimal('0.00')
    
    indicadores = {
        'total_notas': total_notas,
        'total_produtos': total_produtos,
        'valor_acumulado': v_liq,
        'valor_produtos': v_bruto,
        'valor_desconto': v_desc,
    }

    # 2. BLOCO: Cota IA (Barra de Progresso)
    hoje = timezone.now().date()
    cota_hoje, _ = CotaDiariaIA.objects.get_or_create(data=hoje)
    
    percentual_cota = 0
    if cota_hoje.limite_diario > 0:
        percentual_cota = (cota_hoje.requisicoes_feitas / cota_hoje.limite_diario) * 100

    # 3. BLOCO: Gestão de Fornecedores
    total_fornecedores = NotaFiscalAlmoxarifado.objects.values('fornecedor_id').distinct().count()
    total_itens_venda = ProdutoAlmoxarifado.objects.aggregate(total=Sum('quantidade'))['total'] or Decimal('0.00')

    dados_fornecedores = {
        'total_fornecedores': total_fornecedores,
        'valor_total_vendas': v_liq,  # Sincronizado com o total líquido (o que o IFAM efetivamente pagou)
        'total_itens_venda': total_itens_venda,
    }

    # 4. BLOCO: Investimento por Categoria
    # Agrupa os produtos no banco de dados por categoria e soma valores e quantidades
    estoque_qs = ProdutoAlmoxarifado.objects.values('categoria').annotate(
        qtd=Count('id'),
        valor=Sum('valor_total')
    )
    
    # Dicionário para traduzir o código do banco para o nome amigável da tela
    mapa_nomes = {
        'CONSUMO': 'Material de Consumo',
        'PERMANENTE': 'Material Permanente',
        'SERVICO': 'Serviços'
    }
    
    estoque_por_categoria = []
    for item in estoque_qs:
        cat_codigo = item['categoria']
        estoque_por_categoria.append({
            'codigo': cat_codigo,
            'nome_amigavel': mapa_nomes.get(cat_codigo, cat_codigo),
            'qtd': item['qtd'],
            'valor': item['valor'] or Decimal('0.00')
        })

    # Prepara a "maleta" de dados com os nomes exatos que o seu HTML exige
    contexto = {
        'indicadores': indicadores,
        'cota_hoje': cota_hoje,
        'percentual_cota': round(percentual_cota),
        'dados_fornecedores': dados_fornecedores,
        'estoque_por_categoria': estoque_por_categoria
    }
    
    return render(request, 'almoxarifado/home_almoxarifado.html', contexto)

@login_required
def lista_notas_almoxarifado(request):
    """
    Página dedicada à malha de listagem, paginação e filtros complexos.
    """
    # 1. CAPTURA DOS PARÂMETROS DA URL
    sort_param = request.GET.get('sort', '-data_emissao')
    busca = request.GET.get('q', '').strip()
    filtro_projeto = request.GET.get('projeto', '')
    filtro_recebedor = request.GET.get('recebedor', '')
    filtro_rec_inicio = request.GET.get('data_rec_inicio', '')
    filtro_rec_fim = request.GET.get('data_rec_fim', '')
    filtro_imp_inicio = request.GET.get('data_imp_inicio', '')
    filtro_imp_fim = request.GET.get('data_imp_fim', '')
    filtro_rme = request.GET.get('status_rme', '')

    # Tratamento de compatibilidade para ordenação do novo modelo relacional
    if sort_param == 'fornecedor_nome' or sort_param == 'fornecedor__nome':
        sort_param = 'fornecedor__nome'
    elif sort_param == '-fornecedor_nome' or sort_param == '-fornecedor__nome':
        sort_param = '-fornecedor__nome'

    # 2. QUERYSET BASE E ANOTAÇÃO MATEMÁTICA
    notas = NotaFiscalAlmoxarifado.objects.all().annotate(num_itens=Count('produtos'))

    # 3. APLICAÇÃO DOS FILTROS DO USUÁRIO
    if busca:
        notas = notas.filter(
            Q(produtos__descricao__icontains=busca) |
            Q(produtos__categoria__icontains=busca) |
            Q(fornecedor__nome__icontains=busca) | 
            Q(numero__icontains=busca)
        ).distinct()

    if filtro_projeto:
        notas = notas.filter(projeto_vinculado_id=filtro_projeto)
    if filtro_recebedor:
        notas = notas.filter(usuario_recebedor_id=filtro_recebedor)
    if filtro_rec_inicio:
        notas = notas.filter(data_recebimento__gte=filtro_rec_inicio)
    if filtro_rec_fim:
        notas = notas.filter(data_recebimento__lte=filtro_rec_fim)
    if filtro_imp_inicio:
        notas = notas.filter(data_importacao__date__gte=filtro_imp_inicio)
    if filtro_imp_fim:
        notas = notas.filter(data_importacao__date__lte=filtro_imp_fim)
        
    if filtro_rme == 'pendente':
        notas = notas.filter(Q(termo_recebimento_assinado='') | Q(termo_recebimento_assinado__isnull=True))
    elif filtro_rme == 'arquivado':
        notas = notas.exclude(Q(termo_recebimento_assinado='') | Q(termo_recebimento_assinado__isnull=True))

    # 4. CONTAGEM EXATA APÓS FILTROS
    total_notas = notas.count()

    # 5. APLICA ORDENAÇÃO FINAL
    if sort_param == 'numero':
        notas = notas.annotate(numero_len=Length('numero')).order_by('numero_len', 'numero')
    elif sort_param == '-numero':
        notas = notas.annotate(numero_len=Length('numero')).order_by('-numero_len', '-numero')
    elif sort_param:
        notas = notas.order_by(sort_param)

    # 6. CONTEXTO ÚNICO PARA O HTML
    contexto = {
        'notas': notas,
        'total_notas': total_notas,
        'busca': busca,
        'filtro_projeto': filtro_projeto,
        'filtro_recebedor': filtro_recebedor,
        'filtro_rec_inicio': filtro_rec_inicio,
        'filtro_rec_fim': filtro_rec_fim,
        'filtro_imp_inicio': filtro_imp_inicio,
        'filtro_imp_fim': filtro_imp_fim,
        'filtro_rme': filtro_rme,
        'current_sort': sort_param, 
    }
    
    return render(request, 'almoxarifado/lista_notas.html', contexto)

# ==============================================================================
# IMPORTAÇÃO E GESTÃO DE NOTAS (CRUD)
# ==============================================================================

@login_required
def importar_nfe(request):
    """Processa o upload do ficheiro digital da NF-e (PDF) com a Inteligência Artificial."""
    if request.method == 'POST' and request.FILES.get('arquivo_pdf'):
        arquivo = request.FILES['arquivo_pdf']
        
        if not arquivo.name.endswith('.pdf'):
            messages.error(request, "Formato inválido. Aceitamos apenas ficheiros PDF.")
            return redirect('almoxarifado:lista_notas')

        temp_path = None
        try:
            # 1. Guarda num ficheiro temporário apenas para o Gemini conseguir ler
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                for chunk in arquivo.chunks():
                    temp_file.write(chunk)
                temp_path = temp_file.name

            with transaction.atomic():
                # 2. O Gemini processa o texto e cria a nota no banco de dados
                nota = processar_nfe_com_gemini(temp_path, request.user)
                nota.arquivo_pdf = arquivo
                nota.save()
                
            messages.success(request, f"NF-e nº {nota.numero} importada com sucesso!")
            return redirect('almoxarifado:lista_notas')
            
        except Exception as e:
            messages.error(request, f"Falha ao processar NF-e: {str(e)}")
            return redirect('almoxarifado:lista_notas')
            
        finally:
            # 3. Limpa apenas o ficheiro temporário (o ficheiro real já foi guardado pelo Django)
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                    
    return render(request, 'almoxarifado/importar.html')


@login_required
def detalhe_nota_almoxarifado(request, pk):
    """Exibe os detalhes de uma nota fiscal específica."""
    nota = get_object_or_404(NotaFiscalAlmoxarifado, pk=pk)
    
    # 1. Busca todos os usuários ativos para preencher o select de "Recebedor"
    usuarios = User.objects.filter(is_active=True).order_by('first_name')
    
    # 2. Busca todos os projetos para preencher o select de "Projeto Vinculado"
    # IMPORTANTE: Substitua 'Projeto' pelo nome exato do Model que você criou para os projetos
    projetos_lista = ProjetoPDI.objects.all().order_by('nome')


    # =====================================================================
    # LÓGICA DE NAVEGAÇÃO (ANTERIOR / PRÓXIMA)
    # Pula automaticamente IDs que tenham sido excluídos do banco
    # =====================================================================
    nota_anterior = NotaFiscalAlmoxarifado.objects.filter(id__lt=nota.id).order_by('-id').first()
    proxima_nota = NotaFiscalAlmoxarifado.objects.filter(id__gt=nota.id).order_by('id').first()
    
    contexto = {
        'nota': nota,
        'usuarios_cadastrados': usuarios,
        'projetos': projetos_lista,
        'nota_anterior': nota_anterior,
        'proxima_nota': proxima_nota,
    }
    
    return render(request, 'almoxarifado/detalhe_nota.html', contexto)


@login_required
def editar_nota_almoxarifado(request, pk):
    """Retifica a capa da Nota Fiscal (incluindo auditoria e projetos)."""
    nota = get_object_or_404(NotaFiscalAlmoxarifado, pk=pk)

    if request.method == 'POST':
        # Dados Fiscais Básicos
        nota.numero = request.POST.get('numero', nota.numero).strip()
        nota.serie = request.POST.get('serie', nota.serie).strip()
        nota.data_emissao = request.POST.get('data_emissao', nota.data_emissao)
        
        # ATUALIZADO: Captura os 3 campos financeiros novos usando Decimal
        v_produtos = request.POST.get('valor_total_produtos')
        v_desconto = request.POST.get('valor_desconto')
        v_nota = request.POST.get('valor_total_nota')
        
        if v_produtos:
            nota.valor_total_produtos = Decimal(v_produtos.replace(',', '.'))
        if v_desconto:
            nota.valor_desconto = Decimal(v_desconto.replace(',', '.'))
        if v_nota:
            nota.valor_total_nota = Decimal(v_nota.replace(',', '.'))
            
        forn_nome_post = request.POST.get('fornecedor_nome', '')
        forn_cnpj_post = request.POST.get('fornecedor_cnpj', '')
        if forn_cnpj_post:
            import re
            cnpj_limpo = re.sub(r'\D', '', forn_cnpj_post)
            if cnpj_limpo:
                from cadastros.models import Fornecedor
                forn_obj, _ = Fornecedor.objects.get_or_create(
                    cnpj=cnpj_limpo,
                    defaults={'nome': forn_nome_post.strip() or 'NÃO IDENTIFICADO'}
                )
                nota.fornecedor = forn_obj
        nota.destinatario_nome = request.POST.get('destinatario_nome', nota.destinatario_nome).strip()
        nota.destinatario_cnpj = request.POST.get('destinatario_cnpj', nota.destinatario_cnpj).strip()
        
        # Dados de Recebimento e Auditoria (Novos Campos do Modal)
        chave = request.POST.get('chave_acesso', '')
        nota.chave_acesso = chave.replace(' ', '')  # Remove a máscara do JS antes de salvar
        
        data_rec = request.POST.get('data_recebimento')
        if data_rec:
            nota.data_recebimento = data_rec

        # Relacionamentos (Chaves Estrangeiras)
        usr_id = request.POST.get('usuario_recebedor_id')
        nota.usuario_recebedor_id = usr_id if usr_id else None

        proj_id = request.POST.get('projeto_vinculado_id')
        nota.projeto_vinculado_id = proj_id if proj_id else None

        # Validação extra do Django via clean (se der erro matemático, o Django captura aqui)
        try:
            nota.clean()
            nota.save()
            messages.success(request, f"NF-e #{nota.numero} retificada com sucesso!")
        except Exception as e:
            messages.error(request, f"Erro ao salvar: {str(e)}")
        
        # Como estamos num modal na tela de detalhes, recarregamos a própria tela
        return redirect('almoxarifado:detalhe_nota', pk=nota.id)

    # Para GET, como é modal, basta redirecionar de volta aos detalhes
    return redirect('almoxarifado:detalhe_nota', pk=nota.id)


@login_required
@servidor_efetivo_required
def excluir_nota_almoxarifado(request, pk):
    """
    Remove uma Nota Fiscal e seus insumos. Protegido pela regra do SIAPE.
    Nome alinhado com a URL 'excluir_nota'.
    """
    nota = get_object_or_404(NotaFiscalAlmoxarifado, pk=pk)
    
    if request.method == 'POST':
        numero_da_nota = nota.numero
        nota.delete()
        messages.success(request, f"Nota Fiscal nº {numero_da_nota} excluída.")
        return redirect('almoxarifado:lista_notas')
        
    return render(request, 'almoxarifado/confirmar_exclusao.html', {'nota': nota})

# ==============================================================================
# GESTÃO DE INSUMOS (PRODUTOS) E FOTOS
# ==============================================================================

@login_required
def editar_produto_almoxarifado(request, produto_id):
    """Edita um produto específico aninhado na nota."""
    produto = get_object_or_404(ProdutoAlmoxarifado, pk=produto_id)

    if request.method == 'POST':
        # Captura os textos
        produto.descricao = request.POST.get('descricao', produto.descricao).strip()
        produto.categoria = request.POST.get('categoria', produto.categoria)
        produto.unidade_comercial = request.POST.get('unidade_comercial', produto.unidade_comercial).strip()

        # ATUALIZAÇÃO: Captura e converte os números decimais usando Decimal (Segurança Financeira)
        qtd = request.POST.get('quantidade')
        v_unit = request.POST.get('valor_unitario')
        v_total = request.POST.get('valor_total')

        if qtd:
            produto.quantidade = Decimal(qtd.replace(',', '.'))
        if v_unit:
            produto.valor_unitario = Decimal(v_unit.replace(',', '.'))
        if v_total:
            produto.valor_total = Decimal(v_total.replace(',', '.'))

        produto.save()
        messages.success(request, f"Insumo #{produto.numero_item} atualizado.")
        
        # Recarrega a página de detalhes da nota
        return redirect('almoxarifado:detalhe_nota', pk=produto.nota_fiscal.id)

    return redirect('almoxarifado:detalhe_nota', pk=produto.nota_fiscal.id)

@login_required
def upload_foto_produto(request, produto_id):
    """Faz o upload de imagens atreladas a um produto para a matriz documental."""
    produto = get_object_or_404(ProdutoAlmoxarifado, pk=produto_id)

    if request.method == 'POST' and request.FILES.get('foto'):
        arquivo_imagem = request.FILES['foto']
        descricao_foto = request.POST.get('descricao_foto', 'Foto do Insumo')
        
        # Cria e salva a imagem vinculada ao produto no banco de dados
        FotoProduto.objects.create(
            produto=produto,
            imagem=arquivo_imagem,
            descricao=descricao_foto if descricao_foto else None
        )
        
        messages.success(request, "Fotografia arquivada com sucesso!")
        return redirect('almoxarifado:detalhe_nota', pk=produto.nota_fiscal.id)
        
    messages.error(request, "Nenhum arquivo de imagem válido foi enviado.")
    return redirect('almoxarifado:detalhe_nota', pk=produto.nota_fiscal.id)

@login_required
def excluir_foto_produto(request, foto_id):
    """Exclui o registro da foto e o arquivo físico do servidor."""
    foto = get_object_or_404(FotoProduto, pk=foto_id)
    
    # Precisamos do ID da nota antes de apagar a foto para saber para onde redirecionar
    nota_id = foto.produto.nota_fiscal.id

    if request.method == 'POST':
        # 1. Apaga o arquivo físico do disco de forma segura
        if foto.imagem:
            caminho_arquivo = foto.imagem.path
            if os.path.exists(caminho_arquivo):
                os.remove(caminho_arquivo)
        
        # 2. Apaga o registro no banco de dados
        foto.delete()
        messages.success(request, "Fotografia excluída com sucesso.")

    return redirect('almoxarifado:detalhe_nota', pk=nota_id)

# ==============================================================================
# GERAÇÃO DE RELATÓRIOS E EXPORTAÇÕES (CLEAN ARCHITECTURE)
# ==============================================================================

@login_required
def relatorio_categoria(request, categoria_codigo):
    """Exibe os dados de estoque filtrados por uma categoria específica."""
    produtos = ProdutoAlmoxarifado.objects.filter(categoria=categoria_codigo)
    contexto = {'produtos': produtos, 'categoria': categoria_codigo}
    return render(request, 'almoxarifado/relatorio_categoria.html', contexto)

@login_required
def exportar_csv_categoria(request, categoria_codigo):
    """Exporta CSV de insumos filtrados por Categoria."""
    produtos = ProdutoAlmoxarifado.objects.filter(categoria=categoria_codigo).order_by('-nota_fiscal__data_emissao')
    return construir_csv_categoria(produtos, categoria_codigo)

@login_required
def exportar_csv_notas(request):
    """Exporta CSV filtrado da malha geral de Notas."""
    notas = NotaFiscalAlmoxarifado.objects.all().prefetch_related('produtos', 'projeto_vinculado', 'usuario_recebedor')
    return construir_csv_notas(notas)

@login_required
@servidor_efetivo_required
def gerar_termo_recebimento_docx(request, pk):
    """Dispara o download do Termo de Recebimento Provisório no formato Word."""
    nota = get_object_or_404(NotaFiscalAlmoxarifado, pk=pk)

    if nota.termo_recebimento_assinado:
        messages.warning(request, "Ação bloqueada: Esta nota já possui um Termo Assinado arquivado de forma definitiva.")
        return redirect('almoxarifado:detalhe_nota', pk=nota.id)

    return construir_termo_docx(nota, request.user)

@login_required
@servidor_efetivo_required
def anexar_termo_assinado(request, pk):
    """Recebe e arquiva o PDF do Termo de Recebimento já assinado."""
    nota = get_object_or_404(NotaFiscalAlmoxarifado, pk=pk)

    if request.method == 'POST' and request.FILES.get('termo_pdf'):
        arquivo = request.FILES['termo_pdf']
        
        # Trava de segurança para garantir que é PDF
        if not arquivo.name.lower().endswith('.pdf'):
            messages.error(request, "Formato inválido. O Termo assinado deve ser obrigatoriamente um arquivo PDF.")
            return redirect('almoxarifado:detalhe_nota', pk=nota.id)

        nota.termo_recebimento_assinado = arquivo
        nota.save()
        
        messages.success(request, "Termo de Recebimento arquivado com sucesso! O ciclo desta nota foi selado.")
        
    return redirect('almoxarifado:detalhe_nota', pk=nota.id)

@login_required
@servidor_efetivo_required
def visualizar_termo_rme(request, pk):
    """
    Renderiza a tela oficial do Termo RME (Recebimento de Material e Equipamento).
    Formato otimizado para impressão (A4).
    """
    nota = get_object_or_404(NotaFiscalAlmoxarifado, pk=pk)
    
    # Lógica de agrupamento de categorias para o texto da declaração
    # pyrefly: ignore [missing-attribute]
    categorias = nota.produtos.values_list('categoria', flat=True).distinct()
    
    if 'PERMANENTE' in categorias and 'CONSUMO' in categorias:
        bens_texto = "os equipamentos e materiais novos"
    elif 'PERMANENTE' in categorias:
        bens_texto = "os equipamentos novos, em perfeitas condições de funcionamento"
    else:
        bens_texto = "os materiais novos"
        
    recebedor_fisico_texto = "Não identificado"
    if nota.usuario_recebedor:
        vinculo_desc = ""
        if hasattr(nota.usuario_recebedor, 'perfil') and nota.usuario_recebedor.perfil:
            vinculo_desc = f" ({nota.usuario_recebedor.perfil.get_vinculo_display()})"
        recebedor_fisico_texto = f"{nota.usuario_recebedor.get_full_name() or nota.usuario_recebedor.username}{vinculo_desc}"

    declaracao = (
        f"Declaramos que recebemos os itens acima descritos, em conformidade com a nota "
        f"fiscal correspondente, encontrando-se {bens_texto}, sem avarias aparentes no "
        f"momento do recebimento. "
        f"O recebimento físico dos materiais foi realizado por {recebedor_fisico_texto}."
    )
    
    from .forms import UploadTermoAssinadoForm
    form_upload = UploadTermoAssinadoForm()
    # pyrefly: ignore [missing-attribute]
    tem_fotos = any(item.fotos.exists() for item in nota.produtos.all())
    
    contexto = {
        'nota': nota,
        'declaracao': declaracao,
        'agora': timezone.now(),
        'form_upload': form_upload,
        'servidor_verificador': request.user,
        'tem_fotos': tem_fotos,
    }
    
    return render(request, 'almoxarifado/termo_rme.html', contexto)
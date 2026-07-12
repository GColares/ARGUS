# almoxarifado/documentos.py

import os
import io
import csv
from datetime import datetime
# pyrefly: ignore [missing-import, untyped-import]
from django.conf import settings
# pyrefly: ignore [missing-import, untyped-import]
from django.http import HttpResponse
# pyrefly: ignore [missing-import]
from docxtpl import DocxTemplate, InlineImage
# pyrefly: ignore [missing-import]
from docx.shared import Cm

def construir_csv_categoria(produtos, categoria_codigo):
    """Gera a estrutura e resposta HTTP do CSV por Categoria."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    data_str = datetime.now().strftime('%Y-%m-%d')
    response['Content-Disposition'] = f'attachment; filename="argus_estoque_{categoria_codigo.lower()}_{data_str}.csv"'
    
    # Força o Excel do Windows a abrir o arquivo direto em UTF-8
    response.write('\ufeff'.encode('utf-8'))
    writer = csv.writer(response, delimiter=';')
    
    writer.writerow(['Item Num', 'NF-e', 'Fornecedor / Emitente', 'Descrição do Produto', 'Unidade', 'Quantidade', 'Valor Unitário (R$)', 'Valor Total (R$)'])
    
    for item in produtos:
        qtd_fmt = str(item.quantidade).replace('.', ',')
        unit_fmt = str(item.valor_unitario).replace('.', ',')
        total_fmt = str(item.valor_total).replace('.', ',')
        
        writer.writerow([
            item.numero_item,
            item.nota_fiscal.numero,
            item.nota_fiscal.fornecedor.nome if item.nota_fiscal.fornecedor else "Não identificado",
            item.descricao,
            item.unidade_comercial,
            qtd_fmt,
            unit_fmt,
            total_fmt
        ])
    return response

def construir_csv_notas(notas):
    """Gera a estrutura e resposta HTTP do CSV consolidado de Notas (Filtros Avançados)."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="argus_relatorio_filtrado.csv"'
    response.write('\ufeff'.encode('utf-8'))
    writer = csv.writer(response, delimiter=';')
    
    writer.writerow([
        'Número NF-e', 'Série', 'Data de Emissão', 'Data Importação', 'Projeto PDI', 'Fornecedor', 'CNPJ Fornecedor', 
        'Valor Total Nota (R$)', 'Recebido Por', 'Data Entrega', 'Descrição do Insumo', 'Categoria', 'Quantidade', 'Valor Total Item (R$)'
    ])
    
    for nota in notas:
        data_fmt = nota.data_emissao.strftime('%d/%m/%Y') if nota.data_emissao else ''
        data_imp_fmt = nota.data_importacao.strftime('%d/%m/%Y %H:%M') if nota.data_importacao else ''
        data_rec_fmt = nota.data_recebimento.strftime('%d/%m/%Y') if nota.data_recebimento else 'Não Informado'
        proj_txt = nota.projeto_vinculado.nome if nota.projeto_vinculado else 'Nenhum'
        user_txt = nota.usuario_recebedor.get_full_name() if nota.usuario_recebedor else 'Não Informado'
        val_nota_fmt = str(nota.valor_total).replace('.', ',')
        
        for item in nota.produtos.all():
            writer.writerow([
                nota.numero, nota.serie, data_fmt, data_imp_fmt, proj_txt, nota.fornecedor.nome if nota.fornecedor else "", nota.fornecedor.cnpj if nota.fornecedor else "", val_nota_fmt,
                user_txt, data_rec_fmt, item.descricao, item.get_categoria_display(), str(item.quantidade).replace('.', ','), str(item.valor_total).replace('.', ',')
            ])
    return response

def construir_termo_docx(nota, servidor_verificador):
    """Orquestra a injeção de dados no template do Word (Termo de Recebimento)."""
    caminho_matriz = os.path.join(str(settings.BASE_DIR), 'cadastros', 'modelos', 'matriz_rme.docx')
    doc = DocxTemplate(caminho_matriz)
    
    categorias = nota.produtos.values_list('categoria', flat=True).distinct()
    
    if 'PERMANENTE' in categorias and 'CONSUMO' in categorias:
        bens_texto = "os equipamentos e materiais novos"
    elif 'PERMANENTE' in categorias:
        bens_texto = "os equipamentos novos, em perfeitas condições de funcionamento"
    else:
        bens_texto = "os materiais novos"

    linhas_objeto = []
    for item in nota.produtos.all():
        qtd = f"{item.quantidade:.4f}".rstrip('0').rstrip('.')
        linhas_objeto.append(f"• {qtd} {item.unidade_comercial} - {item.descricao}")
    
    objeto_texto = "\n".join(linhas_objeto)
    
    recebedor_fisico_texto = "Não identificado"
    if nota.usuario_recebedor:
        vinculo_desc = ""
        if hasattr(nota.usuario_recebedor, 'perfil') and nota.usuario_recebedor.perfil:
            vinculo_desc = f" ({nota.usuario_recebedor.perfil.get_vinculo_display()})"
        recebedor_fisico_texto = f"{nota.usuario_recebedor.get_full_name() or nota.usuario_recebedor.username}{vinculo_desc}"

    texto_declaracao = (
        f"Declaramos que recebemos os itens acima descritos, em conformidade com a nota "
        f"fiscal correspondente, encontrando-se {bens_texto}, sem avarias aparentes no "
        f"momento do recebimento. "
        f"O recebimento físico dos materiais foi realizado por {recebedor_fisico_texto}."
    )

    nome_rec = "_________________________"
    id_rec = "SIAPE:                               "
    cargo_rec = ""
    
    if servidor_verificador:
        nome_rec = servidor_verificador.get_full_name() or servidor_verificador.username
        if hasattr(servidor_verificador, 'perfil') and servidor_verificador.perfil:
            if servidor_verificador.perfil.vinculo == 'SERVIDOR' and servidor_verificador.perfil.siape:
                id_rec = f"SIAPE: {servidor_verificador.perfil.siape}"
            if servidor_verificador.perfil.cargo:
                cargo_rec = servidor_verificador.perfil.cargo

    lista_fotos = []
    for produto in nota.produtos.all():
        for foto in produto.fotos.all():
            if foto.imagem and os.path.exists(foto.imagem.path):
                try:
                    img_inline = InlineImage(doc, foto.imagem.path, width=Cm(6))
                    lista_fotos.append({
                        'imagem': img_inline,
                        'legenda': f"Item {produto.numero_item}: {produto.descricao}"
                    })
                except Exception:
                    pass

    projeto_str = nota.projeto_vinculado.nome if nota.projeto_vinculado else "Não vinculado"
    if nota.projeto_vinculado and hasattr(nota.projeto_vinculado, 'processo') and nota.projeto_vinculado.processo:
        projeto_str += f" (Processo: {nota.projeto_vinculado.processo})"

    contexto = {
        'objeto': objeto_texto,
        'quantidade_total': f"{nota.produtos.count()} item(ns) discriminado(s)",
        'projeto': projeto_str,
        'numero_nota': nota.numero,
        'serie_nota': nota.serie,
        'fornecedor': nota.fornecedor.nome if nota.fornecedor else "Não identificado",
        'cnpj_fornecedor': nota.fornecedor.cnpj if nota.fornecedor else "Não identificado",
        'destinatario': f"{nota.destinatario_nome} (CNPJ: {nota.destinatario_cnpj})",
        'chave_acesso': nota.chave_acesso if nota.chave_acesso else "Não informada",
        'texto_declaracao': texto_declaracao,
        'nome_recebedor': nome_rec,
        'id_recebedor': id_rec,
        'cargo_recebedor': cargo_rec,
        'lista_fotos': lista_fotos,
    }

    doc.render(contexto)
    f = io.BytesIO()
    doc.save(f)
    f.seek(0)
    
    response = HttpResponse(
        f.read(), 
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    response['Content-Disposition'] = f'attachment; filename="Termo_Recebimento_NFe_{nota.numero}.docx"'
    return response
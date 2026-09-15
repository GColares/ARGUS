# -*- coding: utf-8 -*-
"""
Gerador de Recibos e Termos de Cautela em PDF (ReportLab).
Emite documentos oficiais com layout institucional A5 do Polo de Inovação IFAM.
"""
import os
from reportlab.lib.pagesizes import A5, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, "comprovantes_pdf")
if not os.path.exists(PDF_DIR):
    os.makedirs(PDF_DIR, exist_ok=True)

VERDE_IFAM = colors.HexColor("#006633")
VERDE_CLARO = colors.HexColor("#E8F5E9")
CINZA_TEXTO = colors.HexColor("#333333")
CINZA_BORDA = colors.HexColor("#CCCCCC")

def gerar_recibo_saida(dados):
    num_recibo = dados['num_recibo']
    nome_limpo = dados['solicitante'].replace(" ", "_").upper()
    nome_arquivo = f"{num_recibo.replace('/', '-')}_{nome_limpo}.pdf"
    caminho_pdf = os.path.join(PDF_DIR, nome_arquivo)

    doc = SimpleDocTemplate(
        caminho_pdf,
        pagesize=landscape(A5),
        leftMargin=20, rightMargin=20, topMargin=15, bottomMargin=15
    )
    elementos = []
    styles = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        'Tit', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=11,
        textColor=VERDE_IFAM, alignment=1, spaceAfter=2
    )
    estilo_sub = ParagraphStyle(
        'Sub', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8,
        textColor=colors.white, alignment=1
    )
    estilo_corpo = ParagraphStyle(
        'Corp', parent=styles['Normal'], fontName='Helvetica', fontSize=8,
        textColor=CINZA_TEXTO, leading=10
    )
    estilo_bold = ParagraphStyle(
        'Bld', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8,
        textColor=CINZA_TEXTO, leading=10
    )

    # 1. Cabeçalho
    elementos.append(Paragraph("INSTITUTO FEDERAL DO AMAZONAS — IFAM", estilo_titulo))
    elementos.append(Spacer(1, 2))

    t_header = Table([[Paragraph("POLO DE INOVAÇÃO MANAUS — ALMOXARIFADO CENTRAL", estilo_sub)]], colWidths=[555])
    t_header.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), VERDE_IFAM),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elementos.append(t_header)
    elementos.append(Spacer(1, 6))

    # 2. Dados do Registro
    t_info_data = [
        [
            Paragraph(f"<b>Nº COMPROVANTE:</b> {num_recibo}", estilo_corpo),
            Paragraph(f"<b>DATA/HORA:</b> {dados['data_hora']}", estilo_corpo)
        ],
        [
            Paragraph(f"<b>SOLICITANTE:</b> {dados['solicitante']}", estilo_corpo),
            Paragraph(f"<b>SIAPE/CPF:</b> {dados.get('siape') or 'Não inf.'}", estilo_corpo)
        ],
        [
            Paragraph(f"<b>PROJETO:</b> {dados['projeto']}", estilo_corpo),
            Paragraph(f"<b>AMBIENTE:</b> {dados['ambiente']}", estilo_corpo)
        ],
        [
            Paragraph(f"<b>FINALIDADE:</b> {dados.get('finalidade', 'Uso operacional')}", estilo_corpo),
            Paragraph(f"<b>TIPO:</b> SAÍDA DE CONSUMO", estilo_corpo)
        ],
    ]
    t_info = Table(t_info_data, colWidths=[280, 275])
    t_info.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, CINZA_BORDA),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#EEEEEE")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FAFAFA")),
    ]))
    elementos.append(t_info)
    elementos.append(Spacer(1, 8))

    # 3. Tabela do Item
    t_item_data = [
        [
            Paragraph("<b>CÓDIGO</b>", estilo_bold),
            Paragraph("<b>DESCRIÇÃO DO MATERIAL</b>", estilo_bold),
            Paragraph("<b>CATEGORIA</b>", estilo_bold),
            Paragraph("<b>QTD</b>", estilo_bold),
            Paragraph("<b>UNID</b>", estilo_bold),
            Paragraph("<b>DESTINAÇÃO</b>", estilo_bold),
        ],
        [
            Paragraph(dados['material_id'], estilo_corpo),
            Paragraph(dados['descricao'], estilo_corpo),
            Paragraph(dados.get('categoria', 'CONSUMO'), estilo_corpo),
            Paragraph(str(dados['quantidade']), estilo_bold),
            Paragraph(dados['unidade'], estilo_corpo),
            Paragraph("CONSUMO IMEDIATO", estilo_corpo),
        ]
    ]
    t_item = Table(t_item_data, colWidths=[65, 230, 80, 45, 45, 90])
    t_item.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), VERDE_CLARO),
        ('BOX', (0,0), (-1,-1), 0.5, VERDE_IFAM),
        ('INNERGRID', (0,0), (-1,-1), 0.5, CINZA_BORDA),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elementos.append(t_item)
    elementos.append(Spacer(1, 8))

    # 4. Termo de Responsabilidade
    termo = (
        "Declaro ter recebido os materiais acima relacionados para uso exclusivo nas atividades do Polo de Inovação IFAM."
    )
    elementos.append(Paragraph(f"<i>{termo}</i>", ParagraphStyle('Trm', parent=styles['Normal'], fontSize=6.5, textColor=colors.HexColor("#555555"), alignment=1)))
    elementos.append(Spacer(1, 14))

    # 5. Assinaturas
    t_ass_data = [
        [
            Paragraph("____________________________________________<br/><b>Entregue por: Almoxarifado Central</b>", estilo_corpo),
            Paragraph("____________________________________________<br/><b>Recebido por: Solicitante</b>", estilo_corpo)
        ]
    ]
    t_ass = Table(t_ass_data, colWidths=[277, 277])
    t_ass.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    elementos.append(t_ass)

    doc.build(elementos)
    return caminho_pdf, nome_arquivo

def gerar_termo_cautela(dados):
    id_cautela = dados['id_cautela']
    nome_limpo = dados['solicitante'].replace(" ", "_").upper()
    nome_arquivo = f"{id_cautela.replace('/', '-')}_{nome_limpo}.pdf"
    caminho_pdf = os.path.join(PDF_DIR, nome_arquivo)

    doc = SimpleDocTemplate(
        caminho_pdf,
        pagesize=landscape(A5),
        leftMargin=20, rightMargin=20, topMargin=15, bottomMargin=15
    )
    elementos = []
    styles = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle('Tit', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=11, textColor=VERDE_IFAM, alignment=1, spaceAfter=2)
    estilo_sub = ParagraphStyle('Sub', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, textColor=colors.white, alignment=1)
    estilo_corpo = ParagraphStyle('Corp', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=CINZA_TEXTO, leading=10)
    estilo_bold = ParagraphStyle('Bld', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, textColor=CINZA_TEXTO, leading=10)

    elementos.append(Paragraph("INSTITUTO FEDERAL DO AMAZONAS — IFAM", estilo_titulo))
    elementos.append(Spacer(1, 2))

    t_header = Table([[Paragraph("TERMO DE CAUTELA E RESPONSABILIDADE DE BENS PATRIMONIAIS / FERRAMENTAS", estilo_sub)]], colWidths=[555])
    t_header.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#0D47A1")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elementos.append(t_header)
    elementos.append(Spacer(1, 6))

    t_info_data = [
        [
            Paragraph(f"<b>TERMO DE CAUTELA Nº:</b> {id_cautela}", estilo_corpo),
            Paragraph(f"<b>DATA DE RETIRADA:</b> {dados['data_hora']}", estilo_corpo)
        ],
        [
            Paragraph(f"<b>RESPONSÁVEL:</b> {dados['solicitante']}", estilo_corpo),
            Paragraph(f"<b>SIAPE/CPF:</b> {dados.get('siape') or 'Não inf.'}", estilo_corpo)
        ],
        [
            Paragraph(f"<b>PROJETO VINCULADO:</b> {dados['projeto']}", estilo_corpo),
            Paragraph(f"<b>PREVISÃO DEVOLUÇÃO:</b> {dados.get('data_prevista') or 'A combinar'}", estilo_bold)
        ]
    ]
    t_info = Table(t_info_data, colWidths=[280, 275])
    t_info.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, CINZA_BORDA),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#EEEEEE")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FAFAFA")),
    ]))
    elementos.append(t_info)
    elementos.append(Spacer(1, 8))

    t_item_data = [
        [
            Paragraph("<b>EQUIPAMENTO / FERRAMENTA</b>", estilo_bold),
            Paragraph("<b>Nº DE SÉRIE / TOMBO</b>", estilo_bold),
            Paragraph("<b>QTD</b>", estilo_bold),
            Paragraph("<b>FINALIDADE</b>", estilo_bold),
        ],
        [
            Paragraph(dados['equipamento'], estilo_corpo),
            Paragraph(dados.get('serie') or 'S/N', estilo_bold),
            Paragraph("1 UN", estilo_corpo),
            Paragraph("EMPRÉSTIMO TEMPORÁRIO", estilo_corpo),
        ]
    ]
    t_item = Table(t_item_data, colWidths=[265, 120, 50, 120])
    t_item.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E3F2FD")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#0D47A1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, CINZA_BORDA),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elementos.append(t_item)
    elementos.append(Spacer(1, 8))

    termo = (
        "TERMO DE COMPROMISSO: Declaro ter recebido o equipamento em perfeitas condições de uso, comprometendo-me a zelar por "
        "sua guarda e devolvê-lo na data aprazada, respondendo por quaisquer danos decorrentes de dolo ou culpa."
    )
    elementos.append(Paragraph(f"<i>{termo}</i>", ParagraphStyle('Trm', parent=styles['Normal'], fontSize=6.5, textColor=colors.HexColor("#555555"), alignment=1)))
    elementos.append(Spacer(1, 14))

    t_ass_data = [
        [
            Paragraph("____________________________________________<br/><b>Almoxarifado Central (Entrega)</b>", estilo_corpo),
            Paragraph("____________________________________________<br/><b>Assinatura do Responsável</b>", estilo_corpo)
        ]
    ]
    t_ass = Table(t_ass_data, colWidths=[277, 277])
    t_ass.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    elementos.append(t_ass)

    doc.build(elementos)
    return caminho_pdf, nome_arquivo

def gerar_etiqueta_lata_pdf(dados_lata):
    """
    Gera Etiqueta Adesiva Lateral para Latas de Tinta / Químicos com:
    - Identificação PDM / SKU
    - Data de Abertura e Validade PAO (Period After Opening)
    - Régua Visual de Nível com 4 Faixas Graduadas para marcação a caneta.
    """
    from reportlab.lib.units import mm
    from reportlab.lib.pagesizes import landscape

    id_lata = dados_lata.get('id', 'FRAC-2026-0001')
    nome_arquivo = f"ETIQUETA_LATA_{id_lata.replace('/', '-')}.pdf"
    caminho_pdf = os.path.join(PDF_DIR, nome_arquivo)

    # Dimensão: 105mm x 148mm (A6 Retrato)
    doc = SimpleDocTemplate(
        caminho_pdf,
        pagesize=(105 * mm, 148 * mm),
        leftMargin=6 * mm, rightMargin=6 * mm, topMargin=6 * mm, bottomMargin=6 * mm
    )
    elementos = []
    styles = getSampleStyleSheet()

    cor_laranja = colors.HexColor("#D97706")
    cor_azul = colors.HexColor("#1E3A8A")

    est_topo = ParagraphStyle('Top', fontName='Helvetica-Bold', fontSize=7.5, textColor=colors.HexColor("#1F2937"), alignment=1)
    est_sub = ParagraphStyle('Sub', fontName='Helvetica-Bold', fontSize=6.5, textColor=colors.HexColor("#4B5563"), alignment=1)
    est_tit_box = ParagraphStyle('TitBox', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.white, alignment=1)
    est_item = ParagraphStyle('Itm', fontName='Helvetica-Bold', fontSize=8, textColor=colors.HexColor("#111827"), leading=9)
    est_lbl = ParagraphStyle('Lbl', fontName='Helvetica', fontSize=6.5, textColor=colors.HexColor("#4B5563"))
    est_val = ParagraphStyle('Val', fontName='Helvetica-Bold', fontSize=7, textColor=colors.HexColor("#111827"))
    est_regua = ParagraphStyle('Reg', fontName='Helvetica-Bold', fontSize=7.5, textColor=colors.HexColor("#1F2937"))

    # 1. Topo Institucional
    elementos.append(Paragraph("INSTITUTO FEDERAL DO AMAZONAS — IFAM", est_topo))
    elementos.append(Paragraph("POLO DE INOVAÇÃO MANAUS | ALMOXARIFADO", est_sub))
    elementos.append(Spacer(1, 3 * mm))

    # 2. Tarja do Fracionado
    t_tarja = Table([[Paragraph(f"CONTROLE DE LATA ABERTA • {id_lata}", est_tit_box)]], colWidths=[93 * mm])
    t_tarja.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), cor_laranja),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    elementos.append(t_tarja)
    elementos.append(Spacer(1, 2 * mm))

    # 3. Dados do Material
    sku = dados_lata.get('material_id', '010019')
    desc = dados_lata.get('descricao', 'TINTA ACRILICA')
    vol = dados_lata.get('volume_nominal', '18L')
    pao = dados_lata.get('validade_pao_dias', 60)
    abertura = dados_lata.get('data_abertura', '__/__/2026')
    vencimento = dados_lata.get('data_vencimento_pao', '__/__/2026')
    aberto_por = dados_lata.get('aberto_por', 'Equipe Operacional')

    t_mat_data = [
        [Paragraph(f"<b>SKU:</b> {sku} | <b>CATMAT:</b> {dados_lata.get('codigo_catmat', '-')}", est_lbl),
         Paragraph(f"<b>VOL:</b> {vol}", est_val)],
        [Paragraph(f"<b>ITEM:</b> {desc}", est_item), ""],
    ]
    t_mat = Table(t_mat_data, colWidths=[68 * mm, 25 * mm])
    t_mat.setStyle(TableStyle([
        ('SPAN', (0,1), (1,1)),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#9CA3AF")),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F9FAFB")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elementos.append(t_mat)
    elementos.append(Spacer(1, 2 * mm))

    # 4. Controle PAO (Period After Opening)
    t_pao_data = [
        [Paragraph("<b>DATA DE ABERTURA:</b>", est_lbl), Paragraph(f"<b>{abertura}</b>", est_val)],
        [Paragraph("<b>VALIDADE PÓS-ABERTURA (PAO):</b>", est_lbl), Paragraph(f"<b>{pao} DIAS</b>", est_val)],
        [Paragraph("<b>UTILIZAR ATÉ:</b>", est_lbl), Paragraph(f"<font color='#DC2626'><b>{vencimento}</b></font>", est_val)],
        [Paragraph("<b>ABERTO POR:</b>", est_lbl), Paragraph(f"{aberto_por}", est_lbl)],
    ]
    t_pao = Table(t_pao_data, colWidths=[48 * mm, 45 * mm])
    t_pao.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, cor_laranja),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#FED7AA")),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFFBEB")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elementos.append(t_pao)
    elementos.append(Spacer(1, 3 * mm))

    # 5. Régua Visual de Nível (Visualizador Tátil)
    elementos.append(Paragraph("<b>RÉGUA DE NÍVEL — RISQUE / MARQUE AO DEVOLVER:</b>", est_sub))
    elementos.append(Spacer(1, 1 * mm))

    t_regua_data = [
        [Paragraph("[ &nbsp; ] <b>100% — CHEIA / ABERTURA</b>", est_regua), Paragraph("Recém-aberta", est_lbl)],
        [Paragraph("[ &nbsp; ] <b>75% &nbsp;— TRÊS QUARTOS (3/4)</b>", est_regua), Paragraph("1º Retorno", est_lbl)],
        [Paragraph("[ &nbsp; ] <b>50% &nbsp;— METADE (1/2)</b>", est_regua), Paragraph("2º Retorno", est_lbl)],
        [Paragraph("[ &nbsp; ] <b>25% &nbsp;— UM QUARTO (1/4)</b>", est_regua), Paragraph("Fundo de lata", est_lbl)],
        [Paragraph("[ &nbsp; ] <b>&nbsp;&nbsp;0% &nbsp;— ESGOTADA</b>", est_regua), Paragraph("Descarte limpo", est_lbl)],
    ]
    t_regua = Table(t_regua_data, colWidths=[65 * mm, 28 * mm])
    t_regua.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#374151")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#ECFDF5")),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F0FDF4")),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#FEFCE8")),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#FFF7ED")),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor("#FEF2F2")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    elementos.append(t_regua)
    elementos.append(Spacer(1, 2 * mm))

    # Rodapé
    elementos.append(Paragraph("<i>Fixar na lateral da lata. Não cobrir as instruções de segurança do fabricante.</i>", ParagraphStyle('Rod', fontName='Helvetica-Oblique', fontSize=5.5, textColor=colors.HexColor("#6B7280"), alignment=1)))

    doc.build(elementos)
    return caminho_pdf, nome_arquivo

def gerar_etiqueta_prateleira_pdf(material):
    """
    Gera Etiqueta WMS de Prateleira com Endereçamento 3D e Unidades:
    Ambiente > Estrutura > Posição
    """
    from reportlab.lib.units import mm

    sku = material.get('id', '010001')
    nome_arquivo = f"ETIQUETA_WMS_{sku}.pdf"
    caminho_pdf = os.path.join(PDF_DIR, nome_arquivo)

    doc = SimpleDocTemplate(
        caminho_pdf,
        pagesize=(90 * mm, 50 * mm),
        leftMargin=4 * mm, rightMargin=4 * mm, topMargin=4 * mm, bottomMargin=4 * mm
    )
    elementos = []
    styles = getSampleStyleSheet()

    est_topo = ParagraphStyle('Top', fontName='Helvetica-Bold', fontSize=6.5, textColor=VERDE_IFAM, alignment=1)
    est_sku = ParagraphStyle('Sku', fontName='Helvetica-Bold', fontSize=14, textColor=colors.HexColor("#111827"), alignment=1)
    est_desc = ParagraphStyle('Dsc', fontName='Helvetica-Bold', fontSize=7.5, textColor=colors.HexColor("#1F2937"), alignment=1, leading=8.5)
    est_end = ParagraphStyle('End', fontName='Helvetica-Bold', fontSize=7.5, textColor=colors.HexColor("#1E3A8A"), alignment=1)
    est_unid = ParagraphStyle('Uni', fontName='Helvetica', fontSize=6.5, textColor=colors.HexColor("#4B5563"), alignment=1)

    elementos.append(Paragraph("IFAM • POLO DE INOVAÇÃO — WMS ALMOXARIFADO", est_topo))
    elementos.append(Spacer(1, 1 * mm))

    elementos.append(Paragraph(f"SKU: {sku}", est_sku))
    if material.get('codigo_catmat'):
        elementos.append(Paragraph(f"CATMAT: {material['codigo_catmat']}", ParagraphStyle('Cmt', fontName='Helvetica', fontSize=6, textColor=colors.HexColor("#6B7280"), alignment=1)))
    elementos.append(Spacer(1, 1 * mm))

    elementos.append(Paragraph(f"{material.get('descricao', '')}", est_desc))
    elementos.append(Spacer(1, 1.5 * mm))

    end_3d = f"{material.get('local_estrutura', 'ESTANTE')} • {material.get('local_posicao', 'PRATELEIRA')}"
    t_end = Table([[Paragraph(f"<b>ENDEREÇO:</b> {end_3d}", est_end)]], colWidths=[82 * mm])
    t_end.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EFF6FF")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#3B82F6")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elementos.append(t_end)
    elementos.append(Spacer(1, 1 * mm))

    unid_txt = f"Unid. Base: <b>{material.get('unidade_base', 'UN')}</b> | Embalagem: <b>{material.get('embalagem_compra', 'UN')}</b> (Fator: {material.get('fator_conversao', 1.0)})"
    elementos.append(Paragraph(unid_txt, est_unid))

    doc.build(elementos)
    return caminho_pdf, nome_arquivo


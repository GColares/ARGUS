# c:\ARGUS\scripts\gerar_planilha_almoxarifado.py
"""
Script de Geração da Pasta de Trabalho Operacional do Almoxarifado (Pré-ARGUS).
Higieniza os dados de 'inventario_inova.xlsx' e cria 'Almoxarifado_ARGUS_Operacional.xlsx/xlsm'
estruturado com regras relacionais, fórmulas automáticas e recibo de balcão.
"""

import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

ORIGEM_PATH = r"C:\ARGUS\almoxarifado\inventario_legado\inventario_inova.xlsx"
DESTINO_XLSX = r"C:\ARGUS\almoxarifado\inventario_legado\Almoxarifado_ARGUS_Operacional.xlsx"
DESTINO_XLSM = r"C:\ARGUS\almoxarifado\inventario_legado\Almoxarifado_ARGUS_Operacional.xlsm"

def carregar_dados_legados():
    print("Carregando dados legados de:", ORIGEM_PATH)
    wb_orig = openpyxl.load_workbook(ORIGEM_PATH, data_only=True)

    # 1. Materiais & Ferramentas
    s_manut = wb_orig[wb_orig.sheetnames[6]] # ALMOXARIFADO MANUTENCAO
    materiais = []
    vistos = set()
    palavras_ferramenta = [
        'MARRETA', 'MARTELO', 'DESEMPENADEIRA', 'ALICATE', 'CHAVE', 'TRENA', 
        'SERROTE', 'FURADEIRA', 'PARAFUSADEIRA', 'NIVEL', 'COLHER DE PEDREIRO', 
        'CABO PARA ROLO', 'ESCOVA', 'ESPATULA', 'PISTOLA', 'MULTIMETRO', 'SERRA'
    ]

    for r in range(6, s_manut.max_row + 1):
        desc = s_manut.cell(r, 5).value
        if desc and str(desc).strip():
            desc_clean = str(desc).strip().upper()
            if desc_clean not in vistos:
                vistos.add(desc_clean)
                qtd = s_manut.cell(r, 3).value or 1
                try:
                    qtd = float(qtd)
                except:
                    qtd = 1.0
                nf = s_manut.cell(r, 8).value
                origem = s_manut.cell(r, 10).value
                eh_ferramenta = any(p in desc_clean for p in palavras_ferramenta)
                cat = 'FERRAMENTA' if eh_ferramenta else 'CONSUMO'
                materiais.append({
                    'id': f'MAT-{len(materiais)+1:04d}',
                    'descricao': desc_clean,
                    'categoria': cat,
                    'unidade': 'UN',
                    'estoque_inicial': qtd,
                    'nf': str(nf) if nf else '',
                    'origem': str(origem) if origem else 'POLO DE INOVAÇÃO',
                    'local': 'ALMOXARIFADO MANUTENÇÃO'
                })

    s_mov = wb_orig[wb_orig.sheetnames[7]] # ENTRADA & SAIDA
    for r in range(3, s_mov.max_row + 1):
        m = s_mov.cell(r, 1).value
        if m and str(m).strip():
            m_clean = str(m).strip().upper()
            if m_clean not in vistos:
                vistos.add(m_clean)
                eh_ferramenta = any(p in m_clean for p in palavras_ferramenta)
                qtd = s_mov.cell(r, 6).value or 0
                try:
                    qtd = float(qtd)
                except:
                    qtd = 0.0
                materiais.append({
                    'id': f'MAT-{len(materiais)+1:04d}',
                    'descricao': m_clean,
                    'categoria': 'FERRAMENTA' if eh_ferramenta else 'CONSUMO',
                    'unidade': 'UN',
                    'estoque_inicial': qtd,
                    'nf': str(s_mov.cell(r, 3).value or ''),
                    'origem': 'POLO DE INOVAÇÃO',
                    'local': 'ALMOXARIFADO'
                })

    # 2. Cautelas Históricas de TI e Ferramentas
    cautelas = []
    s_caut1 = wb_orig[wb_orig.sheetnames[2]] # PATRIMONIO_CAUTELAS_
    for r in range(5, s_caut1.max_row + 1):
        desc = s_caut1.cell(r, 4).value
        serie = s_caut1.cell(r, 3).value
        solic = s_caut1.cell(r, 7).value
        if desc and solic:
            cautelas.append({
                'num_cautela': f'CAUT-LEG-{len(cautelas)+1:03d}',
                'equipamento': str(desc).strip().upper(),
                'serie': str(serie).strip() if serie else 'S/N',
                'origem_convenio': str(s_caut1.cell(r, 6).value or 'POLO GERAL').strip(),
                'solicitante': str(solic).strip().upper(),
                'aprovador': str(s_caut1.cell(r, 9).value or '').strip(),
                'data_saida': str(s_caut1.cell(r, 10).value or '')[:10],
                'data_devolucao': str(s_caut1.cell(r, 11).value or '')[:10],
                'status': str(s_caut1.cell(r, 12).value or 'EM USO').strip()
            })

    s_caut2 = wb_orig[wb_orig.sheetnames[3]] # ATUALIZANDO - PATRIMONIO CAUTEL
    for r in range(5, s_caut2.max_row + 1):
        desc = s_caut2.cell(r, 4).value
        serie = s_caut2.cell(r, 3).value
        solic = s_caut2.cell(r, 7).value
        if desc and solic:
            cautelas.append({
                'num_cautela': f'CAUT-LEG-{len(cautelas)+1:03d}',
                'equipamento': str(desc).strip().upper(),
                'serie': str(serie).strip() if serie else 'S/N',
                'origem_convenio': str(s_caut2.cell(r, 6).value or 'POLO GERAL').strip(),
                'solicitante': str(solic).strip().upper(),
                'aprovador': str(s_caut2.cell(r, 10).value or '').strip(),
                'data_saida': str(s_caut2.cell(r, 11).value or '')[:10],
                'data_devolucao': str(s_caut2.cell(r, 12).value or '')[:10],
                'status': str(s_caut2.cell(r, 13).value or 'EM USO').strip()
            })

    # 3. Equipamentos Disponíveis em Armários (Estoque de TI)
    s_disp = wb_orig[wb_orig.sheetnames[9]] # Pagina23
    equipamentos_ti = []
    for r in range(2, s_disp.max_row + 1):
        desc = s_disp.cell(r, 4).value
        serie = s_disp.cell(r, 7).value
        conv = s_disp.cell(r, 8).value
        arm = s_disp.cell(r, 9).value
        status = s_disp.cell(r, 10).value
        if desc:
            equipamentos_ti.append({
                'id': f'TI-{len(equipamentos_ti)+1:04d}',
                'equipamento': str(desc).strip().upper(),
                'marca': str(s_disp.cell(r, 5).value or 'DELL').strip(),
                'serie': str(serie).strip() if serie else 'S/N',
                'origem_convenio': str(conv).strip() if conv else 'POLO DE INOVAÇÃO',
                'localizacao': str(arm).strip() if arm else 'ARMÁRIO 5 PT3',
                'status': str(status).strip() if status else 'DISPONÍVEL'
            })

    # 4. Ambientes do Polo
    ambientes = [
        'ALMOXARIFADO CENTRAL', 'ALMOXARIFADO MANUTENÇÃO', 'SALA DA DIRETORIA',
        'SALA DA ADMINISTRAÇÃO', 'SALA DO TI', 'SALA DA CPO', 'SALA DA PROSPECÇÃO',
        'SALA DE REUNIÃO', 'RECEPÇÃO', 'COPA', 'CORREDORES',
        'LABORATÓRIO LSCN', 'LABORATÓRIO LRI', 'LABORATÓRIO LPH',
        'LABORATÓRIO LEMAS', 'LABORATÓRIO LABCODING', 'ESPAÇO MAKER'
    ]

    # 5. Projetos / Convênios
    projetos = [
        'MANUTENÇÃO PREDIAL / POLO GERAL',
        'BIO CAROÇO (EDITAL FAEPI 072/2026)',
        'CV 001/2020 SAGEMCON',
        'CV 002/2023 ERGO SALUS',
        'CV 016/2022 COELMATIC',
        'CV 001/2022 IOT',
        'CV 007/2022 AX ACADEMY',
        'CV 008/2021 FOGO BIO',
        'CV 011/2021 TELECOM'
    ]

    # 6. Solicitantes (extraídos das cautelas)
    solicitantes_set = set()
    for c in cautelas:
        if c['solicitante']:
            solicitantes_set.add(c['solicitante'])
    solicitantes = sorted(list(solicitantes_set))

    return {
        'materiais': materiais,
        'cautelas': cautelas,
        'equipamentos_ti': equipamentos_ti,
        'ambientes': ambientes,
        'projetos': projetos,
        'solicitantes': solicitantes
    }

def criar_planilha_operacional(dados):
    print("Construindo pasta de trabalho com o Design System do ARGUS...")
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    VERDE_ESCURO = "0F5132"
    VERDE_MEDIO = "198754"
    VERDE_CLARO = "D1E7DD"
    CINZA_HEADER = "F8F9FA"
    CINZA_BORDA = "DEE2E6"
    AZUL_HEADER = "0D6EFD"
    BRANCO = "FFFFFF"

    font_titulo = Font(name="Calibri", size=15, bold=True, color=BRANCO)
    font_subtitulo = Font(name="Calibri", size=11, bold=True, color=BRANCO)
    font_header_tab = Font(name="Calibri", size=10, bold=True, color=BRANCO)
    font_bold = Font(name="Calibri", size=10, bold=True)
    font_normal = Font(name="Calibri", size=10)
    font_small = Font(name="Calibri", size=9, color="6C757D")

    fill_topo = PatternFill(start_color=VERDE_ESCURO, end_color=VERDE_ESCURO, fill_type="solid")
    fill_header_verde = PatternFill(start_color=VERDE_MEDIO, end_color=VERDE_MEDIO, fill_type="solid")
    fill_header_azul = PatternFill(start_color=AZUL_HEADER, end_color=AZUL_HEADER, fill_type="solid")
    fill_zebra = PatternFill(start_color="F9FAFB", end_color="F9FAFB", fill_type="solid")

    borda_fina = Border(
        left=Side(style='thin', color=CINZA_BORDA),
        right=Side(style='thin', color=CINZA_BORDA),
        top=Side(style='thin', color=CINZA_BORDA),
        bottom=Side(style='thin', color=CINZA_BORDA)
    )

    align_center = Alignment(horizontal='center', vertical='center')
    align_left = Alignment(horizontal='left', vertical='center')
    align_right = Alignment(horizontal='right', vertical='center')

    # =========================================================================
    # ABA 1: PAINEL_BALCAO (Operação da Colaboradora)
    # =========================================================================
    ws_balcao = wb.create_sheet(title="PAINEL_BALCAO")
    ws_balcao.views.sheetView[0].showGridLines = True

    ws_balcao.merge_cells("A1:G1")
    ws_balcao["A1"] = "ARGUS  |  SISTEMA DE GESTÃO DO POLO DE INOVAÇÃO IFAM"
    ws_balcao["A1"].font = font_titulo
    ws_balcao["A1"].fill = fill_topo
    ws_balcao["A1"].alignment = align_center
    ws_balcao.row_dimensions[1].height = 32

    ws_balcao.merge_cells("A2:G2")
    ws_balcao["A2"] = "MÓDULO DE ALMOXARIFADO & PATRIMÔNIO — PAINEL OPERACIONAL DE ATENDIMENTO DE BALCÃO"
    ws_balcao["A2"].font = font_subtitulo
    ws_balcao["A2"].fill = fill_header_verde
    ws_balcao["A2"].alignment = align_center
    ws_balcao.row_dimensions[2].height = 22

    ws_balcao["B4"] = "ITENS EM ESTOQUE"
    ws_balcao["B4"].font = font_small
    ws_balcao["B5"] = len(dados['materiais'])
    ws_balcao["B5"].font = Font(name="Calibri", size=16, bold=True, color=VERDE_ESCURO)

    ws_balcao["D4"] = "CAUTELAS HISTÓRICAS"
    ws_balcao["D4"].font = font_small
    ws_balcao["D5"] = len(dados['cautelas'])
    ws_balcao["D5"].font = Font(name="Calibri", size=16, bold=True, color=AZUL_HEADER)

    ws_balcao["F4"] = "EQUIPAMENTOS TI DISPONÍVEIS"
    ws_balcao["F4"].font = font_small
    ws_balcao["F5"] = len(dados['equipamentos_ti'])
    ws_balcao["F5"].font = Font(name="Calibri", size=16, bold=True, color="D97706")

    ws_balcao.merge_cells("B7:F7")
    ws_balcao["B7"] = "NOVO ATENDIMENTO DE BALCÃO (REGISTRO RÁPIDO)"
    ws_balcao["B7"].font = Font(name="Calibri", size=11, bold=True, color=BRANCO)
    ws_balcao["B7"].fill = fill_topo
    ws_balcao["B7"].alignment = align_center
    ws_balcao.row_dimensions[7].height = 24

    campos_formulario = [
        ("B8", "C8", "Tipo de Movimentação:", "1. SAÍDA DE CONSUMO (BAIXA DEFINITIVA)"),
        ("B9", "C9", "Data do Registro:", "=TODAY()"),
        ("B10", "C10", "Solicitante / Responsável:", "ALEXANDRE LOPES"),
        ("B11", "C11", "Matrícula SIAPE ou CPF:", "SIAPE 1245889"),
        ("B12", "C12", "Projeto / Fonte Financiadora:", "MANUTENÇÃO PREDIAL / POLO GERAL"),
        ("B13", "C13", "Ambiente / Laboratório Destino:", "ALMOXARIFADO CENTRAL"),
        ("B14", "C14", "Item / Material Requisitado:", "MARRETA 1,00KG"),
        ("B15", "C15", "Quantidade a Retirar:", 1),
        ("B16", "C16", "Data Prevista Devolução (se cautela):", ""),
        ("B17", "C17", "Finalidade do Uso / Justificativa:", "Reparo de rotina e manutenção predial"),
    ]

    for label_cell, val_cell, label, val_default in campos_formulario:
        row = int(label_cell[1:])
        ws_balcao.row_dimensions[row].height = 20
        ws_balcao[label_cell] = label
        ws_balcao[label_cell].font = font_bold
        ws_balcao[label_cell].alignment = Alignment(horizontal='right', vertical='center')
        
        ws_balcao.merge_cells(f"{val_cell}:F{row}")
        c_val = ws_balcao[val_cell]
        c_val.value = val_default
        c_val.font = font_normal
        c_val.alignment = Alignment(horizontal='left', vertical='center')
        
        for col_idx in range(2, 7):
            cell = ws_balcao.cell(row=row, column=col_idx)
            cell.border = borda_fina
    ws_balcao["C9"].number_format = "DD/MM/YYYY"

    ws_balcao.merge_cells("B19:C20")
    ws_balcao["B19"] = "📦 [REGISTRAR SAÍDA & GERAR RECIBO]"
    ws_balcao["B19"].font = Font(name="Calibri", size=10, bold=True, color=BRANCO)
    ws_balcao["B19"].fill = fill_header_verde
    ws_balcao["B19"].alignment = align_center

    ws_balcao.merge_cells("D19:E20")
    ws_balcao["D19"] = "↩️ [REGISTRAR DEVOLUÇÃO DE CAUTELA]"
    ws_balcao["D19"].font = Font(name="Calibri", size=10, bold=True, color=BRANCO)
    ws_balcao["D19"].fill = fill_header_azul
    ws_balcao["D19"].alignment = align_center

    ws_balcao["F19"] = "🔍 [VER ESTOQUE]"
    ws_balcao["F19"].font = Font(name="Calibri", size=9, bold=True, color=BRANCO)
    ws_balcao["F19"].fill = PatternFill(start_color="4B5563", end_color="4B5563", fill_type="solid")
    ws_balcao["F19"].alignment = align_center

    ws_balcao.column_dimensions['A'].width = 5
    ws_balcao.column_dimensions['B'].width = 30
    ws_balcao.column_dimensions['C'].width = 20
    ws_balcao.column_dimensions['D'].width = 25
    ws_balcao.column_dimensions['E'].width = 20
    ws_balcao.column_dimensions['F'].width = 25
    ws_balcao.column_dimensions['G'].width = 5

    # =========================================================================
    # ABA 2: RECIBO_IMPRESSAO (Termo / Vale Retirada A5)
    # =========================================================================
    ws_recibo = wb.create_sheet(title="RECIBO_IMPRESSAO")
    ws_recibo.views.sheetView[0].showGridLines = True

    ws_recibo.merge_cells("B2:G2")
    ws_recibo["B2"] = "INSTITUTO FEDERAL DO AMAZONAS - IFAM"
    ws_recibo["B2"].font = Font(name="Calibri", size=12, bold=True, color=VERDE_ESCURO)
    ws_recibo["B2"].alignment = align_center

    ws_recibo.merge_cells("B3:G3")
    ws_recibo["B3"] = "POLO DE INOVAÇÃO MANAUS — ALMOXARIFADO CENTRAL"
    ws_recibo["B3"].font = Font(name="Calibri", size=10, bold=True)
    ws_recibo["B3"].alignment = align_center

    ws_recibo.merge_cells("B4:G4")
    ws_recibo["B4"] = "COMPROVANTE DE RETIRADA / TERMO DE CAUTELA Nº: REC-2026/0001"
    ws_recibo["B4"].font = Font(name="Calibri", size=11, bold=True, color=BRANCO)
    ws_recibo["B4"].fill = fill_topo
    ws_recibo["B4"].alignment = align_center
    ws_recibo.row_dimensions[4].height = 22

    dados_recibo = [
        ("B6", "Data / Hora:", "C6", "=TODAY()"),
        ("B7", "Solicitante / Responsável:", "C7", "=PAINEL_BALCAO!C10"),
        ("B8", "Matrícula SIAPE ou CPF:", "C8", "=PAINEL_BALCAO!C11"),
        ("B9", "Projeto Financiador:", "C9", "=PAINEL_BALCAO!C12"),
        ("B10", "Ambiente de Aplicação:", "C10", "=PAINEL_BALCAO!C13"),
        ("B11", "Tipo de Movimentação:", "C11", "=PAINEL_BALCAO!C8"),
    ]
    for lbl_c, lbl_t, val_c, val_f in dados_recibo:
        ws_recibo[lbl_c] = lbl_t
        ws_recibo[lbl_c].font = font_bold
        ws_recibo.merge_cells(f"{val_c}:G{val_c[1:]}")
        ws_recibo[val_c] = val_f
        ws_recibo[val_c].font = font_normal

    ws_recibo["B13"] = "CÓDIGO"
    ws_recibo["C13"] = "DESCRIÇÃO DO ITEM / FERRAMENTA"
    ws_recibo["D13"] = "CATEGORIA"
    ws_recibo["E13"] = "QTD"
    ws_recibo["F13"] = "UNID"
    ws_recibo["G13"] = "PREV. DEVOLUÇÃO"

    for col in ["B", "C", "D", "E", "F", "G"]:
        c = ws_recibo[f"{col}13"]
        c.font = font_header_tab
        c.fill = fill_header_verde
        c.alignment = align_center

    ws_recibo["B14"] = "MAT-0001"
    ws_recibo["C14"] = "=PAINEL_BALCAO!C14"
    ws_recibo["D14"] = "CONSUMO / FERRAMENTA"
    ws_recibo["E14"] = "=PAINEL_BALCAO!C15"
    ws_recibo["F14"] = "UN"
    ws_recibo["G14"] = "=PAINEL_BALCAO!C16"

    for col in ["B", "C", "D", "E", "F", "G"]:
        c = ws_recibo[f"{col}14"]
        c.font = font_normal
        c.alignment = align_center
        c.border = borda_fina

    ws_recibo.merge_cells("B16:G17")
    ws_recibo["B16"] = (
        "TERMO DE COMPROMISSO: Declaro que recebi os materiais/equipamentos acima descritos em perfeito estado "
        "de conservação e funcionamento, comprometendo-me a utilizá-los estritamente nas atividades institucionais do "
        "Polo de Inovação IFAM e a zelar pela sua guarda e integridade, comunicando imediatamente qualquer avaria."
    )
    ws_recibo["B16"].font = Font(name="Calibri", size=8, italic=True)
    ws_recibo["B16"].alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

    ws_recibo.merge_cells("B20:D20")
    ws_recibo["B20"] = "________________________________________"
    ws_recibo["B20"].alignment = align_center

    ws_recibo.merge_cells("B21:D21")
    ws_recibo["B21"] = "Entregue por: Almoxarifado Central"
    ws_recibo["B21"].font = font_small
    ws_recibo["B21"].alignment = align_center

    ws_recibo.merge_cells("E20:G20")
    ws_recibo["E20"] = "________________________________________"
    ws_recibo["E20"].alignment = align_center

    ws_recibo.merge_cells("E21:G21")
    ws_recibo["E21"] = "Recebido por: Solicitante"
    ws_recibo["E21"].font = font_small
    ws_recibo["E21"].alignment = align_center

    ws_recibo.column_dimensions['A'].width = 4
    ws_recibo.column_dimensions['B'].width = 18
    ws_recibo.column_dimensions['C'].width = 30
    ws_recibo.column_dimensions['D'].width = 16
    ws_recibo.column_dimensions['E'].width = 8
    ws_recibo.column_dimensions['F'].width = 8
    ws_recibo.column_dimensions['G'].width = 18

    # =========================================================================
    # ABA 3: TB_CATALOGO_MATERIAIS
    # =========================================================================
    ws_mat = wb.create_sheet(title="TB_CATALOGO_MATERIAIS")
    ws_mat.views.sheetView[0].showGridLines = True

    headers_mat = [
        "Código", "Descrição do Material / Ferramenta", "Categoria Patrimonial",
        "Unidade", "Estoque Inicial", "Entradas Acumuladas", "Saídas Acumuladas",
        "Saldo Atual", "Estoque Mínimo", "Status do Estoque", "Localização Física", "NF Origem"
    ]

    ws_mat.merge_cells("A1:L1")
    ws_mat["A1"] = "CATÁLOGO GERAL DE MATERIAIS & FERRAMENTAS DO ALMOXARIFADO"
    ws_mat["A1"].font = font_titulo
    ws_mat["A1"].fill = fill_topo
    ws_mat["A1"].alignment = align_center
    ws_mat.row_dimensions[1].height = 28

    ws_mat.row_dimensions[3].height = 22
    for col_idx, h in enumerate(headers_mat, 1):
        cell = ws_mat.cell(row=3, column=col_idx, value=h)
        cell.font = font_header_tab
        cell.fill = fill_header_verde
        cell.alignment = align_center
        cell.border = borda_fina

    for i, m in enumerate(dados['materiais'], start=4):
        ws_mat.row_dimensions[i].height = 19
        ws_mat.cell(row=i, column=1, value=m['id']).alignment = align_center
        ws_mat.cell(row=i, column=2, value=m['descricao']).alignment = align_left
        ws_mat.cell(row=i, column=3, value=m['categoria']).alignment = align_center
        ws_mat.cell(row=i, column=4, value=m['unidade']).alignment = align_center
        ws_mat.cell(row=i, column=5, value=m['estoque_inicial']).alignment = align_right
        
        ws_mat.cell(row=i, column=6, value=f'=SUMIF(TB_ENTRADAS_COMPRAS!D:D, A{i}, TB_ENTRADAS_COMPRAS!F:F)').alignment = align_right
        ws_mat.cell(row=i, column=7, value=f'=SUMIF(TB_HISTORICO_SAIDAS!C:C, A{i}, TB_HISTORICO_SAIDAS!E:E)').alignment = align_right
        ws_mat.cell(row=i, column=8, value=f'=E{i}+F{i}-G{i}').alignment = align_right
        ws_mat.cell(row=i, column=9, value=2).alignment = align_right
        ws_mat.cell(row=i, column=10, value=f'=IF(H{i}<=I{i}, "🔴 BAIXO", "🟢 REGULAR")').alignment = align_center
        ws_mat.cell(row=i, column=11, value=m['local']).alignment = align_left
        ws_mat.cell(row=i, column=12, value=m['nf']).alignment = align_center

        for c_idx in range(1, 13):
            cell = ws_mat.cell(row=i, column=c_idx)
            cell.font = font_normal
            cell.border = borda_fina
            if i % 2 == 0:
                cell.fill = fill_zebra

    for col in ws_mat.columns:
        col_letter = get_column_letter(col[0].column)
        ws_mat.column_dimensions[col_letter].width = 18
    ws_mat.column_dimensions['B'].width = 45
    ws_mat.column_dimensions['C'].width = 20

    # =========================================================================
    # ABA 4: TB_HISTORICO_SAIDAS
    # =========================================================================
    ws_sai = wb.create_sheet(title="TB_HISTORICO_SAIDAS")
    ws_sai.views.sheetView[0].showGridLines = True

    headers_sai = [
        "ID Saída", "Data / Hora", "Código Item", "Descrição do Material",
        "Qtd Retirada", "Unidade", "Solicitante", "Projeto Financiador",
        "Ambiente / Destino", "Finalidade / Observações", "Comprovante Nº"
    ]
    ws_sai.merge_cells("A1:K1")
    ws_sai["A1"] = "REGISTRO HISTÓRICO DE SAÍDAS DE MATERIAIS DE CONSUMO"
    ws_sai["A1"].font = font_titulo
    ws_sai["A1"].fill = fill_topo
    ws_sai["A1"].alignment = align_center
    ws_sai.row_dimensions[1].height = 28

    ws_sai.row_dimensions[3].height = 22
    for col_idx, h in enumerate(headers_sai, 1):
        cell = ws_sai.cell(row=3, column=col_idx, value=h)
        cell.font = font_header_tab
        cell.fill = fill_header_verde
        cell.alignment = align_center
        cell.border = borda_fina

    ex_sai = [
        "SAI-2026-0001", "14/09/2026", "MAT-0001", "MARRETA 1,00KG",
        1, "UN", "ALEXANDRE LOPES", "MANUTENÇÃO PREDIAL / POLO GERAL",
        "ALMOXARIFADO CENTRAL", "Manutenção predial de rotina", "REC-2026/0001"
    ]
    ws_sai.row_dimensions[4].height = 19
    for col_idx, val in enumerate(ex_sai, 1):
        c = ws_sai.cell(row=4, column=col_idx, value=val)
        c.font = font_normal
        c.border = borda_fina
        c.alignment = align_center if col_idx not in [4, 7, 8, 10] else align_left

    for col in ws_sai.columns:
        col_letter = get_column_letter(col[0].column)
        ws_sai.column_dimensions[col_letter].width = 18
    ws_sai.column_dimensions['D'].width = 35
    ws_sai.column_dimensions['G'].width = 25
    ws_sai.column_dimensions['H'].width = 30

    # =========================================================================
    # ABA 5: TB_CAUTELAS
    # =========================================================================
    ws_caut = wb.create_sheet(title="TB_CAUTELAS")
    ws_caut.views.sheetView[0].showGridLines = True

    headers_caut = [
        "Nº Cautela", "Equipamento / Ferramenta", "Nº de Série", "Origem / Convênio",
        "Responsável (Solicitante)", "Aprovador", "Data Saída", "Data Devolução Prevista",
        "Status Atual", "Data Retorno Efetivo", "Observações / Avarias"
    ]
    ws_caut.merge_cells("A1:K1")
    ws_caut["A1"] = "HISTÓRICO E CONTROLE DE CAUTELAS DE EQUIPAMENTOS E FERRAMENTAS"
    ws_caut["A1"].font = font_titulo
    ws_caut["A1"].fill = fill_topo
    ws_caut["A1"].alignment = align_center
    ws_caut.row_dimensions[1].height = 28

    ws_caut.row_dimensions[3].height = 22
    for col_idx, h in enumerate(headers_caut, 1):
        cell = ws_caut.cell(row=3, column=col_idx, value=h)
        cell.font = font_header_tab
        cell.fill = fill_header_azul
        cell.alignment = align_center
        cell.border = borda_fina

    for i, c in enumerate(dados['cautelas'], start=4):
        ws_caut.row_dimensions[i].height = 19
        ws_caut.cell(row=i, column=1, value=c['num_cautela']).alignment = align_center
        ws_caut.cell(row=i, column=2, value=c['equipamento']).alignment = align_left
        ws_caut.cell(row=i, column=3, value=c['serie']).alignment = align_center
        ws_caut.cell(row=i, column=4, value=c['origem_convenio']).alignment = align_left
        ws_caut.cell(row=i, column=5, value=c['solicitante']).alignment = align_left
        ws_caut.cell(row=i, column=6, value=c['aprovador']).alignment = align_left
        ws_caut.cell(row=i, column=7, value=c['data_saida']).alignment = align_center
        ws_caut.cell(row=i, column=8, value=c['data_devolucao']).alignment = align_center
        ws_caut.cell(row=i, column=9, value=c['status']).alignment = align_center
        ws_caut.cell(row=i, column=10, value="").alignment = align_center
        ws_caut.cell(row=i, column=11, value="").alignment = align_left

        for c_idx in range(1, 12):
            cell = ws_caut.cell(row=i, column=c_idx)
            cell.font = font_normal
            cell.border = borda_fina
            if i % 2 == 0:
                cell.fill = fill_zebra

    for col in ws_caut.columns:
        col_letter = get_column_letter(col[0].column)
        ws_caut.column_dimensions[col_letter].width = 18
    ws_caut.column_dimensions['B'].width = 35
    ws_caut.column_dimensions['D'].width = 25
    ws_caut.column_dimensions['E'].width = 25

    # =========================================================================
    # ABA 6: TB_TI_DISPONIVEL
    # =========================================================================
    ws_ti = wb.create_sheet(title="TB_TI_DISPONIVEL")
    ws_ti.views.sheetView[0].showGridLines = True

    headers_ti = [
        "Código", "Descrição do Equipamento", "Marca / Modelo", "Nº de Série",
        "Origem / Convênio", "Armário / Prateleira", "Status de Disponibilidade"
    ]
    ws_ti.merge_cells("A1:G1")
    ws_ti["A1"] = "EQUIPAMENTOS DE TI GUARDADOS NO ALMOXARIFADO (PRONTOS PARA CAUTELA)"
    ws_ti["A1"].font = font_titulo
    ws_ti["A1"].fill = fill_topo
    ws_ti["A1"].alignment = align_center
    ws_ti.row_dimensions[1].height = 28

    ws_ti.row_dimensions[3].height = 22
    for col_idx, h in enumerate(headers_ti, 1):
        cell = ws_ti.cell(row=3, column=col_idx, value=h)
        cell.font = font_header_tab
        cell.fill = fill_header_azul
        cell.alignment = align_center
        cell.border = borda_fina

    for i, t in enumerate(dados['equipamentos_ti'], start=4):
        ws_ti.row_dimensions[i].height = 19
        ws_ti.cell(row=i, column=1, value=t['id']).alignment = align_center
        ws_ti.cell(row=i, column=2, value=t['equipamento']).alignment = align_left
        ws_ti.cell(row=i, column=3, value=t['marca']).alignment = align_center
        ws_ti.cell(row=i, column=4, value=t['serie']).alignment = align_center
        ws_ti.cell(row=i, column=5, value=t['origem_convenio']).alignment = align_left
        ws_ti.cell(row=i, column=6, value=t['localizacao']).alignment = align_center
        ws_ti.cell(row=i, column=7, value=t['status']).alignment = align_center

        for c_idx in range(1, 8):
            cell = ws_ti.cell(row=i, column=c_idx)
            cell.font = font_normal
            cell.border = borda_fina
            if i % 2 == 0:
                cell.fill = fill_zebra

    for col in ws_ti.columns:
        col_letter = get_column_letter(col[0].column)
        ws_ti.column_dimensions[col_letter].width = 18
    ws_ti.column_dimensions['B'].width = 40
    ws_ti.column_dimensions['E'].width = 28

    # =========================================================================
    # ABA 7: TB_ENTRADAS_COMPRAS
    # =========================================================================
    ws_ent = wb.create_sheet(title="TB_ENTRADAS_COMPRAS")
    ws_ent.views.sheetView[0].showGridLines = True

    headers_ent = [
        "Data Recebimento", "Nº NF-e", "Fornecedor", "Código Item",
        "Descrição do Material", "Quantidade Recebida", "Valor Unitário (R$)",
        "Valor Total (R$)", "Projeto / Fonte Financiadora", "Responsável Conferência"
    ]
    ws_ent.merge_cells("A1:J1")
    ws_ent["A1"] = "HISTÓRICO DE ENTRADAS DE MATERIAIS VIA COMPRAS / NOTAS FISCAIS"
    ws_ent["A1"].font = font_titulo
    ws_ent["A1"].fill = fill_topo
    ws_ent["A1"].alignment = align_center
    ws_ent.row_dimensions[1].height = 28

    ws_ent.row_dimensions[3].height = 22
    for col_idx, h in enumerate(headers_ent, 1):
        cell = ws_ent.cell(row=3, column=col_idx, value=h)
        cell.font = font_header_tab
        cell.fill = fill_header_verde
        cell.alignment = align_center
        cell.border = borda_fina

    ex_ent = [
        ("01/08/2026", "2248", "FORNECEDOR MATERIAIS LTDA", "MAT-0001", "MARRETA 1,00KG", 1, 45.00, 45.00, "MANUTENÇÃO PREDIAL / POLO GERAL", "ALMOXARIFADO"),
        ("05/08/2026", "19330", "FERRAMENTAS MANAUS EIRELI", "MAT-0002", "MARTELO POLIDO 25MM", 1, 38.50, 38.50, "MANUTENÇÃO PREDIAL / POLO GERAL", "ALMOXARIFADO"),
        ("10/08/2026", "26790", "TINTAS E PINCÉIS DO AMAZONAS", "MAT-0004", "PINCEIS 50MM", 5, 12.00, 60.00, "MANUTENÇÃO PREDIAL / POLO GERAL", "ALMOXARIFADO"),
    ]
    for i, row_vals in enumerate(ex_ent, start=4):
        ws_ent.row_dimensions[i].height = 19
        for c_idx, val in enumerate(row_vals, start=1):
            cell = ws_ent.cell(row=i, column=c_idx, value=val)
            cell.font = font_normal
            cell.border = borda_fina
            cell.alignment = align_center if c_idx in [1, 2, 4, 6] else (align_right if c_idx in [7, 8] else align_left)

    for col in ws_ent.columns:
        col_letter = get_column_letter(col[0].column)
        ws_ent.column_dimensions[col_letter].width = 18
    ws_ent.column_dimensions['C'].width = 30
    ws_ent.column_dimensions['E'].width = 35
    ws_ent.column_dimensions['I'].width = 30

    # =========================================================================
    # ABA 8: TB_PARAMETROS
    # =========================================================================
    ws_par = wb.create_sheet(title="TB_PARAMETROS")
    ws_par.views.sheetView[0].showGridLines = True

    ws_par["A1"] = "PROJETOS PDI (ARGUS)"
    ws_par["A1"].font = font_header_tab
    ws_par["A1"].fill = fill_topo
    ws_par["A1"].alignment = align_center
    for i, p in enumerate(dados['projetos'], start=2):
        ws_par.cell(row=i, column=1, value=p).font = font_normal

    ws_par["C1"] = "AMBIENTES (POLO INOVAÇÃO)"
    ws_par["C1"].font = font_header_tab
    ws_par["C1"].fill = fill_topo
    ws_par["C1"].alignment = align_center
    for i, a in enumerate(dados['ambientes'], start=2):
        ws_par.cell(row=i, column=3, value=a).font = font_normal

    ws_par["E1"] = "SOLICITANTES / COLABORADORES"
    ws_par["E1"].font = font_header_tab
    ws_par["E1"].fill = fill_topo
    ws_par["E1"].alignment = align_center
    for i, s in enumerate(dados['solicitantes'], start=2):
        ws_par.cell(row=i, column=5, value=s).font = font_normal

    ws_par["G1"] = "TIPOS DE MOVIMENTAÇÃO"
    ws_par["G1"].font = font_header_tab
    ws_par["G1"].fill = fill_topo
    ws_par["G1"].alignment = align_center
    tipos_mov = [
        "1. SAÍDA DE CONSUMO (BAIXA DEFINITIVA)",
        "2. NOVA CAUTELA (EMPRÉSTIMO DE FERRAMENTA / TI)",
        "3. DEVOLUÇÃO DE CAUTELA"
    ]
    for i, tm in enumerate(tipos_mov, start=2):
        ws_par.cell(row=i, column=7, value=tm).font = font_normal

    ws_par.column_dimensions['A'].width = 35
    ws_par.column_dimensions['B'].width = 4
    ws_par.column_dimensions['C'].width = 32
    ws_par.column_dimensions['D'].width = 4
    ws_par.column_dimensions['E'].width = 30
    ws_par.column_dimensions['F'].width = 4
    ws_par.column_dimensions['G'].width = 40

    print("Salvando arquivo XLSX em:", DESTINO_XLSX)
    wb.save(DESTINO_XLSX)
    print("Sucesso! Arquivo gerado.")

if __name__ == "__main__":
    dados = carregar_dados_legados()
    criar_planilha_operacional(dados)

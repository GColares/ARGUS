import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, Reference

file_path = r"gestao_projetos\execucao_financeira\relatorio_mensal_recursos.xlsx"
wb = openpyxl.load_workbook(file_path)

# Styles Palette (ARGUS Executive Style)
font_family = "Segoe UI"
header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid") # Dark Navy
header_font = Font(name=font_family, size=11, bold=True, color="FFFFFF")

sub_header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid") # Royal Blue
sub_header_font = Font(name=font_family, size=10, bold=True, color="FFFFFF")

zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid") # Very light slate
total_fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid") # Light slate total

card_header_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
card_bg_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

kpi_val_font = Font(name=font_family, size=16, bold=True, color="0F172A")
kpi_lbl_font = Font(name=font_family, size=9, bold=True, color="FFFFFF")
kpi_sub_font = Font(name=font_family, size=8, italic=True, color="64748B")

title_font = Font(name=font_family, size=14, bold=True, color="1E3A8A")
subtitle_font = Font(name=font_family, size=10, italic=True, color="475569")
bold_font = Font(name=font_family, size=10, bold=True, color="0F172A")
normal_font = Font(name=font_family, size=10, color="1E293B")
small_font = Font(name=font_family, size=9, color="475569")
footnote_font = Font(name=font_family, size=8, italic=True, color="64748B")

thin_border_side = Side(border_style="thin", color="CBD5E1")
thick_bottom_side = Side(border_style="medium", color="1E3A8A")
double_bottom_side = Side(border_style="double", color="1E3A8A")

card_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
grid_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
total_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=double_bottom_side)

align_center = Alignment(horizontal="center", vertical="center")
align_left = Alignment(horizontal="left", vertical="center")
align_right = Alignment(horizontal="right", vertical="center")
align_wrap_left = Alignment(horizontal="left", vertical="center", wrap_text=True)

fmt_currency = 'R$ #,##0.00'
fmt_percent = '0.0%'
fmt_date = 'dd/mm/yyyy'

# ==============================================================================
# 1. ABA: Slide 2 - Saúde do Projeto
# ==============================================================================
sheet_name_s2 = "Slide 2 - Saúde do Projeto"
if sheet_name_s2 in wb.sheetnames:
    del wb[sheet_name_s2]
ws2 = wb.create_sheet(title=sheet_name_s2)
ws2.views.sheetView[0].showGridLines = True

# Title Block
ws2.merge_cells("B2:K2")
ws2["B2"] = "POLO DE INOVAÇÃO MANAUS — CONVÊNIO Nº 002/2026 (BIO CAROÇO)"
ws2["B2"].font = title_font

ws2.merge_cells("B3:K3")
ws2["B3"] = "Dashboard de Saúde do Projeto — Posição Fechada em Setembro/2026 (Pronto para Copiar e Colar no Slide 2)"
ws2["B3"].font = subtitle_font

# Helper to format KPI card
def make_kpi_card(ws, start_col, label, val_text, sub_text, bg_color="1E3A8A"):
    c1 = start_col
    c2 = chr(ord(start_col) + 1)
    # Header
    ws.merge_cells(f"{c1}5:{c2}5")
    cell_h = ws[f"{c1}5"]
    cell_h.value = label
    cell_h.font = kpi_lbl_font
    cell_h.fill = PatternFill(start_color=bg_color, end_color=bg_color, fill_type="solid")
    cell_h.alignment = align_center
    
    # Value
    ws.merge_cells(f"{c1}6:{c2}6")
    cell_v = ws[f"{c1}6"]
    cell_v.value = val_text
    cell_v.font = kpi_val_font
    cell_v.fill = card_bg_fill
    cell_v.alignment = align_center
    
    # Subtext
    ws.merge_cells(f"{c1}7:{c2}7")
    cell_s = ws[f"{c1}7"]
    cell_s.value = sub_text
    cell_s.font = kpi_sub_font
    cell_s.fill = card_bg_fill
    cell_s.alignment = align_center
    
    # Borders
    for r in range(5, 8):
        for col_letter in [c1, c2]:
            ws[f"{col_letter}{r}"].border = card_border

# Draw 5 KPI Cards
make_kpi_card(ws2, "B", "SALDO DISPONÍVEL", "R$ 137.823,81", "Fechamento em 30/09/2026", bg_color="0F172A")
make_kpi_card(ws2, "D", "RECEITAS RECEBIDAS", "R$ 280.500,00", "Aportes acumulados em conta", bg_color="1E3A8A")
make_kpi_card(ws2, "F", "TOTAL EXECUTADO", "R$ 147.398,33", "Execução financeira total", bg_color="0284C7")
make_kpi_card(ws2, "H", "RENDIMENTO FINANC.", "R$ 4.722,14", "Rendimento líquido de aplicação", bg_color="059669")
make_kpi_card(ws2, "J", "SPRINTS ACOMP.", "Sprints 14 e 15", "Ciclo operacional ativo", bg_color="475569")

# Table Section Header
ws2.merge_cells("B9:K9")
ws2["B9"] = "EXECUÇÃO ORÇAMENTÁRIA POR RUBRICA — ORÇAMENTO • EXECUTADO • DISPONÍVEL"
ws2["B9"].font = Font(name=font_family, size=11, bold=True, color="FFFFFF")
ws2["B9"].fill = header_fill
ws2["B9"].alignment = align_center

# Table Column Headers
headers_s2 = [
    ("B", "C", "Rubrica Orçamentária", align_left),
    ("D", "E", "Orçamento (R$)", align_right),
    ("F", "G", "Executado (R$)", align_right),
    ("H", "I", "Disponível (R$)", align_right),
    ("J", "K", "Exec. %", align_center)
]

for c1, c2, text, align in headers_s2:
    ws2.merge_cells(f"{c1}10:{c2}10")
    cell = ws2[f"{c1}10"]
    cell.value = text
    cell.font = sub_header_font
    cell.fill = sub_header_fill
    cell.alignment = align
    for r in [10]:
        for col in [c1, c2]:
            ws2[f"{col}{r}"].border = grid_border

rows_s2 = [
    ("Recursos Humanos – Bolsas P&D", 458000.00, 134250.00, 323750.00, 0.293),
    ("Recursos Humanos Indiretos", 22400.00, 0.00, 22400.00, 0.000),
    ("Serviços de Terceiros PJ (Rateio Internet)", 8937.00, 257.15, 8679.85, 0.029),
    ("Tributos / ISS FAEPI", 5500.00, 4125.00, 1375.00, 0.750),
    ("Tarifas Bancárias (Conta SEBRAE)", 1000.00, 141.68, 858.32, 0.142),
    ("Despesa de Suporte Operacional (DOA)", 72263.00, 8400.00, 63863.00, 0.116),
]

current_r = 11
for i, (rubrica, orc, exec_val, disp, pct) in enumerate(rows_s2):
    row_fill = zebra_fill if i % 2 == 1 else PatternFill(fill_type=None)
    
    ws2.merge_cells(f"B{current_r}:C{current_r}")
    ws2[f"B{current_r}"] = rubrica
    ws2[f"B{current_r}"].font = normal_font
    ws2[f"B{current_r}"].alignment = align_left
    
    ws2.merge_cells(f"D{current_r}:E{current_r}")
    ws2[f"D{current_r}"] = orc
    ws2[f"D{current_r}"].font = normal_font
    ws2[f"D{current_r}"].number_format = fmt_currency
    ws2[f"D{current_r}"].alignment = align_right
    
    ws2.merge_cells(f"F{current_r}:G{current_r}")
    ws2[f"F{current_r}"] = exec_val
    ws2[f"F{current_r}"].font = normal_font
    ws2[f"F{current_r}"].number_format = fmt_currency
    ws2[f"F{current_r}"].alignment = align_right
    
    ws2.merge_cells(f"H{current_r}:I{current_r}")
    ws2[f"H{current_r}"] = disp
    ws2[f"H{current_r}"].font = normal_font
    ws2[f"H{current_r}"].number_format = fmt_currency
    ws2[f"H{current_r}"].alignment = align_right
    
    ws2.merge_cells(f"J{current_r}:K{current_r}")
    ws2[f"J{current_r}"] = pct
    ws2[f"J{current_r}"].font = normal_font
    ws2[f"J{current_r}"].number_format = fmt_percent
    ws2[f"J{current_r}"].alignment = align_center
    
    for col_l in ["B", "C", "D", "E", "F", "G", "H", "I", "J", "K"]:
        c = ws2[f"{col_l}{current_r}"]
        c.border = grid_border
        if row_fill.fill_type:
            c.fill = row_fill
            
    current_r += 1

# Total Row
ws2.merge_cells(f"B{current_r}:C{current_r}")
ws2[f"B{current_r}"] = "TOTAL DO PROJETO"
ws2[f"B{current_r}"].font = bold_font
ws2[f"B{current_r}"].alignment = align_left

ws2.merge_cells(f"D{current_r}:E{current_r}")
ws2[f"D{current_r}"] = 568100.00
ws2[f"D{current_r}"].font = bold_font
ws2[f"D{current_r}"].number_format = fmt_currency
ws2[f"D{current_r}"].alignment = align_right

ws2.merge_cells(f"F{current_r}:G{current_r}")
ws2[f"F{current_r}"] = 147173.83
ws2[f"F{current_r}"].font = bold_font
ws2[f"F{current_r}"].number_format = fmt_currency
ws2[f"F{current_r}"].alignment = align_right

ws2.merge_cells(f"H{current_r}:I{current_r}")
ws2[f"H{current_r}"] = 420926.17
ws2[f"H{current_r}"].font = bold_font
ws2[f"H{current_r}"].number_format = fmt_currency
ws2[f"H{current_r}"].alignment = align_right

ws2.merge_cells(f"J{current_r}:K{current_r}")
ws2[f"J{current_r}"] = 0.259
ws2[f"J{current_r}"].font = bold_font
ws2[f"J{current_r}"].number_format = fmt_percent
ws2[f"J{current_r}"].alignment = align_center

for col_l in ["B", "C", "D", "E", "F", "G", "H", "I", "J", "K"]:
    c = ws2[f"{col_l}{current_r}"]
    c.border = total_border
    c.fill = total_fill

current_r += 1
ws2.merge_cells(f"B{current_r}:K{current_r}")
ws2[f"B{current_r}"] = "* Posição em 30/09/2026. Aportado: R$ 280.500,00. Rendimentos líquidos: R$ 4.722,14. Saldo em caixa: R$ 137.823,81. Tarifas Empresa/EMBRAPII (R$ 224,50) pagas c/ rendimentos."
ws2[f"B{current_r}"].font = footnote_font
ws2[f"B{current_r}"].alignment = align_left


# ==============================================================================
# 2. ABA: Slide 3 - Desembolso & Contas
# ==============================================================================
sheet_name_s3 = "Slide 3 - Desembolso & Contas"
if sheet_name_s3 in wb.sheetnames:
    del wb[sheet_name_s3]
ws3 = wb.create_sheet(title=sheet_name_s3)
ws3.views.sheetView[0].showGridLines = True

# Title Block
ws3.merge_cells("B2:K2")
ws3["B2"] = "CONV. 002/2026 — DESEMBOLSO E EXECUÇÃO ORÇAMENTÁRIA (SETEMBRO/2026)"
ws3["B2"].font = title_font

ws3.merge_cells("B3:K3")
ws3["B3"] = "Contas Bancárias: 15334-6 (Empresa), 15335-4 (SEBRAE), 15338-9 (EMBRAPII) — Pronto para Copiar e Colar no Slide 3"
ws3["B3"].font = subtitle_font

# Left Table: Parcelas Recebidas
ws3.merge_cells("B5:F5")
ws3["B5"] = "PARCELAS RECEBIDAS (ENTRADAS DE RECEITA)"
ws3["B5"].font = header_font
ws3["B5"].fill = header_fill
ws3["B5"].alignment = align_center

headers_s3_l = [
    ("B", "Parcela", align_center),
    ("C", "Nº Doc.", align_center),
    ("D", "Data Pagto", align_center),
    ("E", "Valor (R$)", align_right),
    ("F", "Acumulado (R$)", align_right)
]

for col, text, align in headers_s3_l:
    cell = ws3[f"{col}6"]
    cell.value = text
    cell.font = sub_header_font
    cell.fill = sub_header_fill
    cell.alignment = align
    cell.border = grid_border

parcelas_data = [
    ("01/03 EMB", "Ordem Banc.", "17/06/2026", 103000.00, 103000.00),
    ("01/04 Emp", "NFSe 106", "01/07/2026", 27500.00, 130500.00),
    ("Única SEB", "Aporte Único", "08/07/2026", 150000.00, 280500.00),
    ("02/04 Emp", "—", "Prev. Out/26", 27500.00, "pendente"),
    ("02/03 EMB", "—", "Prev. Out/26", 103000.00, "pendente"),
    ("03/04 Emp", "—", "Prev. Dez/26", 27500.00, "pendente"),
    ("03/03 EMB", "—", "Prev. Jan/27", 103000.00, "pendente"),
]

row_s3 = 7
for i, (parc, doc, dt, val, acum) in enumerate(parcelas_data):
    r_fill = zebra_fill if i % 2 == 1 else PatternFill(fill_type=None)
    ws3[f"B{row_s3}"] = parc
    ws3[f"B{row_s3}"].font = normal_font
    ws3[f"B{row_s3}"].alignment = align_center
    
    ws3[f"C{row_s3}"] = doc
    ws3[f"C{row_s3}"].font = normal_font
    ws3[f"C{row_s3}"].alignment = align_center
    
    ws3[f"D{row_s3}"] = dt
    ws3[f"D{row_s3}"].font = normal_font
    ws3[f"D{row_s3}"].alignment = align_center
    
    ws3[f"E{row_s3}"] = val
    ws3[f"E{row_s3}"].font = normal_font
    ws3[f"E{row_s3}"].number_format = fmt_currency
    ws3[f"E{row_s3}"].alignment = align_right
    
    ws3[f"F{row_s3}"] = acum
    ws3[f"F{row_s3}"].font = normal_font
    if isinstance(acum, (int, float)):
        ws3[f"F{row_s3}"].number_format = fmt_currency
        ws3[f"F{row_s3}"].alignment = align_right
    else:
        ws3[f"F{row_s3}"].alignment = align_center
        
    for col_l in ["B", "C", "D", "E", "F"]:
        c = ws3[f"{col_l}{row_s3}"]
        c.border = grid_border
        if r_fill.fill_type:
            c.fill = r_fill
    row_s3 += 1

# Total Row Left
ws3.merge_cells(f"B{row_s3}:D{row_s3}")
ws3[f"B{row_s3}"] = "TOTAL RECEBIDO"
ws3[f"B{row_s3}"].font = bold_font
ws3[f"B{row_s3}"].alignment = align_left

ws3.merge_cells(f"E{row_s3}:F{row_s3}")
ws3[f"E{row_s3}"] = 280500.00
ws3[f"E{row_s3}"].font = bold_font
ws3[f"E{row_s3}"].number_format = fmt_currency
ws3[f"E{row_s3}"].alignment = align_right

for col_l in ["B", "C", "D", "E", "F"]:
    ws3[f"{col_l}{row_s3}"].border = total_border
    ws3[f"{col_l}{row_s3}"].fill = total_fill

row_s3 += 1
ws3.merge_cells(f"B{row_s3}:F{row_s3}")
ws3[f"B{row_s3}"] = "Receitas recebidas: R$ 280.500,00 (49,3% do convênio). Aportes pendentes: R$ 288.500,00."
ws3[f"B{row_s3}"].font = footnote_font
ws3[f"B{row_s3}"].alignment = align_left

# Right Box 1: Resumo Financeiro Consolidado
ws3.merge_cells("H5:K5")
ws3["H5"] = "RESUMO FINANCEIRO CONSOLIDADO"
ws3["H5"].font = header_font
ws3["H5"].fill = header_fill
ws3["H5"].alignment = align_center

resumo_items = [
    ("Créditos de setembro (Rend. Bruto)", 332.27),
    ("Débitos de setembro (Pagamentos)", 61440.33),
    ("Saldo Financeiro em 30/09", 137823.81)
]

r_box1 = 6
for lbl, val in resumo_items:
    ws3.merge_cells(f"H{r_box1}:I{r_box1}")
    ws3[f"H{r_box1}"] = lbl
    ws3[f"H{r_box1}"].font = bold_font if "Saldo" in lbl else normal_font
    ws3[f"H{r_box1}"].alignment = align_left
    
    ws3.merge_cells(f"J{r_box1}:K{r_box1}")
    ws3[f"J{r_box1}"] = val
    ws3[f"J{r_box1}"].font = bold_font if "Saldo" in lbl else normal_font
    ws3[f"J{r_box1}"].number_format = fmt_currency
    ws3[f"J{r_box1}"].alignment = align_right
    
    for c_letter in ["H", "I", "J", "K"]:
        ws3[f"{c_letter}{r_box1}"].border = grid_border
        if "Saldo" in lbl:
            ws3[f"{c_letter}{r_box1}"].fill = total_fill
    r_box1 += 1

# Right Box 2: Rendimentos de Aplicação Financeira
r_box2 = 10
ws3.merge_cells(f"H{r_box2}:K{r_box2}")
ws3[f"H{r_box2}"] = "RENDIMENTOS DE APLICAÇÃO FINANCEIRA"
ws3[f"H{r_box2}"].font = header_font
ws3[f"H{r_box2}"].fill = PatternFill(start_color="059669", end_color="059669", fill_type="solid") # Emerald Green
ws3[f"H{r_box2}"].alignment = align_center

rend_items = [
    ("Saldo inicial acumulado (Ago)", 4414.24),
    ("Setembro/2026 – bruto", 332.27),
    ("Setembro/2026 – IRRF retido", 24.37),
    ("Acumulado Líquido (30/09)", 4722.14)
]

r_box2 += 1
for lbl, val in rend_items:
    ws3.merge_cells(f"H{r_box2}:I{r_box2}")
    ws3[f"H{r_box2}"] = lbl
    ws3[f"H{r_box2}"].font = bold_font if "Acumulado" in lbl else normal_font
    ws3[f"H{r_box2}"].alignment = align_left
    
    ws3.merge_cells(f"J{r_box2}:K{r_box2}")
    ws3[f"J{r_box2}"] = val
    ws3[f"J{r_box2}"].font = bold_font if "Acumulado" in lbl else normal_font
    ws3[f"J{r_box2}"].number_format = fmt_currency
    ws3[f"J{r_box2}"].alignment = align_right
    
    for c_letter in ["H", "I", "J", "K"]:
        ws3[f"{c_letter}{r_box2}"].border = grid_border
        if "Acumulado" in lbl:
            ws3[f"{c_letter}{r_box2}"].fill = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid") # Soft green
    r_box2 += 1


# ==============================================================================
# 3. ABA: Slide 4 - Análise & Atenção
# ==============================================================================
sheet_name_s4 = "Slide 4 - Análise & Atenção"
if sheet_name_s4 in wb.sheetnames:
    del wb[sheet_name_s4]
ws4 = wb.create_sheet(title=sheet_name_s4)
ws4.views.sheetView[0].showGridLines = True

# Title Block
ws4.merge_cells("B2:K2")
ws4["B2"] = "CONV. 002/2026 — ANÁLISE DE EXECUÇÃO E PONTOS DE ATENÇÃO (SETEMBRO/2026)"
ws4["B2"].font = title_font

ws4.merge_cells("B3:K3")
ws4["B3"] = "Percentuais de Execução por Rubrica e Destaques Gerenciais — Pronto para Copiar e Colar no Slide 4"
ws4["B3"].font = subtitle_font

# Table Left: % Execução por Rubrica
ws4.merge_cells("B5:E5")
ws4["B5"] = "% DE EXECUÇÃO POR RUBRICA ORÇAMENTÁRIA"
ws4["B5"].font = header_font
ws4["B5"].fill = header_fill
ws4["B5"].alignment = align_center

ws4.merge_cells("B6:D6")
ws4["B6"] = "Rubrica Orçamentária"
ws4["B6"].font = sub_header_font
ws4["B6"].fill = sub_header_fill
ws4["B6"].alignment = align_left

ws4["E6"] = "% Exec."
ws4["E6"].font = sub_header_font
ws4["E6"].fill = sub_header_fill
ws4["E6"].alignment = align_center

for col in ["B", "C", "D", "E"]:
    ws4[f"{col}6"].border = grid_border

chart_data_rows = [
    ("Recursos Humanos Diretos (Bolsas)", 0.293),
    ("Recursos Humanos Indiretos", 0.000),
    ("Tributos / ISS FAEPI", 0.750),
    ("Tarifas Bancárias (SEBRAE)", 0.142),
    ("Serviços Terceiros PJ (Rateio)", 0.029),
    ("Despesa Suporte Operacional (DOA)", 0.116)
]

r_s4 = 7
for i, (rubrica, pct) in enumerate(chart_data_rows):
    r_fill = zebra_fill if i % 2 == 1 else PatternFill(fill_type=None)
    ws4.merge_cells(f"B{r_s4}:D{r_s4}")
    ws4[f"B{r_s4}"] = rubrica
    ws4[f"B{r_s4}"].font = normal_font
    ws4[f"B{r_s4}"].alignment = align_left
    
    ws4[f"E{r_s4}"] = pct
    ws4[f"E{r_s4}"].font = bold_font
    ws4[f"E{r_s4}"].number_format = fmt_percent
    ws4[f"E{r_s4}"].alignment = align_center
    
    for c_letter in ["B", "C", "D", "E"]:
        c = ws4[f"{c_letter}{r_s4}"]
        c.border = grid_border
        if r_fill.fill_type:
            c.fill = r_fill
    r_s4 += 1

# Insert Horizontal Bar Chart
chart = BarChart()
chart.type = "bar" # horizontal bar chart
chart.style = 10
chart.title = "% de Execução por Rubrica Orçamentária"
chart.y_axis.title = "Rubrica"
chart.x_axis.title = "% Executado"
chart.x_axis.number_format = '0.0%'
chart.legend = None
chart.width = 16
chart.height = 10

data_ref = Reference(ws4, min_col=5, min_row=6, max_row=12) # % Exec
cats_ref = Reference(ws4, min_col=2, min_row=7, max_row=12) # Rubricas
chart.add_data(data_ref, titles_from_data=True)
chart.set_categories(cats_ref)
ws4.add_chart(chart, "B14")

# Right Side Cards (Cards de Resumo e Pontos de Atenção)
# Card 1: Execução Geral
ws4.merge_cells("G5:K5")
ws4["G5"] = "EXECUÇÃO ACUMULADA GERAL"
ws4["G5"].font = kpi_lbl_font
ws4["G5"].fill = header_fill
ws4["G5"].alignment = align_center

ws4.merge_cells("G6:K6")
ws4["G6"] = "25,9%"
ws4["G6"].font = Font(name=font_family, size=20, bold=True, color="1E3A8A")
ws4["G6"].fill = card_bg_fill
ws4["G6"].alignment = align_center

ws4.merge_cells("G7:K7")
ws4["G7"] = "R$ 147.398,33 executados de R$ 568.100,00 do orçamento total"
ws4["G7"].font = subtitle_font
ws4["G7"].fill = card_bg_fill
ws4["G7"].alignment = align_center

for r in range(5, 8):
    for col_l in ["G", "H", "I", "J", "K"]:
        ws4[f"{col_l}{r}"].border = grid_border

# Card 2: Saldo em Caixa
ws4.merge_cells("G9:K9")
ws4["G9"] = "SALDO FINANCEIRO DISPONÍVEL"
ws4["G9"].font = kpi_lbl_font
ws4["G9"].fill = PatternFill(start_color="059669", end_color="059669", fill_type="solid")
ws4["G9"].alignment = align_center

ws4.merge_cells("G10:K10")
ws4["G10"] = "R$ 137.823,81"
ws4["G10"].font = Font(name=font_family, size=20, bold=True, color="059669")
ws4["G10"].fill = card_bg_fill
ws4["G10"].alignment = align_center

ws4.merge_cells("G11:K11")
ws4["G11"] = "Disponibilidade imediata em 30/09/2026 (3 contas)"
ws4["G11"].font = subtitle_font
ws4["G11"].fill = card_bg_fill
ws4["G11"].alignment = align_center

for r in range(9, 12):
    for col_l in ["G", "H", "I", "J", "K"]:
        ws4[f"{col_l}{r}"].border = grid_border

# Card 3: Pontos de Atenção (Caixa Formatada)
ws4.merge_cells("G13:K13")
ws4["G13"] = "PONTOS DE ATENÇÃO — SETEMBRO/2026"
ws4["G13"].font = header_font
ws4["G13"].fill = PatternFill(start_color="D97706", end_color="D97706", fill_type="solid") # Amber 600
ws4["G13"].alignment = align_center

pontos = [
    "• Integralização SEBRAE: Aporte 100% integralizado em conta única (R$ 150.000,00), garantindo liquidez contínua.",
    "• Regularidade de Bolsas: 100% das bolsas do 1º trimestre quitadas e conciliadas com a FAEPI (34 ordens bancárias).",
    "• Próximos Aportes: Empresa Parcela 02/04 (R$ 27,5k) e EMBRAPII Parcela 02/03 (R$ 103k) previstas p/ o 4º mês.",
    "• Despesas Operacionais: Auxiliar Administrativo alocado em DSO (R$ 8,4k executados / 11,6%). Tarifas SEBRAE com R$ 858,32 de saldo."
]

r_pt = 14
for pt in pontos:
    ws4.merge_cells(f"G{r_pt}:K{r_pt}")
    ws4[f"G{r_pt}"] = pt
    ws4[f"G{r_pt}"].font = normal_font
    ws4[f"G{r_pt}"].alignment = align_wrap_left
    ws4[f"G{r_pt}"].fill = PatternFill(start_color="FFFBEB", end_color="FFFBEB", fill_type="solid") # Warm amber tint
    for col_l in ["G", "H", "I", "J", "K"]:
        ws4[f"{col_l}{r_pt}"].border = grid_border
    ws4.row_dimensions[r_pt].height = 24
    r_pt += 1

# Adjust Column Widths across all 3 sheets
for ws in [ws2, ws3, ws4]:
    ws.column_dimensions["A"].width = 3
    for col_l in ["B", "C", "D", "E", "F", "G", "H", "I", "J", "K"]:
        ws.column_dimensions[col_l].width = 15
    ws.column_dimensions["B"].width = 22
    ws.column_dimensions["C"].width = 16

# Save workbook
wb.save(file_path)
print("Successfully created the 3 dashboard sheets in relatorio_mensal_recursos.xlsx!")

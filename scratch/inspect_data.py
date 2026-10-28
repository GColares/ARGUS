import os
import sys
import openpyxl

base_dir = r"C:\Projetos\ARGUS\gestao_projetos\execucao_financeira"
fin_file = os.path.join(base_dir, "execucao_financeira.xlsx")
conv_dir = os.path.join(base_dir, "dados-conveniar")

print("=" * 60)
print("INSPEÇÃO DE execucao_financeira.xlsx")
print("=" * 60)

wb_fin = openpyxl.load_workbook(fin_file, data_only=True)
print("Sheet names:", wb_fin.sheetnames)

for sname in wb_fin.sheetnames:
    ws = wb_fin[sname]
    print(f"\n--- Sheet: {sname} ---")
    print(f"Dimensions: {ws.dimensions}, Max row: {ws.max_row}, Max col: {ws.max_column}")
    print(f"Tables in sheet: {[t.name for t in ws.tables.values()] if hasattr(ws, 'tables') else 'None'}")
    
    # Imprimir as 5 primeiras linhas
    for r in range(1, min(6, ws.max_row + 1)):
        vals = [ws.cell(r, c).value for c in range(1, min(15, ws.max_column + 1))]
        print(f"  Row {r}: {vals}")

# Detalhes da aba extrato_bancario
ws_ext = wb_fin["extrato_bancario"]
headers = [ws_ext.cell(1, c).value for c in range(1, ws_ext.max_column + 1)]
print(f"\nHeaders extrato_bancario ({len(headers)} cols):")
for i, h in enumerate(headers, 1):
    print(f"  Col {i}: {h}")

# Estatísticas dos dados existentes em extrato_bancario
contas_existentes = set()
tipos_existentes = set()
rubricas_existentes = set()
movimentos_existentes = set()

for r in range(2, ws_ext.max_row + 1):
    c_val = ws_ext.cell(r, 4).value # conta
    r_val = ws_ext.cell(r, 5).value # rubrica
    m_val = ws_ext.cell(r, 7).value # movimento
    t_val = ws_ext.cell(r, 8).value # tipo
    if c_val is not None: contas_existentes.add(c_val)
    if r_val is not None: rubricas_existentes.add(r_val)
    if m_val is not None: movimentos_existentes.add(m_val)
    if t_val is not None: tipos_existentes.add(t_val)

print("\nContas em extrato_bancario:", contas_existentes)
print("\nRubricas em extrato_bancario:", rubricas_existentes)
print("\nTipos em extrato_bancario:", tipos_existentes)
print("\nMovimentos em extrato_bancario:", movimentos_existentes)

print("\n" + "=" * 60)
print("INSPEÇÃO DOS ARQUIVOS DADOS-CONVENIAR")
print("=" * 60)

for fname in sorted(os.listdir(conv_dir)):
    if not fname.endswith(".xlsx"): continue
    fpath = os.path.join(conv_dir, fname)
    print(f"\n>>> Arquivo: {fname} <<<")
    wb_c = openpyxl.load_workbook(fpath, data_only=True)
    print("Sheets:", wb_c.sheetnames)
    ws_c = wb_c[wb_c.sheetnames[0]]
    print(f"Dimensions: {ws_c.dimensions}, Max row: {ws_c.max_row}, Max col: {ws_c.max_column}")
    
    # Imprimir até 15 primeiras linhas
    for r in range(1, min(15, ws_c.max_row + 1)):
        vals = [ws_c.cell(r, c).value for c in range(1, min(15, ws_c.max_column + 1))]
        if any(v is not None for v in vals):
            print(f"  Row {r}: {vals}")

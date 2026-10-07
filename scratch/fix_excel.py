import zipfile
import shutil
import xml.etree.ElementTree as ET

src_bak = r"gestao_projetos\execucao_financeira\relatorio_mensal_recursos.xlsx.bak"
cur_file = r"gestao_projetos\execucao_financeira\relatorio_mensal_recursos.xlsx"
out_test = r"scratch\fixed.xlsx"

# Let's inspect what is in cur_file vs src_bak
with zipfile.ZipFile(src_bak, 'r') as zb, zipfile.ZipFile(cur_file, 'r') as zc, zipfile.ZipFile(out_test, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
    # 1. Copy all files from cur_file
    for item in zc.infolist():
        data = zc.read(item.filename)
        
        # If it's a .rels file, fix leading slashes
        if item.filename.endswith('.rels'):
            text = data.decode('utf-8')
            # Replace Target="/xl/drawings/ with Target="../drawings/
            text = text.replace('Target="/xl/drawings/', 'Target="../drawings/')
            text = text.replace('Target="/xl/tables/', 'Target="../tables/')
            text = text.replace('Target="/xl/charts/', 'Target="../charts/')
            data = text.encode('utf-8')
            
        zout.writestr(item, data)
        
    # 2. Restore dropped files from zb if missing in zc
    missing_files = [
        'xl/charts/colors1.xml',
        'xl/charts/style1.xml',
        'xl/charts/_rels/chart1.xml.rels',
        'xl/calcChain.xml'
    ]
    for mf in missing_files:
        if mf in zb.namelist() and mf not in zc.namelist():
            zout.writestr(mf, zb.read(mf))
            print(f"Restored: {mf}")

print("Fixed archive created at:", out_test)

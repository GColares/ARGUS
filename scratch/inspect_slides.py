import zipfile
import xml.etree.ElementTree as ET

pptx_path = r'gestao_projetos\execucao_financeira\2026-09_Acompanhamento_Conv002_2026_BioCaroco_Setembro_2026-teste.pptx'

NS = {
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
}

with zipfile.ZipFile(pptx_path, 'r') as z:
    for i in [1, 2, 3, 4]:
        root = ET.fromstring(z.read(f'ppt/slides/slide{i}.xml'))
        print(f"\n==================== SLIDE {i} ====================")
        
        # Shapes
        for sp in root.findall('.//p:sp', NS):
            cNvPr = sp.find('.//p:nvSpPr/p:cNvPr', NS)
            name = cNvPr.get('name') if cNvPr is not None else 'Unknown'
            sp_id = cNvPr.get('id') if cNvPr is not None else '?'
            
            paras = []
            for p in sp.findall('.//a:p', NS):
                p_text = ''.join([t.text for t in p.findall('.//a:t', NS) if t.text])
                if p_text:
                    paras.append(p_text)
            if paras:
                print(f"[Shape {sp_id}: {name}] -> " + " // ".join(paras))
        
        # Tables
        for gf in root.findall('.//p:graphicFrame', NS):
            cNvPr = gf.find('.//p:nvGraphicFramePr/p:cNvPr', NS)
            name = cNvPr.get('name') if cNvPr is not None else 'Unknown'
            gf_id = cNvPr.get('id') if cNvPr is not None else '?'
            
            tbl = gf.find('.//a:tbl', NS)
            if tbl is not None:
                print(f"\n[Table {gf_id}: {name}]")
                for tr in tbl.findall('.//a:tr', NS):
                    cells = []
                    for tc in tr.findall('.//a:tc', NS):
                        cell_text = ' '.join([t.text for t in tc.findall('.//a:t', NS) if t.text])
                        cells.append(cell_text.strip())
                    print("  ROW:", " | ".join(cells))

import zipfile
import xml.etree.ElementTree as ET

pptx_path = r'gestao_projetos\execucao_financeira\2026-09_Acompanhamento_Conv002_2026_BioCaroco_Setembro_2026-teste.pptx'

NS = {
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
}

with zipfile.ZipFile(pptx_path, 'r') as z:
    for slide_num in [2, 3, 4]:
        root = ET.fromstring(z.read(f'ppt/slides/slide{slide_num}.xml'))
        print(f"\n==================== SLIDE {slide_num} FULL SHAPES ====================")
        for sp in root.findall('.//p:sp', NS):
            cNvPr = sp.find('.//p:nvSpPr/p:cNvPr', NS)
            name = cNvPr.get('name') if cNvPr is not None else 'Unknown'
            sp_id = cNvPr.get('id') if cNvPr is not None else '?'
            
            # transform
            xfrm = sp.find('.//p:spPr/a:xfrm', NS)
            off = xfrm.find('a:off', NS) if xfrm is not None else None
            ext = xfrm.find('a:ext', NS) if xfrm is not None else None
            pos_str = ""
            if off is not None and ext is not None:
                pos_str = f"x={off.get('x')}, y={off.get('y')}, cx={ext.get('cx')}, cy={ext.get('cy')}"
            
            paras = []
            for p in sp.findall('.//a:p', NS):
                runs = []
                for r in p.findall('.//a:r', NS):
                    t = r.find('a:t', NS)
                    if t is not None and t.text:
                        runs.append(t.text)
                if runs:
                    paras.append("".join(runs))
            
            text_str = " // ".join(paras)
            print(f"ID {sp_id:4s} | {name:25s} | {pos_str} | Text: '{text_str}'")

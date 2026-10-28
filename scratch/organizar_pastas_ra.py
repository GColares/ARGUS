import os
import re
import shutil

base_dir = os.path.abspath('gestao_projetos/media/modelos')
pattern = re.compile(r'^Relatorio_de_Atividades_(.+?)_-_Parcela_(\d+)_de_(\d+)\.docx$', re.IGNORECASE)

files = [f for f in os.listdir(base_dir) if os.path.isfile(os.path.join(base_dir, f))]
print(f"Total de arquivos encontrados em {base_dir}: {len(files)}")

movidos = 0
for f in files:
    m = pattern.match(f)
    if m:
        bolsista_nome = m.group(1).strip()
        if '{{' in bolsista_nome:
            continue
        
        # Sanitizar caracteres proibidos
        chars_proibidos = ['\\', '/', '*', '?', ':', '"', '<', '>', '|']
        bolsista_pasta = bolsista_nome
        for ch in chars_proibidos:
            bolsista_pasta = bolsista_pasta.replace(ch, '_')
            
        dest_dir = os.path.join(base_dir, bolsista_pasta)
        os.makedirs(dest_dir, exist_ok=True)
        
        src_path = os.path.join(base_dir, f)
        dest_path = os.path.join(dest_dir, f)
        
        shutil.move(src_path, dest_path)
        print(f"Movido: {f} -> {bolsista_pasta}/")
        movidos += 1

print(f"\nEngenharia reversa concluida! Total de arquivos organizados em pastas: {movidos}")

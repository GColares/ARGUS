from decimal import Decimal
import os
import pdfplumber
import re
from .models import FiltroImportacao

def limpar_lixo_digital(texto):
    if not texto: return ""
    # Remove resíduos de assinaturas digitais e normaliza espaços
    texto_limpo = re.sub(r'\(?cid:\s*\d+\)?', '', str(texto), flags=re.IGNORECASE)
    texto_limpo = texto_limpo.replace('\n', ' ').strip()
    return re.sub(r'\s+', ' ', texto_limpo)

def limpar_valor(texto):
    """Transforma string de moeda em número Decimal (Python)."""
    if not texto: return Decimal('0.00')
    s = str(texto).strip()
    # Busca apenas os números, pontos e vírgulas
    match = re.search(r'([\d\.,]+)', s)
    if not match: return Decimal('0.00')
    limpo = match.group(1)
    try:
        # Lógica para converter padrão brasileiro (1.234,56) para americano (1234.56)
        if '.' in limpo and ',' in limpo:
            limpo = limpo.replace('.', '').replace(',', '.')
        elif ',' in limpo:
            limpo = limpo.replace(',', '.')
        return Decimal(limpo).quantize(Decimal('0.00'))
    except:
        return Decimal('0.00')

def extrair_linhas_brutas_faepi(pdf_path, linhas_cabecalho=5, pagina_inicio=None, pagina_fim=None):
    """
    ESTÁGIO 1: Extração com limite de páginas e interrupção forçada.
    """
    # Ajuste dos índices (PDFplumber começa em 0. Página 4 = índice 3)
    idx_inicio = (int(pagina_inicio) - 1) if pagina_inicio else 3
    idx_fim = int(pagina_fim) if pagina_fim else None # Se None, vai até o fim

    print(f"\n--- [ARGUS] EXTRAÇÃO INTEGRAL: PÁGINA {idx_inicio + 1} ATÉ {pagina_fim or 'FIM'} ---")
    
    filtros_usuario = list(FiltroImportacao.objects.filter(ativo=True).values_list('termo', flat=True))
    linhas_extraidas = []
    contador_linhas_global = 0

    with pdfplumber.open(pdf_path) as pdf:
        # Fatiamos as páginas EXATAMENTE como você informou (Ex: 4 a 5)
        paginas_alvo = pdf.pages[idx_inicio:idx_fim]

        for num_p, pagina in enumerate(paginas_alvo):
            largura, altura = pagina.width, pagina.height

            v_lines = [
                0.03*largura, 0.08*largura, 0.28*largura, 0.34*largura, 
                0.41*largura, 0.50*largura, 0.58*largura, 0.63*largura, 
                0.68*largura, 0.74*largura, 0.77*largura, 0.80*largura, 
                0.86*largura, 0.91*largura, 0.94*largura, 0.97*largura
            ]
            

            tabela = pagina.extract_table({
                "vertical_strategy": "explicit", 
                "explicit_vertical_lines": v_lines, 
                "horizontal_strategy": "text", 
                "intersection_tolerance": 15
            })
            
            if not tabela: continue

            for linha in tabela:
                contador_linhas_global += 1
                
                # Pula cabeçalho apenas na primeira página do intervalo
                if num_p == 0 and contador_linhas_global <= int(linhas_cabecalho):
                    continue

                dados = [limpar_lixo_digital(c) if c else "" for c in linha]
                linha_completa = " ".join(dados).upper()

# --- FILTROS DE RUÍDO (Baseado no seu arquivo bruto) ---
                # Interrompe se chegar na DANFE
                if "DANFE" in linha_completa or "NOTA FISCAL" in linha_completa:
                    return linhas_extraidas

                # Ignora linhas que são apenas resíduos de assinaturas (como no seu txt)
                termos_assinatura = ["ASSINADO", "PORTAL", "VERIFICAR", "CÓDIGO", "PÁGINA"]
                if any(t in linha_completa for t in termos_assinatura) and len(linha_completa) < 60:
                    continue

                # Só adiciona se a linha não estiver vazia
                if not linha_completa.strip():
                    continue

                while len(dados) < 16: dados.append("")
                linhas_extraidas.append(dados)

# --- GERAÇÃO DO ARQUIVO TXT DE LOG ---
    # Cria o arquivo txt com o mesmo nome do PDF, mas mudando a extensão
    txt_filename = f"{os.path.splitext(pdf_path)[0]}_bruto.txt"
    
    try:
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write(f"   [ARGUS] CONTEÚDO CAPTURADO: {len(linhas_extraidas)} LINHAS\n")
            f.write(f"   ORIGEM: {pdf_path}\n")
            f.write("="*80 + "\n")
            
            for i, linha in enumerate(linhas_extraidas):
                # Escreve a linha inteira no TXT, sem cortar os caracteres
                f.write(f"L{i:03d} | {linha}\n")
                
            f.write("="*80 + "\n")
            
        print(f"--- [ARGUS] LOG GRAVADO COM SUCESSO EM: {txt_filename} ---")
    except Exception as e:
        print(f"--- [ARGUS] ERRO AO CRIAR ARQUIVO TXT: {e} ---")

    return linhas_extraidas
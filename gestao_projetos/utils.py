import re
from docx import Document

def extrair_atividades_texto_docx(arquivo_memoria):
    """
    Varre os parágrafos do documento buscando blocos de Atividades.
    Utiliza extração tolerante a falhas: atributos não encontrados retornam 
    vazio (strings vazias ou None) para preenchimento manual do Coordenador.
    """
    documento = Document(arquivo_memoria)
    texto_completo = "\n".join([p.text for p in documento.paragraphs if p.text.strip()])
    
    # 1. Isola cada bloco de atividade. 
    # Captura o número, o nome na mesma linha e todo o texto até a próxima "Atividade" ou fim do arquivo.
    padrao_bloco = re.compile(
        r"Atividade\s*(\d+):\s*(.*?)(?=\nAtividade\s*\d+:|$)", 
        re.IGNORECASE | re.DOTALL
    )
    
    atividades = []
    
    for match in padrao_bloco.finditer(texto_completo):
        numero = match.group(1).strip()
        # O nome pode ter vindo colado com a quebra de linha do corpo, então isolamos a primeira linha
        nome = match.group(2).split('\n')[0].strip() 
        corpo = match.group(2)
        
        # 2. Buscas individuais não-restritivas (se não achar, retorna None)
        # O (?=...) é um lookahead positivo para parar a captura no próximo rótulo provável
        descricao = re.search(r"Descrição:\s*(.*?)(?=\n\s*Justificativa:|\n\s*Entregáveis:|\n\s*Data de início:|$)", corpo, re.IGNORECASE | re.DOTALL)
        justificativa = re.search(r"Justificativa:\s*(.*?)(?=\n\s*Entregáveis:|\n\s*Data de início:|$)", corpo, re.IGNORECASE | re.DOTALL)
        entregaveis = re.search(r"Entregáveis:\s*(.*?)(?=\n\s*Data de início:|$)", corpo, re.IGNORECASE | re.DOTALL)
        
        mes_inicio = re.search(r"Data de início:\s*Mês\s*(\d+)", corpo, re.IGNORECASE)
        mes_fim = re.search(r"Data de fim:\s*Mês\s*(\d+)", corpo, re.IGNORECASE)
        
        # 3. Estrutura o dicionário consolidando dados encontrados e espaços em branco
        atividades.append({
            "numero": numero,
            "nome": nome,
            "descricao": descricao.group(1).strip() if descricao else "",
            "justificativa": justificativa.group(1).strip() if justificativa else "",
            "entregaveis": entregaveis.group(1).strip() if entregaveis else "",
            "mes_inicio_relativo": int(mes_inicio.group(1)) if mes_inicio else None,
            "mes_fim_relativo": int(mes_fim.group(1)) if mes_fim else None
        })
        
    if not atividades:
        return {"erro": "O sistema não conseguiu identificar a estrutura de 'Atividades' no texto submetido. Verifique o padrão do documento."}
        
    return {"sucesso": atividades}

def obter_dados_parcela_excel(numero_termo, parcela):
    """
    Lê a planilha Painel_bolsas.xlsx e retorna (data_inicio, data_fim, carga_horaria) 
    para um número de termo e uma parcela específicos.
    O formato da coluna deve ser 'Intertício R0X'.
    A carga horária é calculada como Carga Horária Total / Parcelas.
    """
    import os
    import pandas as pd
    from datetime import datetime
    from django.conf import settings
    
    caminho_planilha = os.path.join(settings.BASE_DIR, 'gestao_projetos', 'modelos', 'Painel_bolsas.xlsx')
    
    try:
        df = pd.read_excel(caminho_planilha)
        
        # Garante que o número_termo seja tratado como string para comparação
        df['Termo de Bolsa'] = df['Termo de Bolsa'].astype(str).str.strip()
        numero_termo_str = str(numero_termo).strip()
        
        linha = df[df['Termo de Bolsa'] == numero_termo_str]
        
        if linha.empty:
            return None, None, None
            
        # Calcula Carga Horária da parcela
        carga_total = float(linha.iloc[0].get('Carga Horária', 0))
        qtd_parcelas = float(linha.iloc[0].get('Parcelas', 1))
        carga_horaria = int(carga_total / qtd_parcelas) if qtd_parcelas > 0 else 0
        
        nome_coluna = f'Intertício R{parcela:02d}'
        
        if nome_coluna not in df.columns:
            return None, None, carga_horaria
            
        valor = linha.iloc[0][nome_coluna]
        
        if pd.isna(valor) or not isinstance(valor, str):
            return None, None, carga_horaria
            
        # O formato esperado é 'DD/MM/YY a DD/MM/YY'
        partes = valor.split(' a ')
        if len(partes) != 2:
            return None, None, carga_horaria
            
        # Converte para datetime e formata para 'YYYY-MM-DD' para o Django
        dt_inicio = datetime.strptime(partes[0].strip(), '%d/%m/%y').strftime('%Y-%m-%d')
        dt_fim = datetime.strptime(partes[1].strip(), '%d/%m/%y').strftime('%Y-%m-%d')
        
        return dt_inicio, dt_fim, carga_horaria
        
    except Exception as e:
        print(f"Erro ao ler planilha Painel_bolsas: {str(e)}")
        return None, None, None

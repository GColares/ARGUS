# -*- coding: utf-8 -*-
"""
Script de Carga e Migracao Inicial do Inventario Legado para o SQLite do ARGUS.
Aplica as regras operacionais avancadas:
1. Normalizacao de Unidades (Base m, L, UN vs Embalagem Rolo, Lata, Galao).
2. Enderecamento WMS 3D (Ambiente -> Estrutura -> Posicao).
3. Padronizacao PDM e Codificacao SKU de 6 digitos (010001 a 010090).
4. Parametrizacao de Validade PAO (Period After Opening) para Tintas e Quimicos.
"""
import os
import sys
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARGUS_ROOT = r"C:\ARGUS"
if ARGUS_ROOT not in sys.path:
    sys.path.append(ARGUS_ROOT)
if os.path.join(ARGUS_ROOT, "scripts") not in sys.path:
    sys.path.append(os.path.join(ARGUS_ROOT, "scripts"))

from gerar_planilha_almoxarifado import carregar_dados_legados
from banco import init_db, get_connection

DB_PATH = os.path.join(BASE_DIR, "banco_almoxarifado.db")

def normalizar_item(idx, item_legado):
    sku = f"01{idx:04d}"
    desc = item_legado['descricao'].strip().upper()
    # Limpa caracteres corrompidos de encoding legado se houver
    desc = desc.replace("AMAZNICO", "AMAZONICO").replace("TENSO", "TENSAO").replace("DEMARCAO", "DEMARCACAO")
    desc = desc.replace("FLEXVEL", "FLEXIVEL").replace("", "")
    desc = desc.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")

    cat = item_legado.get('categoria', 'CONSUMO').upper()
    qtd_legada = float(item_legado.get('estoque_inicial', 0) or 0)
    nf = item_legado.get('nf', '')

    unidade_base = "UN"
    embalagem_compra = "UN"
    fator_conversao = 1.0
    validade_pao_dias = 0
    codigo_catmat = ""

    # Endereçamento 3D
    ambiente = "ALMOXARIFADO CENTRAL"
    estrutura = "ESTANTE 01"
    posicao = "PRATELEIRA 01"

    nome_basico = ""
    nome_modificador = ""

    # 1. CABOS ELÉTRICOS
    if "CABO FLEXIVEL" in desc or "CABO ELETRICO" in desc:
        unidade_base = "m"
        codigo_catmat = "389214"
        nome_basico = "CABO ELETRICO"
        nome_modificador = desc.replace("CABO ELETRICO", "").replace("CABO FLEXIVEL", "FLEXIVEL").strip()
        estrutura = "ESTANTE 01 (ELETRICA)"
        posicao = "PRATELEIRA 02"

        if "200MT" in desc or "200M" in desc:
            embalagem_compra = "ROLO 200M"
            fator_conversao = 200.0
        else:
            embalagem_compra = "ROLO 100M"
            fator_conversao = 100.0

    # 2. TINTAS E RESINAS
    elif "TINTA" in desc or "VERNIZ" in desc or "SELADOR" in desc or "ESMALTE" in desc:
        unidade_base = "L"
        codigo_catmat = "454823"
        validade_pao_dias = 60 # 60 dias de validade pós-abertura
        nome_basico = "TINTA"
        nome_modificador = desc.replace("TINTA", "").strip()
        estrutura = "PALETE 01 (TINTAS E QUIMICOS)"
        posicao = "NIVEL CHAO"

        if "19L" in desc:
            embalagem_compra = "LATA 19L"
            fator_conversao = 19.0
        elif "18L" in desc:
            embalagem_compra = "LATA 18L"
            fator_conversao = 18.0
        elif "15L" in desc:
            embalagem_compra = "LATA 15L"
            fator_conversao = 15.0
        elif "3,9L" in desc or "3.9L" in desc:
            embalagem_compra = "GALAO 3.9L"
            fator_conversao = 3.9
        elif "3,6L" in desc or "3.6L" in desc:
            embalagem_compra = "GALAO 3.6L"
            fator_conversao = 3.6
        else:
            embalagem_compra = "LATA 18L"
            fator_conversao = 18.0

    # 3. SOLVENTES / QUÍMICOS
    elif "THINNER" in desc or "AGUARRAS" in desc or "SOLVENTE" in desc:
        unidade_base = "L"
        codigo_catmat = "412589"
        validade_pao_dias = 90
        nome_basico = "SOLVENTE"
        nome_modificador = desc
        estrutura = "PALETE 01 (TINTAS E QUIMICOS)"
        posicao = "PRATELEIRA 01"
        embalagem_compra = "LATA 5L"
        fator_conversao = 5.0

    # 4. FITAS ADESIVAS / ISOLANTES
    elif "FITA" in desc:
        unidade_base = "m"
        codigo_catmat = "284102"
        nome_basico = "FITA ADESIVA"
        nome_modificador = desc.replace("FITA", "").strip()
        estrutura = "ESTANTE 02 (ADESIVOS E FITAS)"
        posicao = "PRATELEIRA 01"

        if "50M" in desc:
            embalagem_compra = "ROLO 50M"
            fator_conversao = 50.0
        elif "20M" in desc:
            embalagem_compra = "ROLO 20M"
            fator_conversao = 20.0
        elif "10M" in desc:
            embalagem_compra = "ROLO 10M"
            fator_conversao = 10.0
        else:
            embalagem_compra = "ROLO"
            fator_conversao = 20.0

    # 5. FERRAMENTAS
    elif cat == "FERRAMENTA":
        unidade_base = "UN"
        embalagem_compra = "UN"
        fator_conversao = 1.0
        codigo_catmat = "150820"
        palavras = desc.split()
        nome_basico = palavras[0] if palavras else "FERRAMENTA"
        nome_modificador = " ".join(palavras[1:]) if len(palavras) > 1 else ""
        if any(e in desc for e in ["FURADEIRA", "PARAFUSADEIRA", "SERRA", "MULTIMETRO"]):
            estrutura = "ARMARIO 02 (FERRAMENTAS ELETRICAS)"
            posicao = "PRATELEIRA 01"
        else:
            estrutura = "ARMARIO 01 (FERRAMENTAS MANUAIS)"
            posicao = "GAVETA 01"

    # 6. DEMAIS MATERIAIS DE CONSUMO (LIXAS, PINCEIS, PARAFUSOS, TUBOS)
    else:
        unidade_base = "UN"
        embalagem_compra = "UN"
        fator_conversao = 1.0
        codigo_catmat = "102340"
        palavras = desc.split()
        nome_basico = palavras[0] if palavras else "MATERIAL"
        nome_modificador = " ".join(palavras[1:]) if len(palavras) > 1 else ""
        estrutura = "ESTANTE 03 (DIVERSOS MANUTENCAO)"
        posicao = "PRATELEIRA 02"

    # Cálculo do estoque inicial na UNIDADE BASE!
    # Ex: se tinha 1 rolo de 100m, o saldo base vira 100.0 metros.
    # Se tinha 2 latas de 18L, o saldo base vira 36.0 litros.
    estoque_inicial_base = qtd_legada * fator_conversao

    return {
        "id": sku,
        "codigo_catmat": codigo_catmat,
        "nome_basico": nome_basico or desc,
        "nome_modificador": nome_modificador,
        "descricao": desc,
        "categoria": cat,
        "unidade_base": unidade_base,
        "embalagem_compra": embalagem_compra,
        "fator_conversao": fator_conversao,
        "estoque_inicial": estoque_inicial_base,
        "estoque_minimo": 2.0 if unidade_base == "UN" else (fator_conversao * 0.25),
        "local_ambiente": ambiente,
        "local_estrutura": estrutura,
        "local_posicao": posicao,
        "validade_pao_dias": validade_pao_dias,
        "nf_origem": nf or "INVENTARIO_LEGADO",
        "motivo_ajuste": "Migração Normalizada PDM/CATMAT e WMS 3D"
    }

def migrar():
    print("Inicializando banco SQLite com o novo schema...")
    conn = get_connection(DB_PATH)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS tb_entradas")
    cur.execute("DROP TABLE IF EXISTS tb_saidas")
    cur.execute("DROP TABLE IF EXISTS tb_fracionados_abertos")
    cur.execute("DROP TABLE IF EXISTS tb_emprestimos_ferramentas")
    cur.execute("DROP TABLE IF EXISTS tb_materiais")
    cur.execute("DROP TABLE IF EXISTS tb_parametros")
    cur.execute("DROP TABLE IF EXISTS tb_fechamentos")
    conn.commit()
    conn.close()

    init_db(DB_PATH)
    conn = get_connection(DB_PATH)
    cur = conn.cursor()

    dados = carregar_dados_legados()

    # 1. Inserir Materiais Normalizados
    itens_inseridos = 0
    for idx, m_legado in enumerate(dados['materiais'], 1):
        m = normalizar_item(idx, m_legado)
        cur.execute("""
        INSERT INTO tb_materiais (
            id, codigo_catmat, nome_basico, nome_modificador, descricao, categoria,
            unidade_base, embalagem_compra, fator_conversao, estoque_inicial, estoque_minimo,
            local_ambiente, local_estrutura, local_posicao, validade_pao_dias, nf_origem, motivo_ajuste, ativo
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            m['id'], m['codigo_catmat'], m['nome_basico'], m['nome_modificador'], m['descricao'],
            m['categoria'], m['unidade_base'], m['embalagem_compra'], m['fator_conversao'],
            m['estoque_inicial'], m['estoque_minimo'], m['local_ambiente'], m['local_estrutura'],
            m['local_posicao'], m['validade_pao_dias'], m['nf_origem'], m['motivo_ajuste']
        ))
        itens_inseridos += 1

    print(f"• Materiais e Ferramentas normalizados e inseridos: {itens_inseridos}")

    # 2. Inserir Parâmetros
    for p in dados.get('projetos', []):
        cur.execute("INSERT OR IGNORE INTO tb_parametros (tipo, valor) VALUES ('PROJETO', ?)", (p.strip().upper(),))

    for a in dados.get('ambientes', []):
        cur.execute("INSERT OR IGNORE INTO tb_parametros (tipo, valor) VALUES ('AMBIENTE', ?)", (a.strip().upper(),))

    for s in dados.get('solicitantes', []):
        cur.execute("INSERT OR IGNORE INTO tb_parametros (tipo, valor) VALUES ('SOLICITANTE', ?)", (s.strip().upper(),))

    # Parâmetros padrão essenciais adicionais
    projetos_padrao = ["MANUTENÇÃO PREDIAL / POLO GERAL", "CANTEIROHUB", "PIBIC / INICIAÇÃO CIENTÍFICA", "P&D INDÚSTRIA 4.0"]
    for pr in projetos_padrao:
        cur.execute("INSERT OR IGNORE INTO tb_parametros (tipo, valor) VALUES ('PROJETO', ?)", (pr,))

    ambientes_padrao = ["LSCN - LABORATÓRIO", "OFICINA MECÂNICA", "SUBESTAÇÃO ELÉTRICA", "ÁREA EXTERNA", "SALA DE SERVIDORES"]
    for am in ambientes_padrao:
        cur.execute("INSERT OR IGNORE INTO tb_parametros (tipo, valor) VALUES ('AMBIENTE', ?)", (am,))

    solicitantes_padrao = ["GABRIEL COLARES", "COLABORADORA ALMOXARIFADO", "EQUIPE DE MANUTENÇÃO", "EQUIPE P&D"]
    for so in solicitantes_padrao:
        cur.execute("INSERT OR IGNORE INTO tb_parametros (tipo, valor) VALUES ('SOLICITANTE', ?)", (so,))

    estruturas_padrao = [
        "PALETE 01 (TINTAS E QUIMICOS)",
        "ESTANTE 01 (ELETRICA)",
        "ESTANTE 02 (ADESIVOS E FITAS)",
        "ESTANTE 03 (DIVERSOS MANUTENCAO)",
        "ARMARIO 01 (FERRAMENTAS MANUAIS)",
        "ARMARIO 02 (FERRAMENTAS ELETRICAS)",
        "GAVETEIRO 01 (FIXADORES)"
    ]
    for es in estruturas_padrao:
        cur.execute("INSERT OR IGNORE INTO tb_parametros (tipo, valor) VALUES ('ESTRUTURA', ?)", (es,))

    conn.commit()
    conn.close()
    print("MIGRAÇÃO DE DADOS NORMALIZADOS EXECUTADA COM SUCESSO NO NOVO BANCO!")

if __name__ == "__main__":
    migrar()

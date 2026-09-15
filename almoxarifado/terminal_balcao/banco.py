# -*- coding: utf-8 -*-
"""
Camada de Banco de Dados SQLite Normalizada - Terminal de Balcao do Almoxarifado.
Implementa:
1. Enderecamento WMS 3D: Ambiente -> Estrutura (Estante/Armario) -> Posicao (Prateleira/Gaveta)
2. Dupla Unidade com Fator de Conversao (Unidade Base m, L, UN vs Embalagem Comercial)
3. Controle de Fracionados e Latas Abertas (PAO - Period After Opening)
4. CRUD Completo de Materiais, Entradas, Saidas e Parametros.
"""
import sqlite3
import os
import re
import hashlib
import secrets
from collections import Counter
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "banco_almoxarifado.db")

def get_connection(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS tb_operadores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cpf TEXT NOT NULL UNIQUE,
        nome_completo TEXT NOT NULL,
        email TEXT DEFAULT '',
        telefone TEXT DEFAULT '',
        tipo_vinculo TEXT NOT NULL DEFAULT 'TERCEIRIZADO',
        cargo_funcao TEXT DEFAULT '',
        siape TEXT DEFAULT '',
        empresa_contratada TEXT DEFAULT '',
        login TEXT NOT NULL UNIQUE,
        senha_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        ativo INTEGER DEFAULT 1,
        data_cadastro TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS tb_materiais (
        id TEXT PRIMARY KEY,                       -- SKU Local 6 digitos (ex: 010001)
        codigo_catmat TEXT DEFAULT '',             -- Codigo CATMAT Governo Federal
        nome_basico TEXT NOT NULL,                 -- PDM Nome Basico (ex: TINTA ACRILICA)
        nome_modificador TEXT DEFAULT '',          -- PDM Modificador (ex: SEMIBRILHO BRANCO)
        descricao TEXT NOT NULL,                   -- Descricao Completa
        categoria TEXT NOT NULL,                   -- CONSUMO ou FERRAMENTA
        unidade_base TEXT NOT NULL DEFAULT 'UN',   -- Menor Unidade de Medida (m, L, UN, kg)
        embalagem_compra TEXT DEFAULT 'UN',        -- Embalagem comercial (ex: LATA 15L, ROLO 100M)
        fator_conversao REAL DEFAULT 1.0,          -- Quantas unidades base tem na embalagem
        estoque_inicial REAL DEFAULT 0,            -- Saldo inicial na unidade base
        estoque_minimo REAL DEFAULT 2,             -- Alerta de estoque minimo
        local_ambiente TEXT DEFAULT 'ALMOXARIFADO CENTRAL', -- 1. Sala/Ambiente
        local_estrutura TEXT DEFAULT 'ESTANTE 01',          -- 2. Estante/Armario/Palete
        local_posicao TEXT DEFAULT 'PRATELEIRA 01',         -- 3. Prateleira/Gaveta/Caixa
        validade_pao_dias INTEGER DEFAULT 0,       -- Validade apos aberto (dias, 0 = N/A)
        nf_origem TEXT DEFAULT '',
        motivo_ajuste TEXT DEFAULT '',
        ativo INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS tb_fracionados_abertos (
        id TEXT PRIMARY KEY,                       -- Ex: FRAC-2026-0001
        material_id TEXT NOT NULL,
        data_abertura TEXT NOT NULL,
        validade_pao_dias INTEGER NOT NULL,
        data_vencimento_pao TEXT NOT NULL,
        nivel_atual TEXT DEFAULT '100%',           -- 100%, 75%, 50%, 25%, ESGOTADO
        saldo_remanescente REAL NOT NULL,          -- Saldo em L ou m
        aberto_por TEXT,
        status TEXT DEFAULT 'NO_ALMOXARIFADO',     -- NO_ALMOXARIFADO, EM_USO, ESGOTADO
        FOREIGN KEY (material_id) REFERENCES tb_materiais(id)
    );

    CREATE TABLE IF NOT EXISTS tb_entradas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_hora TEXT NOT NULL,
        nf TEXT DEFAULT 'S/N',
        fornecedor TEXT DEFAULT 'DIVERSOS',
        material_id TEXT NOT NULL,
        quantidade_compra REAL NOT NULL,           -- Qtd na embalagem de compra
        unidade_compra TEXT,
        fator_conversao REAL DEFAULT 1.0,
        quantidade_base REAL NOT NULL,             -- Qtd convertida na unidade base
        valor_unit REAL DEFAULT 0,
        valor_total REAL DEFAULT 0,
        projeto TEXT DEFAULT 'MANUTENÇÃO PREDIAL / POLO GERAL',
        responsavel TEXT DEFAULT 'ALMOXARIFADO CENTRAL',
        observacao TEXT DEFAULT '',
        FOREIGN KEY (material_id) REFERENCES tb_materiais(id)
    );

    CREATE TABLE IF NOT EXISTS tb_saidas (
        id TEXT PRIMARY KEY,
        data_hora TEXT NOT NULL,
        material_id TEXT NOT NULL,
        descricao TEXT NOT NULL,
        quantidade_base REAL NOT NULL,             -- Qtd na unidade base
        unidade_base TEXT NOT NULL,
        solicitante TEXT NOT NULL,
        siape TEXT DEFAULT '',
        projeto TEXT NOT NULL,
        ambiente TEXT NOT NULL,
        finalidade TEXT DEFAULT '',
        tipo_saida TEXT DEFAULT 'CONSUMO',         -- CONSUMO, EMPRESTIMO_FERRAMENTA, SOBRA_CONSUMO
        fracionado_id TEXT,                        -- Se vinculado a uma lata aberta
        comprovante_num TEXT,
        FOREIGN KEY (material_id) REFERENCES tb_materiais(id)
    );

    CREATE TABLE IF NOT EXISTS tb_emprestimos_ferramentas (
        id TEXT PRIMARY KEY,
        material_id TEXT NOT NULL,
        ferramenta_nome TEXT NOT NULL,
        solicitante TEXT NOT NULL,
        siape TEXT DEFAULT '',
        projeto TEXT NOT NULL,
        data_saida TEXT NOT NULL,
        data_prevista TEXT DEFAULT '',
        status TEXT DEFAULT 'EM USO',             -- EM USO, DEVOLVIDO, AVARIADO
        data_retorno TEXT DEFAULT '',
        avarias TEXT DEFAULT '',
        comprovante_num TEXT,
        FOREIGN KEY (material_id) REFERENCES tb_materiais(id)
    );

    CREATE TABLE IF NOT EXISTS tb_parametros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT NOT NULL,                        -- SOLICITANTE, PROJETO, AMBIENTE, ESTRUTURA
        valor TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS tb_solicitantes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cpf TEXT UNIQUE,                           -- CPF 11 dígitos para unicidade e integração com ARGUS
        nome_completo TEXT NOT NULL,                -- Nome civil para filtro e visualização
        ativo INTEGER DEFAULT 1,
        data_cadastro TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS tb_fechamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_hora TEXT NOT NULL,
        total_entradas INTEGER,
        total_saidas INTEGER,
        arquivo_excel TEXT,
        arquivo_backup TEXT,
        caminho_drive TEXT
    );
    """)

    conn.commit()
    conn.close()

    migrar_solicitantes_legados(db_path=db_path)

# ---------------------------------------------------------------------------
# INDICADORES E PAINEL
# ---------------------------------------------------------------------------
def get_indicadores(db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM tb_materiais WHERE ativo = 1")
    total_itens = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM tb_emprestimos_ferramentas WHERE status = 'EM USO'")
    ferramentas_em_uso = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM tb_fracionados_abertos WHERE status != 'ESGOTADO'")
    latas_abertas = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM tb_entradas")
    total_entradas = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM tb_saidas")
    total_saidas = cur.fetchone()[0]

    catalogo = get_catalogo(db_path=db_path)
    itens_baixo = sum(1 for item in catalogo if item['status_estoque'] == 'BAIXO')

    conn.close()
    return {
        "total_itens": total_itens,
        "ferramentas_em_uso": ferramentas_em_uso,
        "latas_abertas": latas_abertas,
        "total_entradas": total_entradas,
        "total_saidas": total_saidas,
        "itens_baixo": itens_baixo
    }

# ---------------------------------------------------------------------------
# CRUD DE MATERIAIS COM ENDEREÇO 3D E UNIDADES
# ---------------------------------------------------------------------------
def get_catalogo(filtro=None, apenas_ativos=True, db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()

    query = """
    SELECT 
        m.id,
        m.codigo_catmat,
        m.nome_basico,
        m.nome_modificador,
        m.descricao,
        m.categoria,
        m.unidade_base,
        m.embalagem_compra,
        m.fator_conversao,
        m.estoque_inicial,
        m.estoque_minimo,
        m.local_ambiente,
        m.local_estrutura,
        m.local_posicao,
        m.validade_pao_dias,
        m.nf_origem,
        m.ativo,
        m.motivo_ajuste,
        COALESCE((SELECT SUM(quantidade_base) FROM tb_entradas WHERE material_id = m.id), 0) AS total_entradas,
        COALESCE((SELECT SUM(quantidade_base) FROM tb_saidas WHERE material_id = m.id), 0) AS total_saidas,
        COALESCE((SELECT COUNT(*) FROM tb_emprestimos_ferramentas WHERE material_id = m.id AND status = 'EM USO'), 0) AS em_emprestimo,
        COALESCE((SELECT COUNT(*) FROM tb_fracionados_abertos WHERE material_id = m.id AND status != 'ESGOTADO'), 0) AS fracionados_ativos
    FROM tb_materiais m
    WHERE 1=1
    """
    params = []
    if apenas_ativos:
        query += " AND m.ativo = 1"

    if filtro:
        query += " AND (m.descricao LIKE ? OR m.id LIKE ? OR m.codigo_catmat LIKE ? OR m.categoria LIKE ? OR m.local_ambiente LIKE ? OR m.local_estrutura LIKE ?)"
        termo = f"%{filtro}%"
        params.extend([termo, termo, termo, termo, termo, termo])

    query += " ORDER BY m.descricao ASC"
    cur.execute(query, params)
    rows = cur.fetchall()

    resultado = []
    for r in rows:
        saldo = (r['estoque_inicial'] or 0) + (r['total_entradas'] or 0) - (r['total_saidas'] or 0)
        estoque_min = r['estoque_minimo'] or 2
        st = "BAIXO" if saldo <= estoque_min else "REGULAR"

        # Monta endereço WMS 3D amigável
        end_3d = f"{r['local_ambiente']} > {r['local_estrutura']} > {r['local_posicao']}"

        resultado.append({
            "id": r['id'],
            "codigo_catmat": r['codigo_catmat'] or '-',
            "nome_basico": r['nome_basico'],
            "nome_modificador": r['nome_modificador'],
            "descricao": r['descricao'],
            "categoria": r['categoria'],
            "unidade_base": r['unidade_base'],
            "unidade": r['unidade_base'],
            "embalagem_compra": r['embalagem_compra'],
            "fator_conversao": r['fator_conversao'],
            "estoque_inicial": r['estoque_inicial'],
            "total_entradas": r['total_entradas'],
            "total_saidas": r['total_saidas'],
            "em_emprestimo": r['em_emprestimo'],
            "fracionados_ativos": r['fracionados_ativos'],
            "saldo": round(saldo, 2),
            "estoque_minimo": estoque_min,
            "status_estoque": st,
            "local_ambiente": r['local_ambiente'],
            "local_estrutura": r['local_estrutura'],
            "local_posicao": r['local_posicao'],
            "endereco_3d": end_3d,
            "localizacao": end_3d,
            "validade_pao_dias": r['validade_pao_dias'],
            "nf_origem": r['nf_origem'] or '-',
            "ativo": r['ativo'],
            "motivo_ajuste": r['motivo_ajuste'] or ''
        })

    conn.close()
    return resultado

def obter_material(id_mat, db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM tb_materiais WHERE id = ?", (id_mat,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["endereco_3d"] = f"{d['local_ambiente']} > {d['local_estrutura']} > {d['local_posicao']}"
    return d

def criar_material(dados, db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM tb_materiais")
    prox_num = cur.fetchone()[0] + 1
    novo_id = f"01{prox_num:04d}" # Padrão SKU Numérico de 6 dígitos

    nome_b = dados.get('nome_basico', '').strip().upper()
    nome_m = dados.get('nome_modificador', '').strip().upper()
    desc = dados.get('descricao', '').strip().upper()
    if not desc:
        desc = f"{nome_b} {nome_m}".strip()

    cur.execute("""
    INSERT INTO tb_materiais (
        id, codigo_catmat, nome_basico, nome_modificador, descricao, categoria,
        unidade_base, embalagem_compra, fator_conversao, estoque_inicial, estoque_minimo,
        local_ambiente, local_estrutura, local_posicao, validade_pao_dias, nf_origem, motivo_ajuste, ativo
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
    """, (
        novo_id,
        dados.get('codigo_catmat', '').strip(),
        nome_b or desc,
        nome_m,
        desc,
        dados.get('categoria', 'CONSUMO').strip().upper(),
        dados.get('unidade_base', 'UN').strip().upper(),
        dados.get('embalagem_compra', 'UN').strip().upper(),
        float(dados.get('fator_conversao', 1.0) or 1.0),
        float(dados.get('estoque_inicial', 0) or 0),
        float(dados.get('estoque_minimo', 2) or 2),
        dados.get('local_ambiente', 'ALMOXARIFADO CENTRAL').strip().upper(),
        dados.get('local_estrutura', 'ESTANTE 01').strip().upper(),
        dados.get('local_posicao', 'PRATELEIRA 01').strip().upper(),
        int(dados.get('validade_pao_dias', 0) or 0),
        dados.get('nf_origem', '').strip().upper(),
        dados.get('motivo_ajuste', 'Cadastro inicial padronizado')
    ))

    conn.commit()
    conn.close()
    return novo_id

def editar_material(id_mat, dados, db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()

    nome_b = dados.get('nome_basico', '').strip().upper()
    nome_m = dados.get('nome_modificador', '').strip().upper()
    desc = dados.get('descricao', '').strip().upper()
    if not desc:
        desc = f"{nome_b} {nome_m}".strip()

    cur.execute("""
    UPDATE tb_materiais
    SET codigo_catmat = ?, nome_basico = ?, nome_modificador = ?, descricao = ?,
        categoria = ?, unidade_base = ?, embalagem_compra = ?, fator_conversao = ?,
        estoque_inicial = ?, estoque_minimo = ?, local_ambiente = ?, local_estrutura = ?,
        local_posicao = ?, validade_pao_dias = ?, nf_origem = ?, motivo_ajuste = ?
    WHERE id = ?
    """, (
        dados.get('codigo_catmat', '').strip(),
        nome_b or desc,
        nome_m,
        desc,
        dados.get('categoria', 'CONSUMO').strip().upper(),
        dados.get('unidade_base', 'UN').strip().upper(),
        dados.get('embalagem_compra', 'UN').strip().upper(),
        float(dados.get('fator_conversao', 1.0) or 1.0),
        float(dados.get('estoque_inicial', 0) or 0),
        float(dados.get('estoque_minimo', 2) or 2),
        dados.get('local_ambiente', 'ALMOXARIFADO CENTRAL').strip().upper(),
        dados.get('local_estrutura', 'ESTANTE 01').strip().upper(),
        dados.get('local_posicao', 'PRATELEIRA 01').strip().upper(),
        int(dados.get('validade_pao_dias', 0) or 0),
        dados.get('nf_origem', '').strip().upper(),
        dados.get('motivo_ajuste', 'Edição cadastral e normalização'),
        id_mat
    ))

    conn.commit()
    conn.close()
    return True

def excluir_material(id_mat, db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM tb_entradas WHERE material_id = ?", (id_mat,))
    tem_entradas = cur.fetchone()[0] > 0
    cur.execute("SELECT COUNT(*) FROM tb_saidas WHERE material_id = ?", (id_mat,))
    tem_saidas = cur.fetchone()[0] > 0

    if tem_entradas or tem_saidas:
        cur.execute("UPDATE tb_materiais SET ativo = 0 WHERE id = ?", (id_mat,))
        acao = "INATIVADO"
    else:
        cur.execute("DELETE FROM tb_materiais WHERE id = ?", (id_mat,))
        acao = "EXCLUIDO"

    conn.commit()
    conn.close()
    return acao

# ---------------------------------------------------------------------------
# ETAPA 1: ENTRADAS COM CONVERSÃO AUTOMÁTICA
# ---------------------------------------------------------------------------
def registrar_entrada(dados, db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()

    mat_id = dados['material_id']
    cur.execute("SELECT unidade_base, embalagem_compra, fator_conversao FROM tb_materiais WHERE id = ?", (mat_id,))
    mat = cur.fetchone()
    if not mat:
        conn.close()
        raise ValueError("Material não encontrado!")

    fator = float(mat['fator_conversao'] or 1.0)
    qtd_compra = float(dados['quantidade'])

    # Se a entrada foi declarada na embalagem comercial ou na base
    em_embalagem = dados.get('em_embalagem', True)
    if em_embalagem:
        qtd_base = qtd_compra * fator
        unid_compra = mat['embalagem_compra']
    else:
        qtd_base = qtd_compra
        unid_compra = mat['unidade_base']

    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    data_nf = dados.get('data') or datetime.now().strftime("%d/%m/%Y")
    v_unit = float(dados.get('valor_unit', 0) or 0)
    v_total = float(dados.get('valor_total') or (qtd_compra * v_unit))

    cur.execute("""
    INSERT INTO tb_entradas (
        data_hora, nf, fornecedor, material_id, quantidade_compra, unidade_compra,
        fator_conversao, quantidade_base, valor_unit, valor_total, projeto, responsavel, observacao
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data_nf, dados.get('nf', 'S/N'), dados.get('fornecedor', 'DIVERSOS').strip().upper(),
        mat_id, qtd_compra, unid_compra, fator, qtd_base, v_unit, v_total,
        dados.get('projeto', 'MANUTENÇÃO PREDIAL / POLO GERAL').strip().upper(),
        dados.get('responsavel', 'ALMOXARIFADO CENTRAL').strip().upper(),
        dados.get('observacao', '')
    ))

    conn.commit()
    conn.close()
    return {"qtd_base_creditada": qtd_base, "unidade_base": mat['unidade_base']}

def get_historico_entradas(limite=50, db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
    SELECT e.id, e.data_hora, e.nf, e.fornecedor, m.descricao AS material_nome,
           e.quantidade_compra, e.unidade_compra, e.quantidade_base, m.unidade_base,
           e.valor_unit, e.valor_total, e.projeto
    FROM tb_entradas e
    JOIN tb_materiais m ON e.material_id = m.id
    ORDER BY e.id DESC
    LIMIT ?
    """, (limite,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ---------------------------------------------------------------------------
# ETAPA 2: SAÍDAS, FRACIONADOS E EMPRÉSTIMOS DE FERRAMENTAS
# ---------------------------------------------------------------------------
def registrar_saida_consumo(dados, db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()

    ano = datetime.now().year
    cur.execute("SELECT COUNT(*) FROM tb_saidas")
    total = cur.fetchone()[0] + 1
    id_saida = f"SAI-{ano}-{total:04d}"
    num_recibo = f"REC-{ano}/{total:04d}"
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    cur.execute("""
    SELECT descricao, categoria, unidade_base, embalagem_compra, fator_conversao,
           validade_pao_dias, local_ambiente, local_estrutura, local_posicao
    FROM tb_materiais WHERE id = ?
    """, (dados['material_id'],))
    mat = cur.fetchone()
    if not mat:
        conn.close()
        raise ValueError("Material não encontrado!")

    qtd_base = float(dados['quantidade'])

    # Verifica se deve abrir nova lata/embalagem com controle PAO
    fracionado_id = None
    if mat['validade_pao_dias'] and mat['validade_pao_dias'] > 0 and dados.get('abrir_nova_lata'):
        cur.execute("SELECT COUNT(*) FROM tb_fracionados_abertos")
        tot_frac = cur.fetchone()[0] + 1
        fracionado_id = f"FRAC-{ano}-{tot_frac:04d}"
        venc_pao = (datetime.now() + timedelta(days=mat['validade_pao_dias'])).strftime("%d/%m/%Y")

        saldo_lata = float(mat['fator_conversao'] or 1.0) - qtd_base
        if saldo_lata < 0: saldo_lata = 0

        cur.execute("""
        INSERT INTO tb_fracionados_abertos (id, material_id, data_abertura, validade_pao_dias, data_vencimento_pao, nivel_atual, saldo_remanescente, aberto_por, status)
        VALUES (?, ?, ?, ?, ?, '75%', ?, ?, 'EM_USO')
        """, (
            fracionado_id, dados['material_id'], agora, mat['validade_pao_dias'], venc_pao,
            saldo_lata, dados['solicitante']
        ))

    cur.execute("""
    INSERT INTO tb_saidas (
        id, data_hora, material_id, descricao, quantidade_base, unidade_base,
        solicitante, siape, projeto, ambiente, finalidade, tipo_saida, fracionado_id, comprovante_num
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'CONSUMO', ?, ?)
    """, (
        id_saida, agora, dados['material_id'], mat['descricao'],
        qtd_base, mat['unidade_base'], dados['solicitante'],
        dados.get('siape', ''), dados['projeto'], dados['ambiente'],
        dados.get('finalidade', 'Uso operacional'), fracionado_id, num_recibo
    ))

    conn.commit()
    conn.close()

    return {
        "id_saida": id_saida,
        "num_recibo": num_recibo,
        "data_hora": agora,
        "material_id": dados['material_id'],
        "descricao": mat['descricao'],
        "unidade": mat['unidade_base'],
        "categoria": mat['categoria'],
        "quantidade": qtd_base,
        "solicitante": dados['solicitante'],
        "siape": dados.get('siape', ''),
        "projeto": dados['projeto'],
        "ambiente": dados['ambiente'],
        "finalidade": dados.get('finalidade', 'Uso operacional'),
        "fracionado_id": fracionado_id
    }

def registrar_retorno_sobra(dados, db_path=DB_PATH):
    """Registra o retorno ao estoque de uma sobra de lata ou cabo."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    mat_id = dados['material_id']
    cur.execute("SELECT descricao, unidade_base, fator_conversao FROM tb_materiais WHERE id = ?", (mat_id,))
    mat = cur.fetchone()
    if not mat:
        conn.close()
        raise ValueError("Material não encontrado!")

    # Se informou em fração (ex: 3/4, 1/2, 1/4)
    fracao = dados.get('fracao') # 0.75, 0.50, 0.25
    fator = float(mat['fator_conversao'] or 1.0)
    if fracao:
        qtd_retorno = float(fracao) * fator
        nivel_txt = f"{int(float(fracao)*100)}%"
    else:
        qtd_retorno = float(dados['quantidade'])
        nivel_txt = "FRAÇÃO"

    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Atualiza a tabela de fracionados abertos se houver
    frac_id = dados.get('fracionado_id')
    if frac_id:
        cur.execute("""
        UPDATE tb_fracionados_abertos 
        SET nivel_atual = ?, saldo_remanescente = ?, status = 'NO_ALMOXARIFADO'
        WHERE id = ?
        """, (nivel_txt, qtd_retorno, frac_id))

    # Dá uma entrada de retorno para recompor o saldo
    cur.execute("""
    INSERT INTO tb_entradas (
        data_hora, nf, fornecedor, material_id, quantidade_compra, unidade_compra,
        fator_conversao, quantidade_base, valor_unit, valor_total, projeto, responsavel, observacao
    ) VALUES (?, 'RETORNO-SOBRA', ?, ?, 1, 'FRAÇÃO', 1, ?, 0, 0, ?, 'ALMOXARIFADO CENTRAL', ?)
    """, (
        agora, f"DEVOLUÇÃO: {dados['solicitante']}", mat_id, qtd_retorno,
        dados.get('projeto', 'POLO GERAL'), f"Retorno de sobra ({nivel_txt}) de {dados['solicitante']}"
    ))

    conn.commit()
    conn.close()
    return {"sucesso": True, "qtd_retornada": qtd_retorno, "unidade": mat['unidade_base']}

def get_fracionados_abertos(db_path=DB_PATH):
    """Lista latas e fracionados atualmente abertos no almoxarifado."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
    SELECT f.id, f.material_id, m.descricao, m.codigo_catmat, m.embalagem_compra,
           m.unidade_base, f.data_abertura, f.validade_pao_dias, f.data_vencimento_pao,
           f.nivel_atual, f.saldo_remanescente, f.aberto_por, f.status
    FROM tb_fracionados_abertos f
    JOIN tb_materiais m ON f.material_id = m.id
    WHERE f.status != 'ESGOTADO'
    ORDER BY f.id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def obter_fracionado(id_frac, db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
    SELECT f.id, f.material_id, m.descricao, m.codigo_catmat, m.embalagem_compra AS volume_nominal,
           m.unidade_base, f.data_abertura, f.validade_pao_dias, f.data_vencimento_pao,
           f.nivel_atual, f.saldo_remanescente, f.aberto_por, f.status
    FROM tb_fracionados_abertos f
    JOIN tb_materiais m ON f.material_id = m.id
    WHERE f.id = ?
    """, (id_frac,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def registrar_emprestimo_ferramenta(dados, db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()

    ano = datetime.now().year
    cur.execute("SELECT COUNT(*) FROM tb_emprestimos_ferramentas")
    total = cur.fetchone()[0] + 1
    id_emp = f"EMP-{ano}/{total:04d}"
    num_recibo = f"TERMO-{ano}/{total:04d}"
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    data_saida = datetime.now().strftime("%d/%m/%Y")

    cur.execute("SELECT descricao FROM tb_materiais WHERE id = ?", (dados['material_id'],))
    mat = cur.fetchone()
    nome_ferramenta = mat['descricao'] if mat else dados.get('ferramenta_nome', 'FERRAMENTA')

    cur.execute("""
    INSERT INTO tb_emprestimos_ferramentas (id, material_id, ferramenta_nome, solicitante, siape, projeto, data_saida, data_prevista, status, comprovante_num)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'EM USO', ?)
    """, (
        id_emp, dados['material_id'], nome_ferramenta, dados['solicitante'],
        dados.get('siape', ''), dados['projeto'], data_saida, dados.get('data_prevista', ''), num_recibo
    ))

    id_saida = f"SAI-EMP-{ano}-{total:04d}"
    cur.execute("""
    INSERT INTO tb_saidas (id, data_hora, material_id, descricao, quantidade_base, unidade_base, solicitante, siape, projeto, ambiente, finalidade, tipo_saida, comprovante_num)
    VALUES (?, ?, ?, ?, 1, 'UN', ?, ?, ?, 'EMPRÉSTIMO DE FERRAMENTA', ?, 'EMPRESTIMO_FERRAMENTA', ?)
    """, (
        id_saida, agora, dados['material_id'], nome_ferramenta, dados['solicitante'],
        dados.get('siape', ''), dados['projeto'], f"Empréstimo ({id_emp})", num_recibo
    ))

    conn.commit()
    conn.close()

    return {
        "id_cautela": id_emp,
        "num_recibo": num_recibo,
        "data_hora": agora,
        "equipamento": nome_ferramenta,
        "serie": "FERRAMENTA OFICINA",
        "solicitante": dados['solicitante'],
        "siape": dados.get('siape', ''),
        "projeto": dados['projeto'],
        "data_prevista": dados.get('data_prevista', '')
    }

def get_ferramentas_em_uso(db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
    SELECT id, material_id, ferramenta_nome, solicitante, siape, projeto, data_saida, data_prevista
    FROM tb_emprestimos_ferramentas
    WHERE status = 'EM USO'
    ORDER BY id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def devolver_ferramenta(id_emprestimo, sem_avarias=True, obs="", db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("SELECT material_id, ferramenta_nome, solicitante FROM tb_emprestimos_ferramentas WHERE id = ?", (id_emprestimo,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False

    mat_id = row['material_id']
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    novo_st = "DEVOLVIDO" if sem_avarias else "AVARIADO"
    avaria_txt = "Devolvido em perfeito estado" if sem_avarias else f"Avaria: {obs}"

    cur.execute("""
    UPDATE tb_emprestimos_ferramentas
    SET status = ?, data_retorno = ?, avarias = ?
    WHERE id = ?
    """, (novo_st, agora, avaria_txt, id_emprestimo))

    cur.execute("""
    INSERT INTO tb_entradas (
        data_hora, nf, fornecedor, material_id, quantidade_compra, unidade_compra,
        fator_conversao, quantidade_base, valor_unit, valor_total, projeto, responsavel, observacao
    ) VALUES (?, 'RETORNO', ?, ?, 1, 'UN', 1, 1, 0, 0, 'POLO GERAL', 'ALMOXARIFADO CENTRAL', ?)
    """, (
        agora, f"DEVOLUÇÃO: {row['solicitante']}", mat_id, f"Retorno de ferramenta {id_emprestimo}. {avaria_txt}"
    ))

    conn.commit()
    conn.close()
    return True

# ---------------------------------------------------------------------------
# ETAPA 3: EXTRATO CRONOLÓGICO
# ---------------------------------------------------------------------------
def get_extrato(material_id=None, limite=50, db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()

    query = """
    SELECT 'ENTRADA' as tipo, e.data_hora as data, m.descricao as material, e.quantidade_base as quantidade, m.unidade_base as unidade, e.fornecedor as agente, e.nf as ref_doc, e.projeto
    FROM tb_entradas e
    JOIN tb_materiais m ON e.material_id = m.id
    """
    params = []
    if material_id:
        query += " WHERE e.material_id = ?"
        params.append(material_id)

    query += """
    UNION ALL
    SELECT 'SAÍDA' as tipo, s.data_hora as data, s.descricao as material, s.quantidade_base as quantidade, s.unidade_base as unidade, s.solicitante as agente, s.comprovante_num as ref_doc, s.projeto
    FROM tb_saidas s
    JOIN tb_materiais m ON s.material_id = m.id
    """
    if material_id:
        query += " WHERE s.material_id = ?"
        params.append(material_id)

    query += " ORDER BY data DESC LIMIT ?"
    params.append(limite)

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ---------------------------------------------------------------------------
# PARÂMETROS
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# GESTÃO DE SOLICITANTES (CANÔNICO PESSOAFISICA: NOME + CPF)
# ---------------------------------------------------------------------------
def formatar_cpf(cpf):
    if not cpf:
        return ""
    c = "".join(ch for ch in str(cpf) if ch.isdigit())
    if len(c) == 11:
        return f"{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}"
    return cpf

def migrar_solicitantes_legados(db_path=DB_PATH):
    """
    Varre os solicitantes legados em tb_parametros, extrai o CPF e Nome civil limpo,
    e popula a tabela tb_solicitantes sem perda de dados históricos.
    """
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM tb_solicitantes")
    qtd = cur.fetchone()[0]
    if qtd > 0:
        conn.close()
        return

    cur.execute("SELECT id, valor FROM tb_parametros WHERE tipo = 'SOLICITANTE'")
    rows = cur.fetchall()
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    for r in rows:
        texto = r['valor'].strip()
        # Procura CPF na string
        m_cpf = re.search(r'CPF[:/\s\-]*([\d\.\-\s]{11,18})', texto, re.IGNORECASE)
        cpf = None
        if m_cpf:
            raw_cpf = m_cpf.group(1)
            digitos = ''.join(c for c in raw_cpf if c.isdigit())
            if len(digitos) == 11:
                cpf = digitos
            nome = texto[:m_cpf.start()].strip(' ,-.:')
        else:
            m_siape = re.search(r'SIAPE[:\sNº]*(\d+)', texto, re.IGNORECASE)
            if m_siape:
                nome = texto[:m_siape.start()].strip(' ,-.:')
            else:
                nome = texto
        nome = nome.strip().upper()
        if not nome:
            continue

        try:
            cur.execute("""
            INSERT OR IGNORE INTO tb_solicitantes (cpf, nome_completo, ativo, data_cadastro)
            VALUES (?, ?, 1, ?)
            """, (cpf, nome, agora))
        except Exception:
            pass

    conn.commit()
    conn.close()

def get_solicitantes(apenas_ativos=True, db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()
    query = "SELECT id, cpf, nome_completo, ativo, data_cadastro FROM tb_solicitantes"
    if apenas_ativos:
        query += " WHERE ativo = 1"
    query += " ORDER BY nome_completo ASC"
    cur.execute(query)
    rows = cur.fetchall()
    conn.close()

    contagem_nomes = Counter(r['nome_completo'].strip().upper() for r in rows)

    resultado = []
    for r in rows:
        nome = r['nome_completo'].strip().upper()
        cpf = r['cpf'] or ""
        cpf_fmt = formatar_cpf(cpf)

        # Se for homônimo exato com CPF presente, desempata mostrando o final do CPF
        if contagem_nomes[nome] > 1 and cpf:
            rotulo = f"{nome} (final CPF: ***.{cpf[-4:]})"
        else:
            rotulo = nome

        resultado.append({
            "id": r['id'],
            "cpf": cpf,
            "cpf_formatado": cpf_fmt,
            "nome_completo": nome,
            "rotulo": rotulo,
            "ativo": r['ativo'],
            "data_cadastro": r['data_cadastro']
        })
    return resultado

def cadastrar_solicitante(nome, cpf, db_path=DB_PATH):
    nome_limpo = str(nome or "").strip().upper()
    if not nome_limpo:
        raise ValueError("O Nome Completo do Solicitante é obrigatório.")

    cpf_limpo = "".join(c for c in str(cpf or "") if c.isdigit())
    if len(cpf_limpo) != 11:
        raise ValueError("O CPF deve conter exatamente 11 dígitos numéricos.")

    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("SELECT id, nome_completo FROM tb_solicitantes WHERE cpf = ?", (cpf_limpo,))
    existe = cur.fetchone()
    if existe:
        conn.close()
        raise ValueError(f"Este CPF já pertence ao solicitante cadastrado: {existe['nome_completo']}.")

    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    cur.execute("""
    INSERT INTO tb_solicitantes (cpf, nome_completo, ativo, data_cadastro)
    VALUES (?, ?, 1, ?)
    """, (cpf_limpo, nome_limpo, agora))
    novo_id = cur.lastrowid

    # Sincroniza em tb_parametros para compatibilidade plena
    cur.execute("INSERT OR IGNORE INTO tb_parametros (tipo, valor) VALUES ('SOLICITANTE', ?)", (nome_limpo,))

    conn.commit()
    conn.close()
    return novo_id

def editar_solicitante(id_solic, nome, cpf, db_path=DB_PATH):
    nome_limpo = str(nome or "").strip().upper()
    if not nome_limpo:
        raise ValueError("O Nome Completo é obrigatório.")

    cpf_limpo = "".join(c for c in str(cpf or "") if c.isdigit())
    if len(cpf_limpo) != 11:
        raise ValueError("O CPF deve conter 11 dígitos numéricos.")

    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("SELECT id FROM tb_solicitantes WHERE cpf = ? AND id != ?", (cpf_limpo, id_solic))
    if cur.fetchone():
        conn.close()
        raise ValueError("Já existe outro solicitante com este mesmo CPF.")

    cur.execute("""
    UPDATE tb_solicitantes
    SET nome_completo = ?, cpf = ?
    WHERE id = ?
    """, (nome_limpo, cpf_limpo, id_solic))

    conn.commit()
    conn.close()
    return True

def excluir_solicitante(id_solic, db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("UPDATE tb_solicitantes SET ativo = 0 WHERE id = ?", (id_solic,))
    conn.commit()
    conn.close()
    return True

# ---------------------------------------------------------------------------
# PARÂMETROS GERAIS (PROJETO, AMBIENTE, ESTRUTURA)
# ---------------------------------------------------------------------------
def get_parametros(db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()

    # Solicitantes vindos da entidade estruturada tb_solicitantes
    solicitantes_db = get_solicitantes(apenas_ativos=True, db_path=db_path)
    solicitantes = [
        {
            "id": s["id"],
            "valor": s["rotulo"],
            "nome_completo": s["nome_completo"],
            "cpf": s["cpf"],
            "cpf_formatado": s["cpf_formatado"]
        }
        for s in solicitantes_db
    ]

    cur.execute("SELECT id, valor FROM tb_parametros WHERE tipo = 'PROJETO' ORDER BY valor ASC")
    projetos = [{"id": r[0], "valor": r[1]} for r in cur.fetchall()]

    cur.execute("SELECT id, valor FROM tb_parametros WHERE tipo = 'AMBIENTE' ORDER BY valor ASC")
    ambientes = [{"id": r[0], "valor": r[1]} for r in cur.fetchall()]

    cur.execute("SELECT id, valor FROM tb_parametros WHERE tipo = 'ESTRUTURA' ORDER BY valor ASC")
    estruturas = [{"id": r[0], "valor": r[1]} for r in cur.fetchall()]

    cur.execute("SELECT id, descricao, unidade_base, categoria, fator_conversao, embalagem_compra FROM tb_materiais WHERE ativo = 1 ORDER BY descricao ASC")
    materiais = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT id, descricao FROM tb_materiais WHERE categoria = 'FERRAMENTA' AND ativo = 1 ORDER BY descricao ASC")
    ferramentas = [{"id": r[0], "descricao": r[1]} for r in cur.fetchall()]

    conn.close()
    return {
        "solicitantes": solicitantes,
        "projetos": projetos,
        "ambientes": ambientes,
        "estruturas": estruturas,
        "materiais": materiais,
        "ferramentas": ferramentas
    }

def adicionar_parametro(tipo, valor, db_path=DB_PATH):
    tipo_norm = tipo.strip().upper()
    valor_norm = valor.strip().upper()
    if tipo_norm == "SOLICITANTE":
        # Se vier sem CPF pelo endpoint genérico
        return cadastrar_solicitante(valor_norm, "", db_path=db_path)

    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("INSERT INTO tb_parametros (tipo, valor) VALUES (?, ?)", (tipo_norm, valor_norm))
    novo_id = cur.lastrowid
    conn.commit()
    conn.close()
    return novo_id

def editar_parametro(id_param, novo_valor, db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("UPDATE tb_parametros SET valor = ? WHERE id = ?", (novo_valor.strip().upper(), id_param))
    conn.commit()
    conn.close()
    return True

def excluir_parametro(id_param, db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("DELETE FROM tb_parametros WHERE id = ?", (id_param,))
    conn.commit()
    conn.close()
    return True

# ---------------------------------------------------------------------------
# GESTÃO DE OPERADORES & AUTENTICAÇÃO (CANÔNICO PESSOAFISICA DO ARGUS)
# ---------------------------------------------------------------------------
def gerar_hash_senha(senha, salt=None):
    if not salt:
        salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac('sha256', str(senha).encode('utf-8'), salt.encode('utf-8'), 100000)
    return h.hex(), salt

def verificar_senha(senha, senha_hash, salt):
    h, _ = gerar_hash_senha(senha, salt)
    return secrets.compare_digest(h, senha_hash)

def ha_operadores(db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM tb_operadores WHERE ativo = 1")
    count = cur.fetchone()[0]
    conn.close()
    return count > 0

def cadastrar_operador(dados, db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()

    cpf_limpo = "".join([c for c in str(dados.get('cpf', '')) if c.isdigit()])
    if len(cpf_limpo) != 11:
        conn.close()
        raise ValueError("O CPF deve conter exatamente 11 dígitos numéricos.")

    nome = dados.get('nome_completo', '').strip()
    if not nome:
        conn.close()
        raise ValueError("O Nome Completo é obrigatório.")

    login = dados.get('login', '').strip() or cpf_limpo
    senha = str(dados.get('senha', '')).strip()
    if len(senha) < 4:
        conn.close()
        raise ValueError("A senha deve possuir no mínimo 4 caracteres.")

    # Verificar se CPF ou Login já existem
    cur.execute("SELECT id FROM tb_operadores WHERE cpf = ?", (cpf_limpo,))
    if cur.fetchone():
        conn.close()
        raise ValueError("Já existe um operador cadastrado com este CPF.")

    cur.execute("SELECT id FROM tb_operadores WHERE login = ?", (login,))
    if cur.fetchone():
        conn.close()
        raise ValueError(f"O login '{login}' já está em uso por outro operador.")

    senha_hash, salt = gerar_hash_senha(senha)
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    cur.execute("""
    INSERT INTO tb_operadores (
        cpf, nome_completo, email, telefone, tipo_vinculo, cargo_funcao,
        siape, empresa_contratada, login, senha_hash, salt, ativo, data_cadastro
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
    """, (
        cpf_limpo,
        nome.upper(),
        dados.get('email', '').strip().lower(),
        dados.get('telefone', '').strip(),
        dados.get('tipo_vinculo', 'TERCEIRIZADO').strip().upper(),
        dados.get('cargo_funcao', 'Almoxarife').strip().upper(),
        dados.get('siape', '').strip(),
        dados.get('empresa_contratada', '').strip().upper(),
        login,
        senha_hash,
        salt,
        agora
    ))

    novo_id = cur.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": novo_id,
        "cpf": cpf_limpo,
        "nome_completo": nome.upper(),
        "login": login,
        "tipo_vinculo": dados.get('tipo_vinculo', 'TERCEIRIZADO').strip().upper(),
        "cargo_funcao": dados.get('cargo_funcao', 'Almoxarife').strip().upper(),
        "email": dados.get('email', '').strip().lower()
    }

def autenticar_operador(login_ou_cpf, senha, db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()

    termo = str(login_ou_cpf).strip()
    termo_limpo = "".join([c for c in termo if c.isdigit()])

    cur.execute("""
    SELECT id, cpf, nome_completo, email, telefone, tipo_vinculo, cargo_funcao,
           siape, empresa_contratada, login, senha_hash, salt, ativo
    FROM tb_operadores
    WHERE (login = ? OR cpf = ?) AND ativo = 1
    """, (termo, termo_limpo if len(termo_limpo) == 11 else termo))

    row = cur.fetchone()
    conn.close()

    if not row:
        raise ValueError("Operador não localizado ou inativo.")

    if not verificar_senha(senha, row['senha_hash'], row['salt']):
        raise ValueError("Senha incorreta.")

    return {
        "id": row['id'],
        "cpf": row['cpf'],
        "nome_completo": row['nome_completo'],
        "login": row['login'],
        "email": row['email'],
        "telefone": row['telefone'],
        "tipo_vinculo": row['tipo_vinculo'],
        "cargo_funcao": row['cargo_funcao']
    }

def listar_operadores(db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
    SELECT id, cpf, nome_completo, email, telefone, tipo_vinculo, cargo_funcao, login, data_cadastro
    FROM tb_operadores
    WHERE ativo = 1
    ORDER BY nome_completo ASC
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


import re

with open('banco.py', 'r', encoding='utf-8') as f:
    conteudo = f.read()

nova_tabela = '''    CREATE TABLE IF NOT EXISTS tb_diretores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cargo TEXT NOT NULL,
        nome TEXT NOT NULL,
        portaria TEXT NOT NULL,
        is_titular INTEGER DEFAULT 0
    );
    \"\"\"'''

conteudo = conteudo.replace('    \"\"\"', nova_tabela, 1)

migracoes = '''    migrar_schema_cautelas_e_solicitantes(db_path=db_path)
    migrar_solicitantes_legados(db_path=db_path)
    migrar_diretores_iniciais(db_path=db_path)'''

conteudo = conteudo.replace('''    migrar_schema_cautelas_e_solicitantes(db_path=db_path)
    migrar_solicitantes_legados(db_path=db_path)''', migracoes)

funcao_nova = '''
def migrar_diretores_iniciais(db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM tb_diretores WHERE is_titular = 1")
    count = cur.fetchone()[0]
    if count == 0:
        cur.executemany("""
            INSERT INTO tb_diretores (cargo, nome, portaria, is_titular) 
            VALUES (?, ?, ?, 1)
        """, [
            ('Diretor-Geral', 'Alyson de Jesus dos Santos', 'PORTARIA No 061/GR/IFAM, DE 09 DE JANEIRO DE 2026.'),
            ('Diretor Administrativo e Financeiro', 'Alexandre Lopes Martiniano', 'PORTARIA No 010/2026-INOVA/IFAM, DE 11 DE FEVEREIRO DE 2026.')
        ])
        conn.commit()
    conn.close()

# ---------------------------------------------------------------------------
'''

conteudo = conteudo.replace('# ---------------------------------------------------------------------------', funcao_nova, 1)

# Agora os métodos CRUD de diretores:
crud_diretores = '''
def get_diretores(db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM tb_diretores ORDER BY is_titular DESC, id ASC")
    res = [dict(r) for r in cur.fetchall()]
    conn.close()
    return res

def salvar_diretor(cargo, nome, portaria, db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("INSERT INTO tb_diretores (cargo, nome, portaria, is_titular) VALUES (?, ?, ?, 0)", (cargo, nome, portaria))
    conn.commit()
    conn.close()
    
def editar_diretor(id_dir, cargo, nome, portaria, db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("UPDATE tb_diretores SET cargo=?, nome=?, portaria=? WHERE id=? AND is_titular=0", (cargo, nome, portaria, id_dir))
    conn.commit()
    conn.close()

def excluir_diretor(id_dir, db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("DELETE FROM tb_diretores WHERE id = ? AND is_titular = 0", (id_dir,))
    conn.commit()
    conn.close()
'''

conteudo += crud_diretores

with open('banco.py', 'w', encoding='utf-8') as f:
    f.write(conteudo)

import sqlite3

def migrar_diretores(db_path='dados/almoxarifado.db'):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executescript('''
    CREATE TABLE IF NOT EXISTS tb_diretores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cargo TEXT NOT NULL,
        nome TEXT NOT NULL,
        portaria TEXT NOT NULL,
        is_titular INTEGER DEFAULT 0
    );
    ''')
    
    # Injetar os 2 titulares caso não existam
    cur.execute('SELECT COUNT(*) FROM tb_diretores WHERE is_titular = 1')
    count = cur.fetchone()[0]
    if count == 0:
        cur.executemany('''
            INSERT INTO tb_diretores (cargo, nome, portaria, is_titular) 
            VALUES (?, ?, ?, 1)
        ''', [
            ('Diretor-Geral', 'Alyson de Jesus dos Santos', 'PORTARIA No 061/GR/IFAM, DE 09 DE JANEIRO DE 2026.'),
            ('Diretor Administrativo e Financeiro', 'Alexandre Lopes Martiniano', 'PORTARIA No 010/2026-INOVA/IFAM, DE 11 DE FEVEREIRO DE 2026.')
        ])
    
    conn.commit()
    conn.close()

migrar_diretores()
print('Migração de diretores executada!')
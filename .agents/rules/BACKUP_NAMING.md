# Regra de Nomenclatura de Backups

Sempre que você criar um backup de banco de dados (como arquivos .sql, .sqlite3) ou de qualquer arquivo importante do projeto, utilize **OBRIGATORIAMENTE** o seguinte padrão:

1. **ID Numérico Sequencial (3 dígitos):** Adicione no início do nome do arquivo (ex: `001_`, `002_`).
2. **Formato Padrão:** `NNN_db_backup_YYYY-MM-DD_HH-MM.extensao` (ex: `001_db_backup_2026-08-10_23-35.sql`).
3. **Determinação do ID (NNN):** Verifique os arquivos existentes na pasta de backups (ex: `backups/`), encontre o maior número `NNN` já existente e incremente para o próximo.
4. **Data e Hora:** Utilize sempre hifens (YYYY-MM-DD_HH-MM). Se não souber a hora exata, use `00-00`. NUNCA utilize a versão sem o prefixo numérico.
5. **Restauração e Manipulação:** Entenda que o usuário poderá solicitar a manipulação ou restauração de backups usando apenas o ID (ex: "restaure o backup 3", significando o arquivo que começa com `003_`).

---
name: github-bom-dia
description: "Rotina completa de início do dia (Chegada). Sincroniza o código, instala bibliotecas, roda migrações e restaura backups do banco."
---

# Instruções de Execução

Oriente o usuário a executar `.\scripts\bom_dia.ps1` no terminal. A IA não
deve executar a rotina diretamente. Antes de qualquer restauração, exija
confirmação explícita e informe que os dados locais serão substituídos.

Sempre que o usuário enviar o comando "bom dia" (ex: "bom dia", "pode começar"), você deverá preparar o ambiente local com base nas últimas atualizações do GitHub.

Siga os passos rigorosamente nesta ordem:

1. **Ler o Diário de Bordo:**
   - OBRIGATORIAMENTE leia o arquivo `.\diario_de_bordo.md` na raiz do projeto para se contextualizar sobre o status atual e as pendências.
2. **Sincronizar Código (Pull):**
   - Execute o comando para baixar as novidades da nuvem: `git pull --rebase`
3. **Sincronizar Pacotes (Requirements):**
   - Execute a instalação do que houver de novo no requirements: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`
4. **Sincronizar Estrutura do Banco (Migrações):**
   - Execute as migrações para que a estrutura acompanhe o código: `.\.venv\Scripts\python.exe manage.py migrate`
5. **Acionar Restauração de Dados (Restauração Opcional e Híbrida):**
   - Verifique as pastas `backups/sql/` e `backups/json/` para encontrar os arquivos do maior ID sequencial (NNN_).
   - Avise o usuário qual foi o ID do backup mais recente encontrado. Em seguida, **PERGUNTE** se ele deseja restaurar o banco e de qual forma: (A) Via JSON (Recomendado se houveram novas migrações vindas da nuvem) ou (B) Via SQL (Restauração bruta local).
   - **SE O USUÁRIO ESCOLHER JSON:**
     - Limpe o banco de forma segura: `.\.venv\Scripts\python.exe manage.py flush --no-input`
     - Restaure os dados: `.\.venv\Scripts\python.exe manage.py loaddata <CAMINHO_DO_JSON>`
   - **SE O USUÁRIO ESCOLHER SQL:**
     - Limpe o banco bruto: `$env:PGCLIENTENCODING='utf8'; $env:PGPASSWORD='argus'; & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d argus_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO postgres; GRANT ALL ON SCHEMA public TO public;"`
     - Restaure bruto: `$env:PGCLIENTENCODING='utf8'; $env:PGPASSWORD='argus'; & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d argus_db -f <CAMINHO_DO_SQL>`
6. **Reportar ao Usuário:**
   - Deseje um bom dia de trabalho, resuma brevemente o que você leu no diário de bordo e confirme que o ambiente está totalmente sincronizado!

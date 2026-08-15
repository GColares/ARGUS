---
name: github-bom-dia
description: "Rotina completa de início do dia (Chegada). Sincroniza o código, instala bibliotecas, roda migrações e restaura backups do banco."
---

# Instruções de Execução

Sempre que o usuário enviar o comando "bom dia" (ex: "bom dia", "pode começar"), você deverá preparar o ambiente local com base nas últimas atualizações do GitHub.

Siga os passos rigorosamente nesta ordem:

1. **Ler o Diário de Bordo:**
   - OBRIGATORIAMENTE leia o arquivo `diario_de_bordo.md` na raiz do projeto (`c:\ARGUS\diario_de_bordo.md`) para se contextualizar sobre o status atual do projeto e o que está pendente para o dia de hoje.
2. **Sincronizar Código (Pull):**
   - Execute o comando para baixar as novidades da nuvem: `git pull --rebase`
3. **Sincronizar Pacotes (Requirements):**
   - Execute a instalação do que houver de novo no requirements: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`
4. **Sincronizar Estrutura do Banco (Migrações):**
   - Execute as migrações para que a estrutura acompanhe o código: `.\.venv\Scripts\python.exe manage.py migrate`
5. **Acionar Restauração de Dados (Restauração Opcional):**
   - Verifique utilizando o PowerShell qual o backup `.sql` de maior ID (NNN_) na pasta `backups/`. Exemplo:
     `$latest = Get-ChildItem -Path "c:\Projetos\ARGUS\backups\*.sql" -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 1; if ($latest) { $latest.FullName } else { "NOT FOUND" }`
   - Se encontrar um backup, avise o usuário qual foi o backup mais recente que existe na pasta. Em seguida, **PERGUNTE** ao usuário se ele deseja injetar esse backup no banco atual dele.
   - **SE O USUÁRIO CONFIRMAR A INJEÇÃO (ex: "sim, pode injetar"):**
     - Limpe o banco: `$env:PGPASSWORD='argus'; & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d argus_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO postgres; GRANT ALL ON SCHEMA public TO public;"`
     - Restaure: `$env:PGPASSWORD='argus'; & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d argus_db -f <CAMINHO_ENCONTRADO>`
6. **Reportar ao Usuário:**
   - Deseje um bom dia de trabalho, resuma brevemente o que você leu no diário de bordo e confirme que o ambiente está totalmente sincronizado!

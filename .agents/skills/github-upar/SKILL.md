---
name: github-upar
description: "Restaura o banco de dados PostgreSQL local utilizando o arquivo de backup (.sql) mais recente disponível na pasta backups/ ou raiz."
---

# Instruções de Execução

Sempre que o usuário enviar o comando "upar" (ex: "upar", "pode upar", "upar banco", etc), você deverá assumir a rotina de injeção de dados no banco local. Siga os passos abaixo:

1. **Localizar o backup mais recente:**
   Use o PowerShell para encontrar o arquivo `.sql` mais recente (seja na raiz ou na pasta backups): 
   `$latest = Get-ChildItem -Path "c:\ARGUS\backups\*.sql", "c:\ARGUS\argus_backup.sql" | Sort-Object LastWriteTime -Descending | Select-Object -First 1; $latest.FullName`
2. **Limpar o Banco de Dados (Drop Schema):**
   Execute o seguinte comando para apagar e recriar o esquema público do PostgreSQL de forma segura, garantindo que não haverá conflito de dados duplicados:
   `$env:PGPASSWORD='argus'; & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d argus_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO postgres; GRANT ALL ON SCHEMA public TO public;"`
3. **Restaurar os Dados (Injeção):**
   Com base no caminho do arquivo retornado no Passo 1, execute a restauração completa via psql:
   `$env:PGPASSWORD='argus'; & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d argus_db -f <CAMINHO_DO_ARQUIVO_DO_PASSO_1>`
4. **Reportar ao Usuário:**
   Após finalizar a injeção dos dados, responda confirmando o sucesso da operação e informando exatamente qual foi o arquivo (nome e data) utilizado para "upar" a base.

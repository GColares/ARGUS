---
name: github-atualizar
description: "Executa a rotina completa de commit e push para o GitHub quando o usuário enviar o comando 'atualizar'."
---

# Instruções de Execução

Sempre que o usuário solicitar a ação "atualizar" (ex: "atualizar", "pode atualizar", etc), você deverá assumir a rotina de versionamento do projeto. Siga os passos abaixo utilizando as ferramentas do sistema:

1. **Atualizar Regras de Negócio:** Antes de iniciar o versionamento, reflita sobre o que foi desenvolvido na sessão atual. Se você identificar novas definições de negócio, novos fluxos ou módulos criados que agreguem conhecimento ao sistema, utilize suas ferramentas de edição de arquivo para atualizar o arquivo `.agents/rules/CONTEXTO_ARGUS.md` com esses novos aprendizados.
2. **Geração de Backup do Banco (PostgreSQL):**
   - Garanta que a pasta `backups/` existe na raiz do projeto (crie-a se necessário).
   - Execute o dump do banco PostgreSQL usando o executável `pg_dump.exe` passando a senha. Use o seguinte formato (ajuste o caminho do pg_dump se necessário, o padrão esperado é `C:\Program Files\PostgreSQL\18\bin\pg_dump.exe`):
     `$env:PGPASSWORD='argus'; & "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -U postgres -d argus_db -f backups/argus_backup_YYYYMMDD_HHMM.sql`
   - Em seguida, sobrescreva o arquivo da raiz executando o dump para `argus_backup.sql`. Este é o arquivo que será versionado.
3. **Verificar o Status:** Execute `git status` para analisar os arquivos modificados.
4. **Adicionar Modificações:** Execute `git add .` para colocar as modificações em stage.
5. **Gerar Commit:** Com base no contexto recente da conversa, formule uma mensagem curta e clara em português e execute `git commit -m "Sua mensagem aqui"`.
6. **Sincronizar Repositório (Pull):** Execute `git pull --rebase` para baixar as atualizações remotas mais recentes e aplicá-las ao seu histórico local.
7. **Aplicar Migrações (Sync de Banco):** Para garantir que as tabelas acompanhem o código baixado, ative o ambiente virtual e aplique as migrações locais executando: `.\.venv\Scripts\python.exe manage.py migrate`.
8. **Enviar para o GitHub (Push):** Execute `git push` para enviar o repositório sincronizado ao servidor.
9. **Reportar ao Usuário:** Após finalizar, responda confirmando que os arquivos (e os backups) foram enviados, baixados (se houver), e se as migrações rodaram com sucesso.

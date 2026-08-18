---
name: github-ate-amanha
description: "Rotina completa de encerramento do dia (Saída). Faz o backup do banco, salva as dependências e envia o código para a nuvem."
---

# Instruções de Execução

Sempre que o usuário enviar o comando "ate-amanha" (ex: "até amanhã", "ate amanha", "encerrar dia", "fechar a loja"), você deverá executar a rotina de empacotamento e envio do projeto para a nuvem.

Siga os passos rigorosamente nesta ordem:

1. **Atualizar Regras de Negócio e Diário:**
   - Antes de iniciar o versionamento, atualize o arquivo `.agents/rules/CONTEXTO_ARGUS.md` com novos aprendizados caso necessário.
   - Atualize OBRIGATORIAMENTE o arquivo `diario_de_bordo.md` na raiz do projeto. ATENÇÃO: NUNCA sobrescreva o arquivo apagando o histórico anterior. Você deve INSERIR a nova entrada (com a data atual, o que foi feito e o que está pendente) logo abaixo do título principal do arquivo, empurrando todo o texto e os dias anteriores para baixo, preservando todo o histórico intocado.
2. **Geração de Backups Híbridos de Segurança:**
   - Garanta que as pastas `backups/sql/` e `backups/json/` existem na raiz do projeto (crie se não existirem).
   - Determine o próximo ID sequencial de 3 dígitos (NNN) analisando as subpastas em `backups/`.
   - Gere PRIMEIRO o backup SQL (rápido para disaster recovery):
     `$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm" ; $env:PGPASSWORD='argus'; & "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -U postgres -d argus_db -f "backups/sql/NNN_db_backup_${timestamp}.sql"`
   - Gere EM SEGUIDA o backup JSON (seguro para mudanças de estrutura), forçando UTF-8:
     `$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm" ; .\.venv\Scripts\python.exe -X utf8 manage.py dumpdata -e contenttypes -e auth.Permission --indent 2 > "backups/json/NNN_db_backup_${timestamp}.json"`
3. **Salvar Pacotes (Requirements):**
   - Execute a exportação das dependências para garantir que qualquer pacote novo seja salvo:
     `.\.venv\Scripts\python.exe -m pip freeze > requirements.txt`
4. **Verificar o Status e Adicionar:**
   - Execute `git status` e depois `git add .` para colocar tudo em stage.
5. **Gerar Commit:**
   - Formule uma mensagem curta e clara em português e execute `git commit -m "Sua mensagem aqui"`.
6. **Sincronizar (Pull):**
   - Execute `git pull --rebase` para garantir que o seu envio não quebre nada.
7. **Enviar para o GitHub (Push):**
   - Execute `git push` para mandar os commits, o arquivo requirements e o backup gerado para o servidor.
8. **Reportar ao Usuário:**
   - Após finalizar, deseje um bom descanso e confirme que tudo foi salvo e enviado com sucesso.

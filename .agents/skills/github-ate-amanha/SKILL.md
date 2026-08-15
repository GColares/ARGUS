---
name: github-ate-amanha
description: "Rotina completa de encerramento do dia (Saída). Faz o backup do banco, salva as dependências e envia o código para a nuvem."
---

# Instruções de Execução

Sempre que o usuário enviar o comando "ate-amanha" (ex: "até amanhã", "ate amanha", "encerrar dia", "fechar a loja"), você deverá executar a rotina de empacotamento e envio do projeto para a nuvem.

Siga os passos rigorosamente nesta ordem:

1. **Atualizar Regras de Negócio:**
   - Antes de iniciar o versionamento, reflita sobre o que foi desenvolvido na sessão atual. Se você identificar novas definições de negócio, novos fluxos ou módulos criados que agreguem conhecimento ao sistema, atualize o arquivo `.agents/rules/CONTEXTO_ARGUS.md` com esses novos aprendizados.
2. **Geração de Backup de Segurança:**
   - Garanta que a pasta `backups/` existe na raiz do projeto (crie se não existir).
   - Determine o próximo ID sequencial de 3 dígitos (NNN) analisando a pasta `backups/` e crie o backup adotando a regra de nomenclatura NNN:
     `$env:PGPASSWORD='argus'; & "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -U postgres -d argus_db -f backups/NNN_db_backup_YYYY-MM-DD_HH-MM.sql`
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

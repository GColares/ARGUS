---
name: github-atualizar
description: "Executa a rotina completa de commit e push para o GitHub quando o usuário enviar o comando 'atualizar'."
---

# Instruções de Execução

Sempre que o usuário solicitar a ação "atualizar" (ex: "atualizar", "pode atualizar", etc), você deverá assumir a rotina de versionamento do projeto. Siga os passos abaixo utilizando as ferramentas do sistema:

1. **Atualizar Regras de Negócio:** Antes de iniciar o versionamento, reflita sobre o que foi desenvolvido na sessão atual. Se você identificar novas definições de negócio, novos fluxos ou módulos criados que agreguem conhecimento ao sistema, utilize suas ferramentas de edição de arquivo para atualizar o arquivo `.agents/rules/CONTEXTO_ARGUS.md` com esses novos aprendizados.
2. **Verificar o Status:** Execute `git status` para analisar os arquivos modificados.
3. **Adicionar Modificações:** Execute `git add .` para colocar as modificações em stage.
4. **Gerar Commit:** Com base no contexto recente da conversa, formule uma mensagem curta e clara em português e execute `git commit -m "Sua mensagem aqui"`.
5. **Sincronizar Repositório:** Execute `git pull --rebase` para baixar as atualizações remotas mais recentes e aplicá-las ao seu histórico local antes de enviar as suas. (Em caso de conflitos, resolva-os primeiro).
6. **Enviar para o GitHub:** Execute `git push` para enviar o repositório sincronizado ao servidor.
7. **Reportar ao Usuário:** Após finalizar, responda confirmando as atualizações das regras de negócio (se houveram) e resuma o que foi enviado e baixado via Git.

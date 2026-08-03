---
name: github-atualizar
description: "Executa a rotina completa de commit e push para o GitHub quando o usuário enviar o comando 'atualizar'."
---

# Instruções de Execução

Sempre que o usuário solicitar a ação "atualizar" (ex: "atualizar", "pode atualizar", etc), você deverá assumir a rotina de versionamento do projeto. Siga os passos abaixo utilizando as ferramentas do sistema:

1. **Verificar o Status:** Execute `git status` para analisar os arquivos modificados.
2. **Adicionar Modificações:** Execute `git add .` para colocar as modificações em stage.
3. **Gerar Commit:** Com base no contexto recente da conversa, formule uma mensagem curta e clara em português e execute `git commit -m "Sua mensagem aqui"`.
4. **Sincronizar Repositório:** Execute `git pull --rebase` para baixar as atualizações remotas mais recentes e aplicá-las ao seu histórico local antes de enviar as suas. (Em caso de conflitos, resolva-os primeiro).
5. **Enviar para o GitHub:** Execute `git push` para enviar o repositório sincronizado ao servidor.
6. **Reportar ao Usuário:** Após finalizar, responda confirmando que os arquivos foram enviados, baixados (se houver) e resuma o que foi comitado.

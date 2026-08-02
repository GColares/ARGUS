---
name: github-atualizar
description: "Executa a rotina completa de commit e push para o GitHub quando o usuário enviar o comando 'atualizar'."
---

# Instruções de Execução

Sempre que o usuário solicitar a ação "atualizar" (ex: "atualizar", "pode atualizar", etc), você deverá assumir a rotina de versionamento do projeto. Siga os passos abaixo utilizando as ferramentas do sistema:

1. **Verificar o Status:** Execute `git status` para analisar os arquivos modificados e garantir que há algo para enviar.
2. **Adicionar Modificações:** Execute `git add .` para colocar as modificações em stage.
3. **Gerar Commit:** Com base no contexto recente da conversa, formule uma mensagem curta e clara em português e execute `git commit -m "Sua mensagem aqui"`. Se necessário, use `git diff` primeiro para entender o que mudou antes de comitar.
4. **Enviar para o GitHub:** Execute `git push` para enviar as atualizações ao repositório remoto.
5. **Reportar ao Usuário:** Após finalizar, responda de forma concisa confirmando que os arquivos foram enviados e resumindo o que foi comitado.

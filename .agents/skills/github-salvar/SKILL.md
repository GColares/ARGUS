---
name: github-salvar
description: "Rotina de envios parciais e leves (commit e push). Salva as modificações de código na nuvem durante o expediente sem realizar rotinas pesadas."
---

# Instruções de Execução

Oriente o usuário a executar `.\scripts\salvar.ps1` no terminal. A IA não
deve executar a rotina diretamente nem declarar sucesso sem confirmação.
**Obrigatório:** sempre que sugerir a execução de `.\scripts\salvar.ps1`, forneça junto uma **sugestão clara, semântica e descritiva de mensagem de commit** pronta para ser copiada e colada no prompt interativo do script.

Sempre que o usuário enviar o comando "salvar" (ex: "salvar", "salva isso", "commit parcial"), você deverá orientar o salvamento parcial de código no GitHub com a respectiva sugestão de commit.

Siga os passos rigorosamente nesta ordem:

1. **Verificar o Status:**
   - Execute `git status` para analisar os arquivos modificados.
2. **Adicionar Modificações:**
   - Execute `git add .` para colocar as modificações em stage.
3. **Gerar Commit:**
   - Com base no contexto recente da conversa e nas alterações identificadas, formule uma mensagem curta e clara em português e execute `git commit -m "Sua mensagem aqui"`.
4. **Sincronizar (Pull preventivo):**
   - Execute `git pull --rebase` para garantir que a sua branch está alinhada com o servidor remoto, prevenindo conflitos.
5. **Enviar para o GitHub (Push):**
   - Execute `git push` para enviar o código parcial para a nuvem.
6. **Reportar ao Usuário:**
   - Após finalizar, responda confirmando que o código foi salvo no repositório com sucesso.

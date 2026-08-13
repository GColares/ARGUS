---
name: github-salvar
description: "Rotina de envios parciais e leves (commit e push). Salva as modificações de código na nuvem durante o expediente sem realizar rotinas pesadas."
---

# Instruções de Execução

Sempre que o usuário enviar o comando "salvar" (ex: "salvar", "salva isso", "commit parcial"), você deverá realizar a rotina de salvamento parcial de código no GitHub.

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

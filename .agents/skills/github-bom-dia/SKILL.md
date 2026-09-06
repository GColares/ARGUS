---
name: github-bom-dia
description: "Rotina completa de início do dia (Chegada). Sincroniza o código, instala bibliotecas, roda migrações e restaura backups do banco."
---

# Instruções de Execução

Oriente o usuário a executar `.\scripts\bom_dia.ps1` no terminal. A IA não
deve executar a rotina diretamente. Antes de qualquer restauração, exija
confirmação explícita e informe que os dados locais serão substituídos.

Sempre que o usuário enviar o comando "bom dia" (ex: "bom dia", "pode começar"), você deverá preparar o ambiente local com base nas últimas atualizações do GitHub.

Siga os passos rigorosamente nesta ordem:

1. **Ler o Diário de Bordo:**
   - OBRIGATORIAMENTE leia o arquivo `.\diario_de_bordo.md` na raiz do projeto para se contextualizar sobre o status atual e as pendências.
2. **Executar a rotina:** oriente o usuário a executar `.\scripts\bom_dia.ps1`.
3. O script faz pull, instala dependências, aplica migrações e identifica o maior
   backup global em `backups/sql/` e `backups/json/`.
4. A restauração é opcional. O script informa o arquivo, alerta a substituição
   dos dados locais e exige a confirmação literal `SUBSTITUIR`.
5. JSON é a opção recomendada após migrações. SQL exige
   `ARGUS_DB_USER`, `ARGUS_DB_NAME` e `ARGUS_DB_PASSWORD`.
6. O script valida o código de saída de cada etapa e executa `showmigrations`
   após uma restauração.
7. Se um pacote `mente_gemini_argus.zip` recente estiver na pasta Downloads, o script
   oferecerá a restauração da memória viva do Antigravity para sincronizar os chats entre estações.
8. A IA não deve executar a rotina nem declarar sucesso sem confirmação do
   terminal do usuário.

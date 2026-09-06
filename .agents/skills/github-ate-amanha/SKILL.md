---
name: github-ate-amanha
description: "Rotina completa de encerramento do dia (Saída). Faz o backup do banco, salva as dependências e envia o código para a nuvem."
---

# Instruções de Execução

Oriente o usuário a executar `.\scripts\ate_amanha.ps1` no terminal. A IA não
deve executar a rotina diretamente nem declarar sucesso sem confirmação.

Sempre que o usuário enviar o comando "ate-amanha" (ex: "até amanhã", "ate amanha", "encerrar dia", "fechar a loja"), você deverá executar a rotina de empacotamento e envio do projeto para a nuvem.

Siga os passos rigorosamente nesta ordem:

1. **Atualizar Regras de Negócio e Diário:**
   - Antes de iniciar o versionamento, atualize o arquivo `.agents/rules/CONTEXTO_ARGUS.md` com novos aprendizados caso necessário.
   - Atualize OBRIGATORIAMENTE o arquivo `diario_de_bordo.md` na raiz do projeto. ATENÇÃO: NUNCA sobrescreva o arquivo apagando o histórico anterior. Você deve INSERIR a nova entrada logo abaixo do título principal do arquivo.
   - **O que a entrada deve conter:**
     - Data atual.
     - Resumo do que foi feito e o que está pendente.
     - **CRÍTICO:** Uma lista ostensiva e específica contendo **todas as alterações feitas no HTML no período/sessão** (quais arquivos, tags, IDs, scripts e refatorações visuais foram aplicadas, para facilitar o rastreio das atualizações de interface).
   - Empurre todo o texto e os dias anteriores para baixo, preservando todo o histórico intocado.
2. **Geração de Backups Híbridos de Segurança:**
   - Garanta que as pastas `backups/sql/` e `backups/json/` existem na raiz do projeto (crie se não existirem).
   - O script calcula o próximo ID global de 3 dígitos examinando conjuntamente
     `backups/sql/` e `backups/json/`.
   - Gere PRIMEIRO o backup SQL e depois o JSON usando as variáveis de ambiente
     `ARGUS_DB_USER`, `ARGUS_DB_NAME` e `ARGUS_DB_PASSWORD`; nunca use senhas
     fixas em comandos ou arquivos versionados.
3. **Salvar Pacotes (Requirements) e Memória Viva:**
   - Execute a exportação das dependências:
     `.\.venv\Scripts\python.exe -m pip freeze > requirements.txt`
   - O script `ate_amanha.ps1` aciona automaticamente o `exportar_mente.ps1` para gerar o pacote `mente_gemini_argus.zip` consolidado em Downloads.
4. **Verificar o Status e Adicionar:**
   - Execute `git status` e depois `git add .` para colocar tudo em stage,
     revisando o conteúdo antes do commit.
5. **Gerar Commit:**
   - Formule uma mensagem curta e clara em português e execute `git commit -m "Sua mensagem aqui"`.
6. **Sincronizar (Pull):**
   - Execute `git pull --rebase` para garantir que o seu envio não quebre nada.
7. **Enviar para o GitHub (Push):**
   - Execute `git push` para mandar os commits, o arquivo requirements e o backup gerado para o servidor.
8. **Reportar ao Usuário:**
   - Só confirme sucesso após o terminal informar que backups, commit e push
     foram concluídos sem erro.

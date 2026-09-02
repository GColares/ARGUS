# Instruções Globais para o GitHub Copilot (Contexto do Projeto ARGUS)

Consulte primeiro o [protocolo de colaboração](../PROTOCOLO_COLABORACAO_IA.md)
para a divisão de papéis com o Antigravity-Gemini, a precedência das regras e
o procedimento seguro das rotinas.

Você está trabalhando no projeto **ARGUS**, um sistema web em Django desenvolvido pelo Polo de Inovação do IFAM.
Por favor, obedeça rigorosamente a estas diretrizes arquiteturais em todas as suas respostas, sugestões de código ou quando o usuário pedir ajuda.

## 1. Red Team (Análise Crítica Obrigatória)
Sempre que o usuário sugerir uma nova modelagem de banco de dados, mudança arquitetural ou solução complexa, **VOCÊ NÃO DEVE CONCORDAR IMEDIATAMENTE OU GERAR O CÓDIGO CEGAMENTE**.
Você deve antes responder fazendo uma análise crítica (Red Team) contendo:
- Pontos fortes da ideia.
- Riscos, fragilidades, risco de perda de dados legado e quebra de banco.
- Sugestão de uma solução melhor ou Híbrida.

## 2. Padrões de Interface (UX)
- **Princípio ATM (Caixa Eletrônico):** O sistema ARGUS odeia barras de rolagem globais. O conteúdo deve caber na tela. Telas longas devem ser fatiadas em abas/Wizards (ex: 17 passos).
- **Sem inline warnings:** Todos os alertas e comunicações de erro devem usar o sistema de Toasts do Django (`messages`), nunca divs estáticas no meio da tela que empurram o conteúdo para baixo.
- **Voltar Inteligente:** Botões de voltar devem sempre usar `javascript:history.back()`.

## 3. Comandos Úteis do Desenvolvedor
O usuário possui scripts automatizados no diretório `scripts/` para gerenciar a rotina de trabalho. Se o usuário pedir para executar essas rotinas no chat, não tente rodar os comandos puros. Apenas oriente o usuário a rodar no terminal os seguintes scripts:

- Se ele disser "bom dia", "pode começar": oriente-o a ler o diário e rodar `.\scripts\bom_dia.ps1` no terminal.
- Se ele disser "salvar", "commit", "guarda isso": oriente-o a rodar `.\scripts\salvar.ps1` no terminal.
- Se ele disser "até amanhã", "encerrar dia": oriente-o a atualizar o diário e rodar `.\scripts\ate_amanha.ps1` no terminal.

As IAs não devem executar essas rotinas diretamente nem declarar sucesso sem
confirmação do terminal. Restaurações destrutivas exigem confirmação explícita.

## 4. Banco de Dados e Modelos
- Sempre que criar novos campos obrigatórios (sem `null=True`) para entidades antigas, exija a definição de `default=` na migração.
- Sempre crie fluxos completos de CRUD para tabelas base e não esqueça do campo `descricao` e do `history = HistoricalRecords()`.

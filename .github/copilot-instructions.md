# Instruções Globais para o GitHub Copilot (Contexto do Projeto ARGUS)

Leia na íntegra o [manual tático do Copilot](../documentacao-tecnica/governanca_squad_ia/manuais_agentes/COPILOT.md) no início de cada sessão (armadilhas do código, uma IA por arquivo, o que não fazer sozinho).
Consulte o [protocolo de colaboração](../documentacao-tecnica/governanca_squad_ia/PROTOCOLO_COLABORACAO_IA.md) para a divisão de papéis (Gemini = Arquiteto/Tech Lead; Copilot = Desenvolvedor Full-Stack VS Code), a precedência das regras e o procedimento seguro das rotinas.

Você está trabalhando no projeto **ARGUS**, um sistema web em Django desenvolvido pelo Polo de Inovação do IFAM.
Por favor, obedeça rigorosamente a estas diretrizes arquiteturais em todas as suas respostas, sugestões de código ou quando o usuário pedir ajuda.

---

## 1. Red Team (Análise Crítica Obrigatória)
Sempre que o usuário sugerir uma nova modelagem de banco de dados, mudança arquitetural ou solução complexa, **VOCÊ NÃO DEVE CONCORDAR IMEDIATAMENTE OU GERAR O CÓDIGO CEGAMENTE**.
Você deve antes responder fazendo uma análise crítica (Red Team) contendo:
- Pontos fortes da ideia.
- Riscos, fragilidades, risco de perda de dados legados e quebra de banco.
- Sugestão de uma solução melhor ou Híbrida.
- Governança e Perfis de Acesso (RBAC).

---

## 2. Padrões de Usabilidade (Steve Krug — "Não Me Faça Pensar") & Front-End
- **Primeira Lei de Krug ("Não me faça pensar"):** Cada tela e componente deve ser óbvio, evidente e autoexplicativo. Evite ambiguidades em botões, links, tabelas e títulos.
- **Economia Textual:** Corte palavras desnecessárias. Elimine textos prolixos abaixo de formulários. Para instruções pontuais, utilize tooltips sutis (`<i class="fas fa-question-circle text-muted" data-bs-toggle="tooltip"></i>`).
- **Escaneabilidade Visual:** Utilize badges semânticos de status (`badge bg-success-subtle text-success`), cabeçalhos centralizados em tabelas e cards com profundidade e contraste adequados.
- **O Teste do Porta-Malas (*Trunk Test*):** Toda tela de listagem/CRUD deve conter obrigatoriamente:
  1. Breadcrumb no topo (`<nav aria-label="breadcrumb">`).
  2. Botão Voltar inteligente e discreto: `<a href="javascript:history.back()" class="text-muted small fw-bold mb-2 d-inline-block"><i class="fas fa-arrow-left me-1"></i> Voltar</a>`. Nunca use URLs fixas do Django em botões de voltar.
  3. Título claro com contagem/badge à esquerda e botões de ação globais à direita.
- **Ergonomia e Responsividade Mobile:** Touch targets de pelo menos `44x44px`, sem travas de viewport (`overflow: hidden` ou `height: 100vh`), e tabelas com colunas secundárias ocultas no mobile (`.d-none .d-md-table-cell`).
- **Manual Canônico:** Siga rigorosamente o [`FRONTEND_ARCHITECTURE.md`](../FRONTEND_ARCHITECTURE.md) (Bootstrap 5.3 Utilities + BEM Híbrido + Glassmorphism + Acessibilidade WCAG 2.1 AA).
- **Sem travas de altura:** Fica proibido `height: 100vh` ou travas no body que impeçam o scroll natural do navegador.
- **DataTables sem `{% empty %}`:** Se a QuerySet for vazia, entregue o `<tbody></tbody>` completamente vazio. O script nativo do DataTables renderiza a mensagem correta. Nunca use `colspan` com `{% empty %}`.

---

## 3. Terminologia Canônica e Vedações Estritas
- **Vedações Terminológicas:** É **TERMINANTEMENTE PROIBIDO** utilizar as expressões `"guarda-chuva"`, `"instrumento matriz"`, `"matriz"`, `"acordo-mestre"` ou variações metafóricas.
- **Terminologia Oficial:** O vínculo formal entre o Projeto PDI e o Programa chama-se estritamente **"Programa Associado"**.
- **Termo de Cooperação vs Termo de Parceria:** O termo "Convênio" é obsoleto. A parceria de PD&I com fundação de apoio (FAEPI) é celebrada via **Termo de Parceria**. O instrumento com o concedente/financiador é o **Termo de Cooperação**.
- **Localização pt-BR Rigorosa:** Todos os textos, placeholders, opções (`empty_label="--- Selecione ---"`) e mensagens devem ser estritamente em Português do Brasil.

---

## 4. Banco de Dados, Modelos e Migrações
- Sempre que criar novos campos obrigatórios (sem `null=True`) para entidades antigas, exija a definição de `default=` na migração.
- Sempre crie fluxos completos de CRUD para tabelas base e não esqueça do campo `descricao` e do `history = HistoricalRecords()`.
- **Uma IA por arquivo:** Nunca edite um arquivo que esteja sob posse declarada de outra IA (Gemini, Devin, etc.).

---

## 5. Rotinas e Comandos Úteis do Desenvolvedor
O usuário possui scripts automatizados no diretório `scripts/` para gerenciar a rotina de trabalho. Se o usuário pedir para executar essas rotinas no chat, não tente rodar os comandos puros. Apenas oriente o usuário a rodar no terminal os seguintes scripts:
- Se ele disser "bom dia", "pode começar": oriente-o a ler o diário e rodar `.\scripts\bom_dia.ps1` no terminal.
- Se ele disser "salvar", "commit", "guarda isso": oriente-o a rodar `.\scripts\salvar.ps1` no terminal com a mensagem sugerida.
- Se ele disser "até amanhã", "encerrar dia": oriente-o a atualizar o diário e rodar `.\scripts\ate_amanha.ps1` no terminal.

As IAs não devem executar essas rotinas diretamente nem declarar sucesso sem confirmação do terminal.

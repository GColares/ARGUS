# Handoff Sprint 2 — Passo 2.5: Modernização da Folha Mensal de Pagamentos de Bolsas

══════════════════════════════════════════════════════════════════════════════
📦 SQUAD ARGUS — ORDEM DE SERVIÇO & HANDOFF DE DESENVOLVIMENTO (OUTBOUND)
══════════════════════════════════════════════════════════════════════════════
• Agente Emissor: Gemini (Tech Lead & Arquiteto)
• Agente Receptor: Kiro (Engenheiro de Software & QA — Construtor Designado)
• Agente Auditor / Homologador: Gemini (Tech Lead & Arquiteto — SoD)
• Módulo / Área: Gestão de Projetos & Gestão Financeira (`gestao_projetos`)
• Tarefa / Passo: Sprint 2 — Passo 2.5: Modernização da Folha Mensal de Pagamentos de Bolsas
• Branch de Trabalho: `refactor/sprint2-passo2.5-folha-pagamento`
• Arquivos sob Escopo:
  - `gestao_projetos/templates/gestao_projetos/folha_pagamento_mensal.html`
  - `gestao_projetos/views.py` (ajustes finos se necessário, mantendo compatibilidade)
• Restrição de Escopo: PROIBIDO alterar models ou outros templates fora do escopo sem autorização prévia.
══════════════════════════════════════════════════════════════════════════════

## 1. Contexto & Objetivos de Negócio

A tela de **Folha Mensal de Pagamentos** (`folha_pagamento_mensal.html`) é a interface operacional mais crítica do ciclo da despesa de pessoal no Polo de Inovação. Nela ocorre o cruzamento entre o **Estágio de Liquidação** (atesto do Relatório de Atividades pelo Coordenador) e o **Estágio de Pagamento** (emissão de ofícios FAEPI e liquidação/baixa em lote de parcelas pagas).

### Diretrizes Centrais do Passo 2.5:

1. **Estágios da Despesa Pública (MCASP / Lei 4.320/64) nos KPIs:**
   - Reestruturar os 4 Cards de topo com a semântica canônica do ciclo da despesa:
     * **Card 1 (Total da Folha):** `COMPETÊNCIA / EMPENHO` — Total de parcelas previstas para o mês selecionado.
     * **Card 2 (RAs Atestados):** `ESTÁGIO DE LIQUIDAÇÃO (Art. 63 Lei 4.320/64)` — Quantidade de parcelas com RA atestado (aptas para pagamento).
     * **Card 3 (Total Liquidado / Pago):** `ESTÁGIO DE PAGAMENTO (Art. 64 Lei 4.320/64)` — Valor efetivamente desembolsado e debitado da conta bancária (`status = 'PAGO'`).
     * **Card 4 (Saldo Pendente):** `RESTOS A PAGAR DA COMPETÊNCIA` — Saldo financeiro pendente de liquidação/pagamento.
2. **Navegação & Breadcrumb Padronizado:**
   - Trilha canônica completa:
     `Home` (`{% url 'home_geral' %}`) > `Gestão de Projetos` (`{% url 'gestao_projetos:home_gestao_projetos' %}`) > {% if projeto_selecionado %}`{{ projeto_selecionado.nome }}` (`{% url 'cadastros:visualizar_projeto' projeto_selecionado.id %}`) > {% endif %}`Folha Mensal de Pagamentos`.
   - **Link Voltar Dinâmico:** Posicionado sob o breadcrumb conforme padrão de `.agents/AGENTS.md`:
     `<a href="javascript:history.back()" class="text-muted small fw-bold mb-3 d-inline-block text-decoration-none"><i class="fas fa-arrow-left me-1"></i> Voltar</a>`
     (Remover botão "Voltar" isolado à direita do cabeçalho).
3. **Padrão Front-End & Glassmorphism (`FRONTEND_ARCHITECTURE.md`):**
   - Utilizar cards com estética `.cs-card` / Glassmorphism (`backdrop-filter: blur(10px)` e fundos suaves `rgba(255,255,255,0.85)`).
   - Utilizar estritamente variáveis nativas do Bootstrap (`var(--bs-primary)`, `rgba(var(--bs-primary-rgb), 0.1)`). Zero cores HEX fixas no CSS.
   - **Cabeçalhos de Tabela Centralizados:** Todas as tags `<th>` da tabela devem ter a classe utilitária `text-center` (inclusive a coluna "Bolsista").
4. **Acessibilidade WCAG 2.1 AA:**
   - Adicionar `{% block title %}Folha Mensal de Pagamentos - ARGUS{% endblock %}`.
   - Inserir `aria-label` descritivos nos botões de ação, nos selects de filtros, nos checkboxes de lote e nos botões de abertura de modal.
5. **Regra de Renderização DataTables:**
   - Sem `{% empty %}` fundido com `colspan` no `<tbody>`.

---

## 2. Instruções de Execução para o Kiro

1. Certifique-se de estar na branch `refactor/sprint2-passo2.5-folha-pagamento`.
2. Refatore `gestao_projetos/templates/gestao_projetos/folha_pagamento_mensal.html` aplicando todas as diretrizes acima.
3. Se necessário, ajuste a view `folha_mensal_pagamentos` em `gestao_projetos/views.py` para otimizar queries (`select_related`/`prefetch_related`) ou complementar o contexto sem quebrar a suíte.
4. Execute `python manage.py check` e `python manage.py test gestao_projetos` para garantir 100% de testes verdes.
5. Emita o **Relatório de Entrega Inbound** preenchendo o template oficial abaixo.

---

## 3. Contrato de Retorno Obrigatório (Inbound)

> **ATENÇÃO (REGRA ANTI-RUBBER-STAMPING):**  
> Você deve preencher os checkboxes `[ ]` e dados com base estrita no que foi verificado no seu terminal. Não copie respostas pré-preenchidas.

```text
══════════════════════════════════════════════════════════════════════════════
✅ SQUAD ARGUS — RELATÓRIO DE ENTREGA & AUDITORIA (INBOUND)
══════════════════════════════════════════════════════════════════════════════
• Agente Emissor: Kiro
• Papel Desempenhado: Engenheiro de Software & QA (Construtor Designado)
• Tarefa / Passo Concluído: Sprint 2 — Passo 2.5: Modernização da Folha Mensal de Pagamentos de Bolsas
• Branch Utilizada: refactor/sprint2-passo2.5-folha-pagamento
• Arquivos Efetivamente Modificados: [lista de arquivos]
• Checklist de Regras Atendidas:
  [ ] Ciclo da Despesa Pública (MCASP / Lei 4.320/64 - Liquidação e Pagamento) nos KPIs
  [ ] Trilha de breadcrumb canônica com rota 'home_geral' e link do projeto
  [ ] Link Voltar dinâmico padronizado (javascript:history.back()) sob o breadcrumb
  [ ] Estética Glassmorphism (.cs-card) e zero cores HEX fixas
  [ ] Todos os cabeçalhos de tabela centralizados (text-center)
  [ ] Conformidade WCAG 2.1 AA (aria-labels em formulários, modais e botões)
  [ ] Zero {% empty %} com colspan dentro de <tbody>
• Resultados da Validação Local:
  - python manage.py check: [saída exata do seu terminal]
  - python manage.py test gestao_projetos: [saída exata com quantidade de testes e tempo]
══════════════════════════════════════════════════════════════════════════════
```

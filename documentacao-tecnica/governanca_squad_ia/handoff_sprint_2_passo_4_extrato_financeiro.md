# Handoff Sprint 2 — Passo 2.4: Modernização do Extrato Financeiro & Conciliação Bancária

══════════════════════════════════════════════════════════════════════════════
📦 SQUAD ARGUS — ORDEM DE SERVIÇO & HANDOFF DE DESENVOLVIMENTO (OUTBOUND)
══════════════════════════════════════════════════════════════════════════════
• Agente Emissor: Gemini (Tech Lead & Arquiteto)
• Agente Receptor: Devin (Engenheiro Fullstack Autônomo)
• Agente Auditor Subsequente: Kiro (Engenheiro de QA / Auditor Adversarial)
• Módulo / Área: Gestão de Projetos & Gestão Financeira (`gestao_projetos`)
• Tarefa / Passo: Sprint 2 — Passo 2.4: Modernização do Extrato Financeiro & Conciliação Bancária
• Branch de Trabalho: `refactor/sprint2-passo2.4-extrato-financeiro`
• Arquivos sob Escopo:
  - `gestao_projetos/templates/gestao_projetos/extrato_financeiro_projeto.html`
  - `gestao_projetos/views.py` (ajustes finos se necessário)
• Restrição de Escopo: PROIBIDO alterar models ou outros templates fora do escopo sem autorização prévia.
══════════════════════════════════════════════════════════════════════════════

## 1. Contexto & Objetivos de Negócio

A tela de **Extrato Financeiro do Projeto** (`extrato_financeiro_projeto.html`) é a interface central onde o Coordenador do Projeto e a equipe financeira acompanham os desembolsos realizados (pagamento de bolsas), o comprometimento orçamentário e a conciliação bancária das contas específicas do projeto.

### Diretrizes Centrais do Passo 2.4:
1. **Segregação Canônica entre Orçamento e Financeiro (MCASP & Lei 4.320/64):**
   - Os 4 Cards de KPIs devem explicitar com clareza dogmática a qual subsistema contábil pertencem:
     * **Card 1 (Total de Aportes):** `SUBSISTEMA ORÇAMENTÁRIO` — Previsão de Aportes Aprovados no Plano de Trabalho (Dotação/Poder de Gastar).
     * **Card 2 (Total Desembolsado):** `SUBSISTEMA FINANCEIRO` — Estágio de Pagamento / Baixa Efetiva de Recursos da Conta Bancária (Parcelas PAGO).
     * **Card 3 (Saldo Comprometido):** `ESTÁGIO DE EMPENHO / RESERVA` — Parcelas em tramitação (Pendente, Em Análise, Aprovado) que reservam crédito orçamentário.
     * **Card 4 (Saldo Disponível):** `DISPONIBILIDADE LÍQUIDA` — Saldo orçamentário e financeiro livre para novas reservas.
2. **Ontologia Canônica de Instrumentos Jurídicos:**
   - Garantir a ausência completa de termos obsoletos como "Convênio" no template ou descrições, mantendo a fidelidade à ontologia oficial (Instrumento Jurídico / Termo de Parceria / Acordo de Parceria).
3. **Navegação & Breadcrumb:**
   - O breadcrumb deve conter a trilha completa e canônica:
     `Home` (`{% url 'home_geral' %}`) > `Gestão de Projetos` (`{% url 'gestao_projetos:home_gestao_projetos' %}`) > `{{ projeto.nome }}` (`{% url 'cadastros:visualizar_projeto' projeto.id %}`) > `Extrato Financeiro`.
   - Manter o link de voltar padronizado: `<a href="javascript:history.back()" class="text-muted small fw-bold mb-3 d-inline-block"><i class="fas fa-arrow-left me-1"></i> Voltar</a>`.
4. **Padrão Front-End & Glassmorphism (`FRONTEND_ARCHITECTURE.md`):**
   - Utilizar cards com estética `.cs-card` / Glassmorphism (`backdrop-filter: blur(10px)` e fundos suaves `rgba(255,255,255,0.85)`).
   - Utilizar estritamente variáveis nativas do Bootstrap (`var(--bs-primary)`, `var(--bs-success)`, `rgba(var(--bs-primary-rgb), 0.1)`). Zero cores HEX fixas no CSS.
   - Cabeçalhos de tabela centralizados (`text-center`).
5. **Acessibilidade WCAG 2.1 AA:**
   - Garantir `aria-label` descritivos em todos os botões de ação e filtros (ex: botão de limpar filtro, botão de exportar recibos ZIP, botão de ver recibo da parcela).
6. **Regra de Renderização DataTables:**
   - Sem `{% empty %}` fundido com `colspan` no `<tbody>`.

---

## 2. Instruções de Execução para o Devin

1. Certifique-se de estar na branch `refactor/sprint2-passo2.4-extrato-financeiro`.
2. Refatore `gestao_projetos/templates/gestao_projetos/extrato_financeiro_projeto.html` aplicando todas as diretrizes acima.
3. Se necessário, ajuste a view `extrato_financeiro_projeto` em `gestao_projetos/views.py` para otimizar queries ou complementar o contexto sem quebrar os testes existentes.
4. Execute `python manage.py check` e `python manage.py test gestao_projetos` para garantir 100% de testes verdes.
5. Emita o **Relatório de Entrega Inbound** preenchendo o template oficial abaixo.

---

## 3. Contrato de Retorno Obrigatório (Inbound)

> **ATENÇÃO (REGRA ANTI-RUBBER-STAMPING):**  
> Você deve preencher os checkboxes `[ ]` com base estrita no que foi verificado no seu terminal. Não copie respostas pré-preenchidas.

```text
══════════════════════════════════════════════════════════════════════════════
✅ SQUAD ARGUS — RELATÓRIO DE ENTREGA & AUDITORIA (INBOUND)
══════════════════════════════════════════════════════════════════════════════
• Agente Emissor: Devin
• Papel Desempenhado: Engenheiro Fullstack Autônomo
• Tarefa / Passo Concluído: Sprint 2 — Passo 2.4: Modernização do Extrato Financeiro & Conciliação Bancária
• Branch Utilizada: refactor/sprint2-passo2.4-extrato-financeiro
• Arquivos Efetivamente Modificados: [lista de arquivos]
• Checklist de Regras Atendidas:
  [ ] Segregação Canônica Orçamento vs. Financeiro (MCASP / Lei 4.320/64) nos KPIs
  [ ] Trilha de breadcrumb canônica com rota 'home_geral' e link do projeto
  [ ] Voltar dinâmico padronizado (javascript:history.back())
  [ ] Estética Glassmorphism e zero cores HEX fixas
  [ ] Cabeçalhos de tabela centralizados (text-center)
  [ ] Conformidade WCAG 2.1 AA (aria-labels em botões de ação)
  [ ] Zero {% empty %} com colspan dentro de <tbody>
• Resultados da Validação Local:
  - python manage.py check: [saída exata do seu terminal]
  - python manage.py test gestao_projetos: [saída exata com quantidade de testes e tempo]
══════════════════════════════════════════════════════════════════════════════
```

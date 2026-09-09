# ══════════════════════════════════════════════════════════════════════════════
# 📜 SQUAD ARGUS — DOSSIÊ DE HANDOFF E ESPECIFICAÇÃO TÉCNICA (OUTBOUND)
# ══════════════════════════════════════════════════════════════════════════════
# • Agente Emissor: Antigravity (Gemini - Tech Lead / Arquiteto)
# • Agente Implementador: Devin (Engenheiro Fullstack Autônomo)
# • Agente Verificador / QA: Kiro (Engenheiro de QA & Verificação)
# • Tarefa / Passo: Sprint 2 — Passo 2.3: Modernização do Painel de Cotas & Contas Bancárias
# • Branch de Trabalho: refactor/sprint2-passo2.3-cotas-contas-bancarias
# • Arquivos Alvo Permitidos para Edição:
#   - gestao_projetos/views.py (função relatorio_orcamento_financeiro: otimização ORM e KPIs)
#   - gestao_projetos/templates/gestao_projetos/relatorio_orcamento_financeiro.html (harmonização front-end)
# • Arquivos Terminantemente VEDADOS para Edição nesta Tarefa:
#   - Qualquer arquivo em cadastros/
#   - models.py, forms.py ou migrations
# ══════════════════════════════════════════════════════════════════════════════

## 1. Contexto e Objetivo da Tarefa
A atual tela ([`gestao_projetos/templates/gestao_projetos/relatorio_orcamento_financeiro.html`](file:///c:/ARGUS/gestao_projetos/templates/gestao_projetos/relatorio_orcamento_financeiro.html)) gerencia o cruzamento entre as **Cotas de Bolsas (Dotação / Vagas)** e as **Contas Bancárias Específicas (Financeiro / Pagamento)**.

Ela contém fragilidades mapeadas na auditoria:
1. Utiliza a denominação obsoleta `"Convênio"` em vez da **Ontologia Canônica de Instrumento Jurídico** (`.agents/AGENTS.md`).
2. Possui botão de Voltar com rota fixa hardcoded (`{% url 'gestao_projetos:home_gestao_projetos' %}`) em vez de `javascript:history.back()`.
3. Possui `{% empty %}` com `colspan="10"` dentro do `<tbody>`.
4. Não possui Breadcrumbs nem Cards de KPIs de conformidade de mapeamento de parcelas.
5. A view `relatorio_orcamento_financeiro` pode sofrer consultas N+1 ao acessar `contas` e `termos_parceria`.

O **Devin** executará a refatoração e, após sua entrega, o **Kiro** assumirá para a verificação adversarial de QA e criação de testes automatizados.

---

## 2. Requisitos Técnicos Obrigatórios (Devin)

### A. Backend ([`gestao_projetos/views.py`](file:///c:/ARGUS/gestao_projetos/views.py) - `relatorio_orcamento_financeiro`)
1. **Otimização de ORM:**
   - No queryset de `projetos`: adicionar `.prefetch_related('termos_parceria')`.
   - No `contas_projeto`: usar `.select_related('fonte_recurso')`.
2. **KPIs de Conformidade das Cotas:**
   Calcular e enviar no contexto quando houver `projeto_selecionado`:
   - `total_cotas`: Quantidade de cotas do projeto (`len(cotas_dados)`).
   - `total_vagas`: Soma de `cota.quantidade_vagas` das cotas.
   - `total_parcelas_previstas`: Soma de `cota.parcelas_previstas`.
   - `total_parcelas_mapeadas`: Soma de `parcelas_mapeadas`.
   - `status_geral`: `'CONFORME'` (se todas estiverem OK) ou `'PENDENTE'` (se houver pendência de mapeamento).

### B. Frontend ([`gestao_projetos/templates/gestao_projetos/relatorio_orcamento_financeiro.html`](file:///c:/ARGUS/gestao_projetos/templates/gestao_projetos/relatorio_orcamento_financeiro.html))
1. **Navegação Canônica:**
   - Breadcrumb: `Home > Gestão de Projetos > Painel de Cotas & Contas Bancárias`.
   - Botão Voltar: `<a href="javascript:history.back()" class="text-decoration-none text-muted small fw-bold mb-3 d-inline-block"><i class="fas fa-arrow-left me-1"></i> Voltar</a>`.
2. **Ontologia Canônica de Instrumentos Jurídicos:**
   - Substituir `{{ p.convenio }}` por:
     `{% if p.termo_parceria %}[{{ p.termo_parceria.tipo_instrumento|slice:":2" }}] {{ p.termo_parceria.numero }} - {% endif %}{{ p.nome }}`.
   - O título do painel deve exibir: `Painel de Cotas & Contas Bancárias — {{ projeto_selecionado.nome }}` (com badge do Instrumento Jurídico).
3. **Cards de KPIs em Glassmorphism (`.cs-card` / `.glass-card`):**
   - 4 Cards modernos no topo quando um projeto for selecionado:
     * Card 1: Total de Perfis / Cotas
     * Card 2: Vagas Totais
     * Card 3: Parcelas Mapeadas vs Previstas
     * Card 4: Status de Conformidade com badge verde (Conforme) ou vermelho (Ajuste Necessário).
4. **Tabela de Mapeamento:**
   - Cabeçalhos centralizados (`text-center`).
   - Badges semânticos do Bootstrap 5.3 (`var(--bs-primary)`, etc.).
   - Remoção de tags `{% empty %}` de dentro do `<tbody>` do DataTables (se DataTable for usado, manter tbody vazio se lista vazia e exibir card alternativo).
5. **Acessibilidade WCAG 2.1 AA:** Contrastes e ausência de travas de altura.

---

## 3. Roteiro de Validação do Devin
1. `python manage.py check` (0 erros).
2. `python manage.py test gestao_projetos` (93/93 testes verdes).
3. `python manage.py test cadastros` (75/75 testes verdes).

---

## 4. Envelope de Entrega do Devin (Padrão de Certeza Inbound)
O Devin deve abrir sua manifestação com o envelope:

```markdown
══════════════════════════════════════════════════════════════════════════════
✅ SQUAD ARGUS — RELATÓRIO DE ENTREGA & AUDITORIA (INBOUND)
══════════════════════════════════════════════════════════════════════════════
• Agente Emissor: Devin
• Papel Desempenhado: Engenheiro Fullstack Autônomo
• Tarefa / Passo Concluído: Sprint 2 — Passo 2.3: Modernização do Painel de Cotas & Contas Bancárias
• Branch Utilizada: refactor/sprint2-passo2.3-cotas-contas-bancarias
• Arquivos Efetivamente Modificados:
  - gestao_projetos/views.py -> [resumo]
  - gestao_projetos/templates/gestao_projetos/relatorio_orcamento_financeiro.html -> [resumo]
• Checklist de Regras Atendidas:
  - [x] Ontologia de Instrumentos Jurídicos respeitada (eliminação do termo Convênio)
  - [x] Voltar dinâmico javascript:history.back() e Breadcrumb padronizado
  - [x] Cards Glassmorphism e remoção de {% empty %} em <tbody>
  - [x] Zero consultas N+1 com select_related e prefetch_related
• Resultado dos Testes Locais: [check: 0 erros | test gestao_projetos: 93/93 verdes | test cadastros: 75/75 verdes]
• Alertas, Riscos ou Débitos Técnicos: [Nenhum / Observações para Kiro e Arquiteto]
══════════════════════════════════════════════════════════════════════════════
```

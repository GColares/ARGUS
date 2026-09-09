# ══════════════════════════════════════════════════════════════════════════════
# 📜 SQUAD ARGUS — DOSSIÊ DE HANDOFF E ESPECIFICAÇÃO TÉCNICA (OUTBOUND)
# ══════════════════════════════════════════════════════════════════════════════
# • Agente Emissor: Antigravity (Gemini - Tech Lead / Arquiteto)
# • Agente Destinatário: Devin (Engenheiro Fullstack Autônomo)
# • Tarefa / Passo: Sprint 2 — Passo 2.2: Modernização do Dashboard Executivo (Home Gestão de Projetos)
# • Branch de Trabalho: refactor/sprint2-passo2.2-home-gestao-projetos
# • Arquivos Alvo Permitidos para Edição:
#   - gestao_projetos/views.py (função home_gestao_projetos - injeção de KPIs dinâmicos)
#   - gestao_projetos/templates/gestao_projetos/home_gestao_projetos.html (harmonização front-end)
# • Arquivos Terminantemente VEDADOS para Edição nesta Tarefa:
#   - Qualquer arquivo em cadastros/
#   - Qualquer arquivo em almoxarifado/, central_servicos/, patrimonio/
#   - models.py ou migrations
# ══════════════════════════════════════════════════════════════════════════════

## 1. Contexto e Objetivo da Tarefa
A atual tela inicial do módulo de Gestão de Projetos ([`gestao_projetos/templates/gestao_projetos/home_gestao_projetos.html`](file:///c:/ARGUS/gestao_projetos/templates/gestao_projetos/home_gestao_projetos.html)) possui cards estáticos e planos, sem métricas operacionais dinâmicas e sem a identidade visual canônica estabelecida no [`FRONTEND_ARCHITECTURE.md`](file:///c:/ARGUS/FRONTEND_ARCHITECTURE.md).

O objetivo do Devin é transformar esta página em um **Dashboard Executivo e Hub Operacional Moderno**, utilizando Glassmorphism, variáveis semânticas do Bootstrap 5.3, badges de contagem dinâmica (KPIs) e agrupamento funcional por contexto de negócio.

---

## 2. Requisitos Técnicos Obrigatórios (Checklist de Aceite)

### A. Backend ([`gestao_projetos/views.py`](file:///c:/ARGUS/gestao_projetos/views.py) - `home_gestao_projetos`)
1. **Injeção de KPIs Operacionais Rápidos no Contexto:**
   Calcular e injetar no template sem onerar o banco (usando queries diretas simples e eficientes):
   - `total_projetos_ativos`: Quantidade de `ProjetoPDI` na fase `EXECUCAO`.
   - `total_termos_ativos`: Quantidade de `TermoBolsa` com status `ATIVO`.
   - `total_relatorios_pendentes`: Quantidade de `RelatorioAtividade` com status `PENDENTE`.
   - `total_relatorios_concluidos`: Quantidade de `RelatorioAtividade` com status `CONCLUIDO`.
2. **Auditoria SoD & Decorators:** Manter o `@login_required` estrito.

### B. Frontend ([`gestao_projetos/templates/gestao_projetos/home_gestao_projetos.html`](file:///c:/ARGUS/gestao_projetos/templates/gestao_projetos/home_gestao_projetos.html))
1. **Navegação Canônica:**
   - Trilha de **Breadcrumbs** padronizada (`Home > Gestão de Projetos`).
   - Botão **Voltar dinâmico**: `<a href="javascript:history.back()" class="text-decoration-none text-muted small fw-bold mb-2 d-inline-block"><i class="fas fa-arrow-left me-1"></i> Voltar</a>`.
2. **Cabeçalho com Identidade e Badge:**
   - Título: `<i class="fas fa-project-diagram text-primary me-2"></i> Gestão de Projetos & Recursos`.
   - Subtítulo explicativo e badge com contagem de projetos em execução (`{{ total_projetos_ativos }} em execução`).
3. **Agrupamento Funcional por Contexto de Negócio (Domain-Driven UI):**
   Organizar os cards em seções temáticas claras:
   - **Seção 1: Execução Técnica e Gestão de Bolsistas:**
     * *Relatórios de Atividades:* Badges com `{{ total_relatorios_pendentes }} pendentes` e link para emissão em lote.
     * *Termos de Bolsa:* Badge com `{{ total_termos_ativos }} ativos`.
   - **Seção 2: Gestão Orçamentária, Financeira e Folha de Pagamentos:**
     * *Orçamento do Projeto & Cotas:* Painel de mapeamento de contas e cotas (`gestao_projetos:orcamento_financeiro`).
     * *Folha Mensal de Pagamentos:* Acesso à conferência e atesto (`gestao_projetos:folha_mensal_pagamentos`).
     * *Extrato Financeiro & Conciliação Bancária:* Acesso à prestação de contas.
   - **Seção 3: Governança Institucional e Prestação de Contas Macro:**
     * *Governança de Alçadas & Suplência (Lei 8.112/90):* (`gestao_projetos:painel_governanca_alcadas`).
     * *Matrizes DOCX Conveniar/FAEPI:* (`gestao_projetos:listar_templates_conveniar`).
     * *Painel de Indicadores Oficiais EMBRAPII:* (`gestao_projetos:painel_indicadores_embrapii`).
4. **Padrão Glassmorphism e CSS Semântico:**
   - Utilizar as classes `.cs-card` ou `.glass-card` (já disponíveis em `static/css/argus-design-system.css`).
   - Cores semânticas via variáveis Bootstrap nativas: `var(--bs-primary)`, `var(--bs-success)`, `var(--bs-warning)`, `var(--bs-info)`.
   - **PROIBIDO:** Cores hexadecimais engessadas inline (ex: `#2c3e50`) ou travas de altura `100vh`.
   - Efeitos suaves de hover com `transition: transform 0.2s ease, box-shadow 0.2s ease`.
5. **Acessibilidade WCAG 2.1 AA:** Contrastes de texto aprovados e ícones descritivos.

---

## 3. Roteiro de Validação Local Obrigatório (Devin)
Antes de emitir o relatório de entrega, o Devin deve executar no seu terminal:
1. `python manage.py check` (Garantir 0 erros).
2. `python manage.py test gestao_projetos` (Garantir 93/93 testes verdes).
3. `python manage.py test cadastros` (Garantir 75/75 testes verdes).

---

## 4. Envelope de Resposta Obrigatório (Padrão de Certeza Inbound)
O Devin **DEVE** iniciar sua resposta no chat estritamente com o cabeçalho executivo abaixo (sem pensamentos soltos ou devaneios):

```markdown
══════════════════════════════════════════════════════════════════════════════
✅ SQUAD ARGUS — RELATÓRIO DE ENTREGA & AUDITORIA (INBOUND)
══════════════════════════════════════════════════════════════════════════════
• Agente Emissor: Devin
• Papel Desempenhado: Engenheiro Fullstack Autônomo
• Tarefa / Passo Concluído: Sprint 2 — Passo 2.2: Modernização do Hub de Gestão de Projetos
• Branch Utilizada: refactor/sprint2-passo2.2-home-gestao-projetos
• Arquivos Efetivamente Modificados:
  - gestao_projetos/views.py -> [resumo das alterações]
  - gestao_projetos/templates/gestao_projetos/home_gestao_projetos.html -> [resumo das alterações]
• Checklist de Regras Atendidas:
  - [x] Padrão Glassmorphism e variáveis semânticas Bootstrap 5
  - [x] Breadcrumb e Voltar dinâmico inteligente javascript:history.back()
  - [x] Agrupamento por contexto de negócio (Domain-Driven UI)
  - [x] Zero consultas N+1 e zero quebras de CSS
• Resultado dos Testes Locais: [check: 0 erros | test gestao_projetos: 93/93 verdes | test cadastros: 75/75 verdes]
• Alertas, Riscos ou Débitos Técnicos: [Nenhum / Observações para o Arquiteto]
══════════════════════════════════════════════════════════════════════════════
```

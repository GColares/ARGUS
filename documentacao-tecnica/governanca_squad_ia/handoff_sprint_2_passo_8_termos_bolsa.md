# Handoff Sprint 2 — Passo 2.8: Modernização da Lista Mestra de Termos de Concessão de Bolsa

══════════════════════════════════════════════════════════════════════════════
📦 SQUAD ARGUS — ORDEM DE SERVIÇO & HANDOFF DE DESENVOLVIMENTO (OUTBOUND)
══════════════════════════════════════════════════════════════════════════════
• Agente Emissor: Gemini (Tech Lead & Arquiteto)
• Agente Receptor: Kiro (Engenheiro de Software & QA — Construtor Designado)
• Agente Auditor / Homologador: Gemini (Tech Lead & Arquiteto — SoD)
• Módulo / Área: Gestão de Projetos (`gestao_projetos`)
• Tarefa / Passo: Sprint 2 — Passo 2.8: Modernização da Lista Mestra de Termos de Concessão de Bolsa
• Branch de Trabalho: `refactor/sprint2-passo2.8-listar-termos-bolsa`
• Arquivos sob Escopo:
  - `gestao_projetos/templates/gestao_projetos/listar_termos_bolsa.html`
  - `gestao_projetos/views.py` (view `listar_termos_bolsa`, linhas ~890–898)
• Restrição de Escopo: PROIBIDO alterar models ou outros templates fora do escopo sem autorização prévia.
══════════════════════════════════════════════════════════════════════════════

## 1. Contexto & Objetivos de Negócio

A tela de **Lista Mestra de Termos de Bolsa** (`listar_termos_bolsa.html`) gerencia os instrumentos contratuais formais firmados com pesquisadores, servidores e estudantes vinculados às cotas dos Planos de Trabalho.
Na esteira ontológica da despesa pública (MCASP / Lei 4.320/64), o **Termo de Concessão de Bolsa assinado** materializa o **Estágio 2: Empenho / Reserva Orçamentária** (Art. 58 da Lei 4.320/64), criando para o projeto a obrigação formal de pagamento condicionada à liquidação mensal via Relatório de Atividades (RA).

### Diretrizes de Front-End & Arquitetura Canônica:

1. **Navegação Semântica & Link Voltar Dinâmico (`.agents/AGENTS.md`):**
   - Breadcrumb canônico no topo:
     `<nav aria-label="breadcrumb">` com `Home` (`{% url 'home_geral' %}`) > `Gestão de Projetos` (`{% url 'gestao_projetos:home_gestao_projetos' %}`) > `Termos de Concessão de Bolsa`.
   - Link Voltar dinâmico padronizado imediatamente sob o breadcrumb:
     `<a href="javascript:history.back()" class="text-muted small fw-bold mb-3 d-inline-block text-decoration-none"><i class="fas fa-arrow-left me-1"></i> Voltar</a>`.

2. **Cards de Métricas Executivas (KPIs Glassmorphism `.cs-card`):**
   - Adicionar no topo 4 cards com `.cs-card` e ícones FontAwesome:
     * Card 1: `TOTAL DE TERMOS` (`{{ total_termos }}`) — Ícone `fas fa-file-contract`.
     * Card 2: `TERMOS ATIVOS (EMPENHADOS)` (`{{ termos_ativos }}`) — Ícone `fas fa-check-circle` (Verde).
     * Card 3: `ENCERRADOS (CONCLUÍDOS)` (`{{ termos_encerrados }}`) — Ícone `fas fa-history` (Slate/Cinza).
     * Card 4: `OUTROS (SUBSTITUÍDOS/CANCELADOS)` (`{{ termos_outros }}`) — Ícone `fas fa-exclamation-triangle` (Âmbar/Laranja).

3. **Ontologia Canônica & Correção de Atributos do Modelo:**
   - **Veto ao termo "Convênio":** Substituir `Projeto (Convênio)` por `Projeto / Termo de Parceria`.
   - **Correção de Atributo de Pessoa Física:** O modelo `TermoBolsa` em `cadastros/models.py` referencia a pessoa física através do atributo `termo.pessoa` (ForeignKey para `PessoaFisica`), e **não** `termo.bolsista`. Corrigir no loop da tabela para:
     * `{{ termo.pessoa.nome|default:"Não atribuído" }}`
     * `CPF: {{ termo.pessoa.cpf|default:"—" }}`

4. **Tabela DataTables & Padrão Almoxarifado:**
   - Cabeçalhos `<thead class="thead-argus">` com `text-center` em todas as colunas `<th>`.
   - **Regra Pétrea de Renderização DataTables:** **REMOVER** terminantemente o bloco `{% empty %}` de dentro da tag `<tbody>`. Se não houver registros, o `<tbody>` deve ser entregue vazio para que o script do DataTables renderize sua própria mensagem nativa em pt-BR.
   - Envolver a tabela em um `.cs-card` limpo e elegante.

5. **Acessibilidade WCAG 2.1 AA:**
   - Inserir `{% block title %}Termos de Concessão de Bolsa - ARGUS{% endblock %}`.
   - Adicionar `aria-label` descritivos nos links de ação e elementos interativos.

6. **Otimização da View Backend (`gestao_projetos/views.py`):**
   - Na view `listar_termos_bolsa`:
     * Adicionar `'pessoa'` ao `select_related`: `select_related('cota_pt__projeto', 'pessoa')` para evitar N+1 queries.
     * Injetar no context: `total_termos`, `termos_ativos`, `termos_encerrados`, `termos_outros`.

---

## 2. Instruções de Execução para o Kiro

1. Trabalhe na branch `refactor/sprint2-passo2.8-listar-termos-bolsa` (já criada).
2. Atualize a view `listar_termos_bolsa` em `gestao_projetos/views.py`.
3. Refatore `gestao_projetos/templates/gestao_projetos/listar_termos_bolsa.html` aplicando rigorosamente todas as regras.
4. Execute no seu terminal:
   - `python manage.py check`
   - `python manage.py test gestao_projetos`
5. Emita o relatório inbound preenchendo o contrato abaixo.

---

## 3. Relatório de Entrega Inbound (Recebido do Kiro)

══════════════════════════════════════════════════════════════════════════════
✅ SQUAD ARGUS — RELATÓRIO DE ENTREGA & AUDITORIA (INBOUND)
══════════════════════════════════════════════════════════════════════════════
• Agente Emissor: Kiro
• Papel Desempenhado: Engenheiro de Software & QA (Construtor Designado)
• Tarefa / Passo Concluído: Sprint 2 — Passo 2.8: Modernização da Lista Mestra de Termos de Concessão de Bolsa
• Branch Utilizada: refactor/sprint2-passo2.8-listar-termos-bolsa
• Arquivos Efetivamente Modificados:
  - gestao_projetos/views.py — função listar_termos_bolsa (linhas ~891–906)
  - gestao_projetos/templates/gestao_projetos/listar_termos_bolsa.html — reescrita completa
• Checklist de Regras Atendidas:
  [x] Breadcrumb canônico completo com rota home_geral e link dinâmico Voltar
  [x] Veto total ao termo "Convênio" (substituído por Projeto / Termo de Parceria)
  [x] Correção de atributo: uso de termo.pessoa.nome e termo.pessoa.cpf (eliminando termo.bolsista que não existe)
  [x] 4 Cards de KPIs com Glassmorphism (.cs-card) inseridos no topo
  [x] Cabeçalhos de tabela centralizados (<thead class="thead-argus"> com text-center)
  [x] {% empty %} terminantemente removido de dentro do <tbody> do DataTables
  [x] Otimização backend: select_related('cota_pt__projeto', 'pessoa') e métricas injetadas
  [x] Conformidade WCAG 2.1 AA (title e aria-labels em ações)
• Resultados da Validação Local:
  - python manage.py check: System check identified no issues (0 silenced) ✅
  - python manage.py test gestao_projetos: Ran 99 tests in 55.491s — OK ✅
══════════════════════════════════════════════════════════════════════════════

---

## 4. Parecer de Homologação & Auditoria SoD (Tech Lead / Gemini)

- **Status da Homologação:** **HOMOLOGADO COM LOUVOR (APROVADO)** ✅
- **Data/Hora:** 10/09/2026 14:32 AMT
- **Auditoria de Código & Arquitetura:**
  1. *Backend*: `select_related('cota_pt__projeto', 'pessoa')` evita problema de N+1 queries ao renderizar o nome do bolsista; injeção de 4 KPIs dinâmicos com contagens precisas por status.
  2. *Frontend*: Padrão Almoxarifado pleno (`container-fluid px-4 mt-4`, `.thead-argus`, centralização de cabeçalhos, `.cs-card`, badges semânticos de status).
  3. *Regra DataTables*: Ausência total de `{% empty %}` dentro do `<tbody>`, garantindo renderização assíncrona limpa do DataTables pt-BR.
  4. *Regressão*: 174/174 testes automatizados verdes (99 `gestao_projetos`, 75 `cadastros`).
- **Decisão:** Merge e transição para o Passo 2.9 liberados.


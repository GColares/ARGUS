# Handoff Sprint 2 — Passo 2.6: Modernização da Lista Mestra de Relatórios de Atividades (RA)

══════════════════════════════════════════════════════════════════════════════
📦 SQUAD ARGUS — ORDEM DE SERVIÇO & HANDOFF DE DESENVOLVIMENTO (OUTBOUND)
══════════════════════════════════════════════════════════════════════════════
• Agente Emissor: Gemini (Tech Lead & Arquiteto)
• Agente Receptor: Kiro (Engenheiro de Software & QA — Construtor Designado)
• Agente Auditor / Homologador: Gemini (Tech Lead & Arquiteto — SoD)
• Módulo / Área: Gestão de Projetos (`gestao_projetos`)
• Tarefa / Passo: Sprint 2 — Passo 2.6: Modernização da Lista Mestra de Relatórios de Atividades
• Branch de Trabalho: `refactor/sprint2-passo2.6-listar-relatorios`
• Arquivos sob Escopo:
  - `gestao_projetos/templates/gestao_projetos/listar_relatorios.html`
  - `gestao_projetos/views.py` (view `listar_relatorios`: `@login_required` e otimização ORM)
• Restrição de Escopo: PROIBIDO alterar models ou outros templates fora do escopo sem autorização prévia.
══════════════════════════════════════════════════════════════════════════════

## 1. Contexto & Objetivos de Negócio

A tela de **Relatórios de Atividades (RA)** (`listar_relatorios.html`) é a interface central onde a equipe de gestão e os coordenadores acompanham a entrega dos RAs dos bolsistas. No ciclo da despesa pública (MCASP / Lei 4.320/64), o Relatório de Atividades com Atesto Técnico SIAPE do Coordenador constitui o **Estágio de Liquidação (Art. 63)**, condição indispensável para a liberação do pagamento.

### Diretrizes Centrais do Passo 2.6:

1. **Padrão Visual Almoxarifado (`.agents/AGENTS.md`):**
   - **Container:** `<div class="container-fluid px-4 mt-4">`.
   - **Breadcrumbs:** Trilha canônica iniciando na raiz:
     `<nav aria-label="breadcrumb">` com `Home` (`{% url 'home_geral' %}`) > `Gestão de Projetos` (`{% url 'gestao_projetos:home_gestao_projetos' %}`) > `Relatórios de Atividades`.
   - **Link Voltar Dinâmico:** Posicionado sob o breadcrumb:
     `<a href="javascript:history.back()" class="text-muted small fw-bold mb-3 d-inline-block text-decoration-none"><i class="fas fa-arrow-left me-1"></i> Voltar</a>`.
   - **Cabeçalho:** Flexbox com Título + Badge de contagem à esquerda, e botões de ação ("Gerar RA", "Limpar Filtros", "Filtros e Ações") alinhados à direita. Subtítulo descritivo: *"Controle de entregas e atesto técnico dos Relatórios de Atividades para liquidação da despesa (Art. 63 da Lei 4.320/64)."*
2. **Ontologia Canônica de Instrumentos Jurídicos:**
   - **Veto ao termo "Convênio":** Substituir o cabeçalho da coluna `Convênio / Projeto` por `Projeto / Termo de Parceria`.
   - No corpo da tabela, referenciar o Termo de Parceria ou o nome do projeto (ex: `relatorio.termo_bolsa.cota_pt.projeto.nome`).
3. **KPIs com Estética Glassmorphism (`FRONTEND_ARCHITECTURE.md`):**
   - Substituir os badges simples do cabeçalho por 3 Cards Glassmorphism (`.cs-card`) no topo:
     * **Card 1 (Total de RAs):** `TOTAL DE RELATÓRIOS` — Volume total na fila/filtrados.
     * **Card 2 (Pendentes / Rascunhos):** `AGUARDANDO ATESTO TÉCNICO (Pendente)` — RAs aguardando liquidação.
     * **Card 3 (Concluídos):** `ESTÁGIO DE LIQUIDAÇÃO CONCLUÍDO (Art. 63)` — RAs atestados e aptos para pagamento.
4. **Tabela Padrão-Ouro & Cabeçalhos Centralizados:**
   - Trocar `<thead class="table-dark">` por `<thead class="table-light">` ou `<thead class="thead-argus">`.
   - **TODAS as tags `<th>` devem ter `text-center`** (inclusive as colunas de Projeto e Bolsista).
   - Manter ações CRUD completas (Visualizar, Editar/Alterar, Baixar DOCX, Excluir).
   - Manter a ausência de `{% empty %}` fundido com colspan no `<tbody>` (compatibilidade DataTables).
5. **Acessibilidade WCAG 2.1 AA:**
   - Adicionar `{% block title %}Relatórios de Atividades - ARGUS{% endblock %}`.
   - Adicionar `aria-label` descritivos em todos os botões de ação, offcanvas e links da tabela.
6. **Backend (`gestao_projetos/views.py`):**
   - Adicionar o decorator `@login_required` na view `listar_relatorios`.
   - Otimizar a queryset com `select_related('termo_bolsa__pessoa', 'parcela_referencia', 'termo_bolsa__cota_pt__projeto')` para eliminar N+1.

---

## 2. Instruções de Execução para o Kiro

1. Certifique-se de estar na branch `refactor/sprint2-passo2.6-listar-relatorios`.
2. Refatore `gestao_projetos/templates/gestao_projetos/listar_relatorios.html` e `gestao_projetos/views.py` aplicando todas as diretrizes acima.
3. Execute `python manage.py check` e `python manage.py test gestao_projetos` para garantir 100% de testes verdes.
4. Emita o **Relatório de Entrega Inbound** preenchendo o template oficial abaixo.

---

## 3. Contrato de Retorno Obrigatório (Inbound)

> **ATENÇÃO (REGRA ANTI-RUBBER-STAMPING):**  
> Você deve preencher os checkboxes `[ ]` e placeholders com base estrita no que foi verificado no seu terminal. Não copie respostas pré-preenchidas.

```text
══════════════════════════════════════════════════════════════════════════════
✅ SQUAD ARGUS — RELATÓRIO DE ENTREGA & AUDITORIA (INBOUND)
══════════════════════════════════════════════════════════════════════════════
• Agente Emissor: Kiro
• Papel Desempenhado: Engenheiro de Software & QA (Construtor Designado)
• Tarefa / Passo Concluído: Sprint 2 — Passo 2.6: Modernização da Lista Mestra de Relatórios de Atividades
• Branch Utilizada: refactor/sprint2-passo2.6-listar-relatorios
• Arquivos Efetivamente Modificados: [lista de arquivos]
• Checklist de Regras Atendidas:
  [ ] Padrão Almoxarifado completo (container-fluid px-4 mt-4, breadcrumb com home_geral)
  [ ] Link Voltar dinâmico padronizado (javascript:history.back()) sob o breadcrumb
  [ ] Veto total ao termo "Convênio" (substituído por Projeto / Termo de Parceria)
  [ ] Cards Glassmorphism (.cs-card) para KPIs do ciclo de liquidação (Art. 63 Lei 4.320/64)
  [ ] Todos os cabeçalhos de tabela centralizados (text-center)
  [ ] CRUD completo de ações preservado (Visualizar, Editar, DOCX, Excluir)
  [ ] Conformidade WCAG 2.1 AA (title e aria-labels)
  [ ] @login_required e otimização ORM aplicados em gestao_projetos/views.py
• Resultados da Validação Local:
  - python manage.py check: [saída exata do seu terminal]
  - python manage.py test gestao_projetos: [saída exata com quantidade de testes e tempo]
══════════════════════════════════════════════════════════════════════════════
```

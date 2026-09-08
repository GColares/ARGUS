# 05 — Design System Canônico do ERP ARGUS

> **Versão:** 1.0  
> **Data:** 05/09/2026  
> **Status:** Oficial / Homologado  
> **Autores:** Antigravity-Gemini (Tech Lead) & IBM Bob (SDLC Partner) / Aprovado por: Geziel (PO)

---

## 1. Filosofia e Identidade Visual

O ERP ARGUS adota o **Padrão Almoxarifado / Corporate Modern**: uma interface pensada para governança pública, auditoria e operações de alta complexidade em Ciência, Tecnologia e Inovação (ICT / IFAM).

### Pilares Fundamentais:
1. **Clareza Informacional:** A interface deve valorizar a densidade de dados sem gerar sobrecarga cognitiva. Menos ruído visual, mais legibilidade.
2. **Cores Semânticas Estritas:** Cada cor carrega um significado unívoco em todos os módulos (ex: status pendente nunca pode ser vermelho).
3. **Consistência de Componentes:** Cards de KPI, tabelas DataTables, modais e formulários compartilham o mesmo DNA estrutural em `almoxarifado`, `cadastros`, `gestao_projetos` e `central_servicos`.
4. **Desempenho e Acessibilidade:** Estilos centralizados no CSS global (`style.css`), sem estilos inline (`style="..."`), com contraste adequado (WCAG AA) e suporte total a navegação fluida.

---

## 2. Paleta de Cores e Tokens Semânticos

O ARGUS utiliza uma arquitetura híbrida de tokens que sobrescreve nativamente o Bootstrap 5.3:

```css
:root {
    /* Identidade Primária ARGUS (Software Identity) */
    --argus-azul: #0D3B66;          /* Primária: Ações estruturais, headers, links */
    --argus-teal: #1AA3A8;          /* Secundária/Acento: Destaques, badges de fluxo */
    
    /* Identidade Institucional INOVA (IFAM) */
    --inova-verde: #7EC247;         /* Sucesso: Conclusões, pagamentos, aprovações */
    --inova-vermelho: #B72D25;      /* Perigo/Crítico: Cancelamentos, expurgos, rejeições */
    --inova-ouro: #D48806;          /* Alerta/Pendente: Atenção, aguardando ação, rascunhos */
    --inova-grafite: #1A1A1A;       /* Texto base de alta legibilidade */
    --inova-cinza-claro: #F1F1F2;   /* Fundos sutis e divisores */
    
    /* Superfícies e Elevações Corporativas */
    --argus-bg-app: #f8fafc;        /* Fundo global da aplicação (Slate 50) */
    --argus-card-bg: #ffffff;       /* Fundo de cards e modais */
    --argus-card-border: #e2e8f0;   /* Bordas sutis de cards e tabelas (Slate 200) */
    --argus-header-bg: #1e293b;     /* Cabeçalhos escuros de tabelas e KPIs (Slate 800) */
}
```

---

## 3. Matriz Canônica de Badges de Status (Regra Mandatória)

Fica terminantemente vedada a criação de cores arbitrárias para status em templates. Todos os módulos devem seguir rigorosamente esta tabela:

| Categoria Semântica | Status de Negócio (Exemplos) | Classe CSS | Cor de Fundo | Cor do Texto |
|---|---|---|---|---|
| **Sucesso / Regular** | `ATIVO`, `HOMOLOGADO`, `CONCLUÍDO`, `PAGO`, `EFETIVADO` | `.badge-status-success` | `#dcfce7` (Verde 100) | `#15803d` (Verde 700) |
| **Alerta / Aguardando** | `PENDENTE`, `EM ANÁLISE`, `EM ANDAMENTO`, `RASCUNHO`, `AGUARDANDO ATESTO` | `.badge-status-warning` | `#fef3c7` (Âmbar 100) | `#b45309` (Âmbar 700) |
| **Crítico / Interrompido** | `CANCELADO`, `REJEITADO`, `VENCIDO`, `EXCLUÍDO`, `GLOSADO` | `.badge-status-danger` | `#fee2e2` (Vermelho 100) | `#b91c1c` (Vermelho 700) |
| **Neutro / Arquivado** | `CONGELADO`, `SUSPENSO`, `INATIVO`, `SUBSTITUÍDO` | `.badge-status-secondary` | `#f1f5f9` (Slate 100) | `#475569` (Slate 600) |
| **Informativo / Inicial** | `PROSPECÇÃO`, `PLANEJADO`, `ANONIMIZADO LGPD` | `.badge-status-info` | `#e0f2fe` (Ciano 100) | `#0369a1` (Ciano 700) |

---

## 4. Tipografia e Hierarquia Visual

- **Família Tipográfica Oficial:** `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`.
- **Títulos de Telas:** O título principal de cada view deve ser formatado como `<h4>` com classe `fw-bold text-dark mb-0` (nunca `<h2>`, para manter a escala executiva).
- **Subtítulos e Descrições:** `<p class="text-muted small mb-0">`.
- **Labels de Formulário:** `<label class="form-label small fw-bold text-secondary">`.

---

## 5. Ícones Oficiais: Biblioteca Canônica

- **Padrão Exclusivo:** **FontAwesome 6 Free** (`fas fa-*` para sólidos, `far fa-*` para regulares).
- **Proibição:** É vedado o uso de **Bootstrap Icons (`bi bi-*`)**. Qualquer ocorrência legada em `gestao_projetos` ou `patrimonio` deve ser migrada para o equivalente FontAwesome.
- **Tabela de Correspondência Comum:**
  * Visualizar / Detalhes: `<i class="fas fa-eye"></i>`
  * Editar: `<i class="fas fa-edit"></i>`
  * Excluir / Lixeira: `<i class="fas fa-trash-alt"></i>`
  * Novo / Adicionar: `<i class="fas fa-plus-circle"></i>`
  * Voltar: `<i class="fas fa-arrow-left"></i>`
  * Filtros: `<i class="fas fa-filter"></i>`
  * Financeiro / Cifrão: `<i class="fas fa-hand-holding-usd"></i>` ou `<i class="fas fa-dollar-sign"></i>`
  * Relatórios / PDFs: `<i class="fas fa-file-pdf"></i>` ou `<i class="fas fa-chart-line"></i>`

---

## 6. Componentes Canônicos

### A. Estrutura de Página (Layout Master)
Todo template de listagem ou formulário deve iniciar com a estrutura:
```html
{% extends 'base.html' %}
{% load static %}

{% block content %}
<div class="container-fluid px-4 mt-4">
    <!-- 1. Breadcrumb -->
    <nav aria-label="breadcrumb">
        <ol class="breadcrumb mb-2"> ... </ol>
    </nav>
    
    <!-- 2. Header de Ações -->
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h4 class="fw-bold mb-0 text-dark">Título da Funcionalidade</h4>
            <p class="text-muted small mb-0">Descrição objetiva do contexto.</p>
        </div>
        <div class="d-flex gap-2">
            <!-- Botões de Ação Global -->
        </div>
    </div>
    
    <!-- 3. Conteúdo (KPIs, Filtros, Tabelas) -->
</div>
{% endblock %}
```

### B. Cards de KPI (Métricas Executivas)
Substitui definições locais por classe padronizada:
```html
<div class="col-md-3">
    <div class="card card-kpi-argus border-0 shadow-sm h-100">
        <div class="card-body p-3 d-flex align-items-center">
            <div class="icon-shape bg-primary-subtle text-primary rounded-3 p-3 me-3">
                <i class="fas fa-wallet fa-lg"></i>
            </div>
            <div>
                <span class="text-muted small fw-bold text-uppercase">Total Aportado</span>
                <h4 class="fw-bold mb-0 text-dark">R$ 150.000,00</h4>
            </div>
        </div>
    </div>
</div>
```

### C. Tabelas e DataTables (Padrão Almoxarifado)
- **Regra Inegociável:** **JAMAIS** utilizar `{% empty %}` dentro do loop de um `<tbody>` que inicializa o DataTables (o DataTables gerencia nativamente a linha de "Nenhum registro encontrado").
- **Cabeçalho:** Fundo Slate escuro (`table-dark` ou classe personalizada `.thead-argus`).
- **Alinhamento:**
  * Textos e descrições: alinhados à esquerda (`text-start`).
  * Códigos, datas e badges: centralizados (`text-center`).
  * Valores monetários e quantitativos: alinhados à direita (`text-end font-monospace`).
  * Coluna de Ações: centralizada ou à direita, com largura fixa (`width: 120px;`).

### D. Botões de Ação
- **Criar / Novo:** `<button class="btn btn-primary fw-bold"><i class="fas fa-plus-circle me-1"></i> Novo</button>`
- **Editar:** `<a class="btn btn-sm btn-outline-primary" title="Editar"><i class="fas fa-edit"></i></a>`
- **Excluir:** `<a class="btn btn-sm btn-outline-danger" title="Excluir"><i class="fas fa-trash-alt"></i></a>`
- **Voltar:** `<a href="javascript:history.back()" class="btn btn-outline-secondary"><i class="fas fa-arrow-left me-1"></i> Voltar</a>`

---

## 7. Padrão Glassmorphism (Cards & Painéis Premium)

Para manter coerência com o Dashboard (`home_geral.html`), painéis e formulários complexos devem utilizar:
- **Classe canônica:** `.cs-card` ou `.glass-card`.
- **Fundo:** `rgba(255, 255, 255, 0.85)` com `backdrop-filter: blur(10px)`.
- **Borda:** `1px solid rgba(var(--bs-primary-rgb), 0.12)`.
- **Sombra:** `box-shadow: 0 0.5rem 1.5rem rgba(var(--bs-dark-rgb), 0.08)`.
- **Fallback:** `@supports not (backdrop-filter: blur(10px))` deve aplicar `background: #ffffff`.

## 8. Regra Anti-Trava (Layouts Fluidos)

- Formulários extensos devem sempre utilizar `.container-fluid.px-4.mt-4`.
- É estritamente proibido aplicar `height: 100vh` ou `overflow: hidden` no `body` ou contêineres principais de formulários.
- Ações globais (Salvar, Avançar, Voltar) devem utilizar `.sticky-actions-bar`.

## 9. Proibições Absolutas de Frontend

1. 🚫 **Estilos Inline (`style="..."`):** Todo estilo deve estar encapsulado em classes utilitárias no `style.css` e no design system centralizado `argus-design-system.css`.
2. 🚫 **Eventos de Estilo Inline (`onmouseover`, `onmouseout`):** Animações de hover devem ser exclusivamente via CSS (`:hover`, `transform: translateY(-2px)`).
3. 🚫 **`{% empty %}` em DataTables:** Viola o ciclo de vida do plugin e quebra paginação.
4. 🚫 **Cores Hexadecimais Hardcoded em Templates:** Sempre usar variáveis CSS `--argus-*`, classes Bootstrap ou classes semânticas de status.
5. 🚫 **Travas de viewport no wizard:** `body`, `html`, `#v-pills-tab`, `.custom-scrollbar` e `height: calc(100vh - ...)` não podem impedir scroll natural do navegador.

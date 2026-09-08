# Manual de Arquitetura Front-End do ARGUS: Padrão-Ouro Adaptado
**Versão:** 2.0.0  
**Data de Vigência:** 2026-09-07  
**Autor:** Antigravity / Tech Lead Arquiteto  
**Homologação:** Squad IA (Gemini, Copilot, DeepSeek-v4-pro, Claude Sonnet 5) & PO Geziel  
**Status:** Norma Canônica de Interface e Acessibilidade (Obrigatória)

---

## 📜 Histórico de Controle de Versão (Changelog)

| Versão | Data | Autor | Descrição das Alterações |
| :--- | :--- | :--- | :--- |
| **1.0.0** | 2026-08-15 | Squad Frontend | Padronização inicial de listagens (Padrão Almoxarifado) no `05_DESIGN_SYSTEM_ARGUS.md`. |
| **2.0.0** | 2026-09-07 | Antigravity & DeepSeek | Versão enciclopédica canônica: BEM Híbrido, Glassmorphism, WCAG 2.1 AA, extinção da Trava de Caixa Eletrônico e Diretivas Propositivas para IAs. |

---

## ⚖️ Matriz de Correspondência: Teoria Genérica (X) vs. Realidade ARGUS (Y)

| Dimensão | Padrão Teórico Acadêmico (X) | Padrão Institucional ARGUS (Y) |
| :--- | :--- | :--- |
| **Framework Base** | CSS puro do zero, sem frameworks utilitários. | **Bootstrap 5.3+ obrigatório** (`container-fluid`, grid flex, utilitários de espaçamento e flexbox). |
| **Metodologia de Classes** | BEM estrito para 100% dos elementos da página. | **BEM Híbrido:** Utilitários do Bootstrap para grid/espaçamento + BEM estrito **apenas** para componentes proprietários (`.cs-card`, `.wizard-step`). |
| **Bibliotecas de Terceiros** | Proibidas ou banidas se não aderirem a BEM puro. | **Convivência Oficial:** DataTables, Select2 e Quill JS são integrados nativamente com estilizações de casca sem quebrar seus markups internos. |
| **Direção Responsiva** | *Mobile-First* estrito (`min-width` cego). | **Desktop-First Enterprise:** Otimizado para telas de alta densidade (pesquisadores/auditores em monitores de trabalho), com adaptação degradativa para tablets/mobile. |
| **Unidades de Medida** | Proibição dogmática e absoluta de pixels (`px`). | **Rem/Em para tipografia e padding**, mas **Pixels (`px`) expressamente permitidos para bordas finas (1px, 2px)** para evitar borrões de subpixel. |
| **Identidade Visual** | Minimalismo plano (Flat Design puro). | **Glassmorphism Corporativo:** Fundos translúcidos (`rgba(255,255,255,0.85)`), `backdrop-filter: blur(10px)` e sombras suaves (`.cs-card`). |
| **Navegação Histórica** | Links comuns com URLs relativas (`href="/..."`). | **Voltar Inteligente Dinâmico:** Sempre `<a href="javascript:history.back()">` para manter filtros de busca e paginação do usuário. |
| **Alertas & Validação** | Divs estáticas no meio do DOM empurrando a página. | **Zero Inline Warnings no fluxo:** Uso de Toasts do Bootstrap (`django.contrib.messages`) para manter o layout estável. |

---

## 1. Fundamentos e Filosofia Arquitetural

O desenvolvimento front-end no ecossistema ARGUS baseia-se na união da **Separação Estrita de Conceitos (SoC)** com a **Produtividade de Frameworks Industriais**:

* **HTML5 / Django Templates:** Camada estrita de dados, semântica estrutural e orquestração de blocos via `{% include %}`. É terminantemente proibido o uso de tags estruturais para fins visuais cosméticos.
* **Bootstrap 5.3 Utilities:** Responsável pela topologia da página, grid, espaçamentos (`m-*`, `p-*`), alinhamentos (`d-flex`, `justify-content-*`) e display responsivo.
* **CSS3 Centralizado (`argus-design-system.css`):** Responsável pelos tokens de Glassmorphism, componentes complexos proprietários, animações de microinteração e estados visuais. **Zero `<style>` inline em templates.**

---

## 2. Semântica Estrutural e Landmarks (HTML5)

Todo documento renderizado no ARGUS deve respeitar os landmarks da especificação W3C/WHATWG:

### 2.1 Estrutura de Documentos e Modais
```html
<header class="navbar navbar-expand-lg ...">
  <nav aria-label="Navegação Principal do Módulo">
    <!-- Breadcrumbs e Identificação do Sistema -->
  </nav>
</header>

<main class="container-fluid px-4 mt-4">
  <!-- Topo: Título + Badge + Ações Globais -->
  <section aria-labelledby="page-title">
    <h1 id="page-title" class="h3 fw-bold ...">Título da Tela</h1>
  </section>

  <!-- Conteúdo Principal / Cards / DataTables -->
  <article class="cs-card p-4">
    <!-- Formulário ou Lista de Registros -->
  </article>
</main>
```

### 2.2 Distinção Rigorosa de Elementos Interativos
* **Tag `<a>`:** Usada **exclusivamente** quando houver mudança de URL ou navegação de âncora.
  - *Regra de Voltar:* `<a href="javascript:history.back()" class="text-muted small fw-bold mb-2 d-inline-block"><i class="fas fa-arrow-left me-1"></i> Voltar</a>`.
* **Tag `<button>`:** Usada para qualquer gatilho acionado por JavaScript, submissão de formulário (`type="submit"`), abertura de modais (`data-bs-toggle="modal"`) ou avanço de passos de wizard.
* **Proibição Absoluta:** Proibido atribuir eventos de clique (`onclick`) em `<div>`, `<span>` ou `<li>` sem teclado e ARIA.

### 2.3 Hierarquia Linear de Títulos
A ordem dos cabeçalhos textuais deve seguir progressão linear estrita (`<h1>` → `<h2>` → `<h3>`). É proibido saltar níveis (ex: `<h1>` direto para `<h4>`) para simular tamanho visual — utilize classes do Bootstrap como `.h4`, `.h5` ou `.small`.

---

## 3. Metodologia CSS: BEM Híbrido e Tokens Canônicos

Para evitar colisão de classes com o Bootstrap 5, o ARGUS adota o **BEM Híbrido**:

### 3.1 Quando usar Bootstrap vs. Quando usar BEM
* **Use Bootstrap:** Para grid, containers, margens, paddings, alinhamentos e cores utilitárias básicas (`container-fluid`, `row`, `col-md-6`, `mb-3`, `text-center`).
* **Use BEM:** Para componentes proprietários complexos criados pelo ARGUS:
  - *Bloco:* `.cs-card`, `.wizard-step`, `.kpi-badge`
  - *Elemento:* `.cs-card__header`, `.wizard-step__content`, `.kpi-badge__icon`
  - *Modificador:* `.cs-card--featured`, `.wizard-step--active`, `.kpi-badge--warning`

### 3.2 Tokens de Glassmorphism Canônico (`static/css/argus-design-system.css`)
Todo card de conteúdo no ARGUS deve herdar os tokens canônicos:
```css
.cs-card, .glass-card {
    background: rgba(255, 255, 255, 0.85);
    border: 1px solid rgba(var(--bs-primary-rgb), 0.12);
    border-radius: 0.75rem;
    box-shadow: 0 0.5rem 1.5rem rgba(var(--bs-dark-rgb), 0.06);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

/* Fallback para navegadores sem suporte a blur */
@supports not ((-webkit-backdrop-filter: blur(10px)) or (backdrop-filter: blur(10px))) {
    .cs-card, .glass-card {
        background: #ffffff;
    }
}
```

### 3.3 Gestão de Seletores
* **Proibição de Seletores de ID no CSS:** IDs como `#meu-form` são exclusivos para ancoragem no DOM e seletores JavaScript. Nunca estilize via `#id` em código novo.
* **Proibição de `!important`:** Permitido unicamente em classes utilitárias globais de acessibilidade (ex: `.visually-hidden`).

---

## 4. Integração com Ecossistema de Terceiros (DataTables, Select2, Quill)

Componentes industriais já consolidados possuem regras específicas de coexistência:

1. **DataTables (JavaScript):**
   - **Proibição Absoluta:** É estritamente proibido usar `{% empty %}` com `<td colspan="...">` dentro do `<tbody>` de tabelas processadas por DataTables. O `<tbody>` deve ser entregue vazio para o DataTables renderizar a mensagem nativa.
   - **Alinhamento:** Cabeçalhos `<th>` e colunas de Ações devem ser centralizados (`class="text-center"`).
2. **Select2 (Global):**
   - Todo `<select>` deve receber a classe `.form-select`. A inicialização do Select2 é feita de forma única no `base.html`. Proibido reinicializar scripts do Select2 em templates filhos.
3. **Quill (Rich Text):**
   - Editores de texto rico devem usar a classe `.ql-editor-fluid` (`min-height: 160px; height: auto;`). Proibido travar altura fixa rígida que gere barras duplas de rolagem.

---

## 5. Responsividade, Ergonomia e Unidades

### 5.1 Desktop-First Enterprise
O ARGUS atende primariamente a analistas em estações de trabalho desktop com alta densidade de dados:
* Os formulários e dashboards devem priorizar conforto horizontal com `.container-fluid.px-4.mt-4`.
* A adaptação para telas menores ocorre por colapso vertical gracioso via classes responsivas do Bootstrap (`col-12 col-lg-6`).

### 5.2 Regra Anti-Trava (Proibição da "Trava de Caixa Eletrônico")
* **PROIBIDO:** `height: 100vh`, `overflow: hidden` ou `calc(100vh - ...)` aplicados ao `body`, `html` ou contêineres mestre de formulários.
* **PERMITIDO:** `overflow: hidden` associado a `text-overflow: ellipsis` exclusivamente para truncar células de tabelas com nomes longos.
* **Barra de Ações Fixa (Sticky Actions):** Em formulários longos, os botões "Avançar", "Voltar" e "Salvar" devem ser envelopados na classe `.sticky-actions-bar`.

### 5.3 Regra de Unidades: Onde usar `rem`, `em` e `px`
* `rem`: Tipografia global, espaçamentos maiores e margens estruturais.
* `em`: Espaçamentos internos dependentes do tamanho da fonte do próprio componente.
* `px`: **Permitido estritamente para espessura de bordas (1px, 2px)** e sombras de micro-precisão geométrica.

---

## 6. Acessibilidade (WCAG 2.1 Nível AA & eMAG)

1. **Contraste Cromático:** Texto regular deve possuir contraste mínimo de **4.5:1** contra o fundo translúcido do card.
2. **Foco Visível:** Proibido `outline: none;` sem `:focus-visible`. Todo input e botão focado deve exibir o halo luminoso padrão do Bootstrap / ARGUS.
3. **Leitores de Tela:** Elementos de contexto auditivo exclusivo devem usar a classe utilitária `.visually-hidden`.

---

## 7. Diretrizes de Execução para Agentes de IA (Squad SoD)

1. **Auditoria Preventiva & Propositiva (Anti-Paralisia):** Ao lidar com código legado contendo estilos inline antigos, a IA **não deve travar** a execução. Ela deve realizar a tarefa de negócio solicitada e **propor ativamente** a migração dos estilos inline para classes do `argus-design-system.css`.
2. **Fatiamento Modular Obrigatório:** Qualquer template HTML que ultrapassar **500 linhas** deve ser fatiado imediatamente em fragmentos modulares chamados via `{% include %}` dentro de uma subpasta correspondente (ex: `projetos_steps/`).
3. **CRUD Completo e Seguro:** Toda tabela de listagem deve prover no mínimo as ações de Visualizar, Editar e Excluir, com fluxo de confirmação seguro (`confirm_delete`).

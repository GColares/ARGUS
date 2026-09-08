# Handoff de Implementação: Revolução UI/UX do Wizard de Projetos & Design System

**Destinatário:** GitHub Copilot / Agente de Frontend (IBM Bob)  
**Autor:** Antigravity / Tech Lead Arquiteto (Consolidado com Red Team do DeepSeek-v4-pro e Claude Sonnet 5)  
**Status da Suíte Atual:** 207/207 Testes Verdes (Baseline Intacto)  

---

## 1. Contexto & Diagnóstico
O template `cadastros/templates/cadastros/form_projeto.html` é um monólito de **102 KB** com **17 etapas/abas** e uma trava artificial de layout (*Trava de Caixa Eletrônico*):
- Estilos inline impondo `html, body { height: 100% }`, `overflow-x: hidden`, e contêineres `#v-pills-tab` e `.custom-scrollbar` com `height: calc(100vh - 290px); overflow-y: auto`.
- Editores Quill com altura travada em 150px criando múltiplas barras de rolagem concorrentes.
- A classe `.cs-card` e estilos de *Glassmorphism* estão dispersos em vários arquivos sem uma fonte canônica centralizada.

Este handoff detalha a execução segura da **Fase 1 e Fase 2** da Master RFC, blindada pelas ressalvas do Red Team.

---

## 2. Regras Não-Negociáveis (Filtros Red Team)

1. **Diferenciação Crítica de `overflow: hidden`:**
   - **PROIBIDO:** Travas de altura/viewport no `body`, `html`, `#v-pills-tab`, `.custom-scrollbar` e `height: 100vh` ou `calc(100vh - ...)`.
   - **PERMITIDO & PRESERVADO:** `overflow: hidden` com `text-overflow: ellipsis` e `white-space: nowrap` utilizado para truncar textos em células de tabelas e badges. **NÃO REMOVER.**
2. **Preservação Rígida de Contratos HTML/JS:**
   - **NENHUM** `id`, `name`, `data-bs-*` ou atributo de formulário dos inputs/selects deve ser alterado.
   - O bloco de JavaScript de orquestração do Wizard (linhas 1482 a 1791 do `form_projeto.html`) deve ser mantido **100% funcional**, preservando as funções de avanço, retorno, cálculo e sincronização do Quill.
3. **Fatiamento 1-para-1 (Sem Fusão de Abas):**
   - As 17 etapas (`step1` a `step17`) devem ser fatiadas estritamente em **17 fragmentos HTML** em `cadastros/templates/cadastros/projetos_steps/`. O arquivo `form_projeto.html` será apenas o orquestrador que inclui cada pedaço via `{% include %}`.
4. **Fonte Única de CSS:**
   - Zero blocos `<style>` inline novos. Todo o Glassmorphism e estilos de barra sticky devem residir em `static/css/argus-design-system.css`.

---

## 3. Roteiro Passo a Passo de Implementação

### Passo 0: Atualizar Documentação de Governança (`documentacao-tecnica/05_DESIGN_SYSTEM_ARGUS.md`)
Adicionar a seção oficial do **Padrão Glassmorphism & Layouts Fluidos**:
```markdown
## 7. Padrão Glassmorphism (Cards & Painéis Premium)
Para manter coerência com o Dashboard (`home_geral.html`), painéis e formulários complexos devem utilizar:
- **Classe Canônica:** `.cs-card` ou `.glass-card`.
- **Fundo:** `rgba(255, 255, 255, 0.85)` com `backdrop-filter: blur(10px)`.
- **Borda:** `1px solid rgba(var(--bs-primary-rgb), 0.12)`.
- **Sombra:** `box-shadow: 0 0.5rem 1.5rem rgba(var(--bs-dark-rgb), 0.08)`.
- **Fallback:** `@supports not (backdrop-filter: blur(10px))` deve aplicar `background: #ffffff`.

## 8. Regra Anti-Trava (Layouts Fluidos)
- Formulários extensos devem sempre utilizar `.container-fluid.px-4.mt-4`.
- É estritamente proibido aplicar `height: 100vh` ou `overflow: hidden` no `body` ou contêineres principais de formulários.
- Ações globais (Salvar, Avançar, Voltar) devem utilizar `.sticky-actions-bar`.
```

---

### Passo 1: Criar o CSS Canônico e Vincular no `base.html`
1. Criar o arquivo `static/css/argus-design-system.css`:
```css
/* ARGUS Design System - Tokens Canônicos */
.cs-card, .glass-card {
    background: rgba(255, 255, 255, 0.85);
    border: 1px solid rgba(var(--bs-primary-rgb), 0.12);
    border-radius: 0.75rem;
    box-shadow: 0 0.5rem 1.5rem rgba(var(--bs-dark-rgb), 0.06);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

@supports not ((-webkit-backdrop-filter: blur(10px)) or (backdrop-filter: blur(10px))) {
    .cs-card, .glass-card {
        background: #ffffff;
    }
}

/* Barra de Ações Sticky para Wizards e Formulários Longos */
.sticky-actions-bar {
    position: sticky;
    bottom: 0;
    z-index: 1020;
    background: rgba(255, 255, 255, 0.92);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border-top: 1px solid rgba(0, 0, 0, 0.08);
    padding: 0.85rem 1.5rem;
    box-shadow: 0 -0.25rem 1rem rgba(0, 0, 0, 0.04);
}

/* Editor Quill Fluido */
.ql-editor-fluid {
    min-height: 160px;
    height: auto;
    font-size: 0.95rem;
}
```
2. No arquivo `templates/base.html`, incluir a tag `<link rel="stylesheet" href="{% static 'css/argus-design-system.css' %}">` logo após o CSS principal.

---

### Passo 2: Fatiamento de `cadastros/templates/cadastros/form_projeto.html`
1. Criar a pasta: `cadastros/templates/cadastros/projetos_steps/`
2. Extrair os conteúdos dos passos `step1` a `step17` para arquivos dedicados:
   - `_step_01_dados_gerais.html`
   - `_step_02_empresa_termo.html`
   - `_step_03_plano_trabalho.html`
   - `_step_04_coordenacao.html`
   - `_step_05_equipe.html`
   - `_step_06_metodologia.html`
   - `_step_07_cronograma_macro.html`
   - `_step_08_atividades.html`
   - `_step_09_rubricas.html`
   - `_step_10_desembolso.html`
   - `_step_11_contrapartidas.html`
   - `_step_12_contas_bancarias.html`
   - `_step_13_metas_indicadores.html`
   - `_step_14_riscos.html`
   - `_step_15_anexos.html`
   - `_step_16_revisao.html`
   - `_step_17_conclusao.html`
   *(Mapear os blocos exatos existentes dentro de cada `<div class="tab-pane ..." id="stepX">`)*
3. No arquivo mestre `form_projeto.html`:
   - Remover as regras de trava inline (`html, body { height: 100% }`, `overflow: hidden`, `calc(100vh - 290px)`).
   - Aplicar `.cs-card` no sidebar de navegação lateral (`#v-pills-tab`) e no contêiner principal das abas.
   - Deixar o sidebar com `position: sticky; top: 1rem;` para acompanhar o scroll natural da página sem travar o body.
   - Renderizar o conteúdo de cada passo chamando:
     ```html
     <div class="tab-content" id="v-pills-tabContent">
         <div class="tab-pane fade show active" id="step1" role="tabpanel">
             {% include 'cadastros/projetos_steps/_step_01_dados_gerais.html' %}
         </div>
         ...
         <div class="tab-pane fade" id="step17" role="tabpanel">
             {% include 'cadastros/projetos_steps/_step_17_conclusao.html' %}
         </div>
     </div>
     ```
   - Aplicar a classe `.sticky-actions-bar` no rodapé dos botões ("Avançar", "Voltar", "Salvar Rascunho").
   - Manter intacto o bloco `<script>` final de navegação.

---

### Passo 3: Auditoria Pontual de `DateInput` em Formulários
No arquivo `central_servicos/forms.py` (ou onde residirem `avcb_validade` e `licenca_ambiental_validade`), assegurar o formato ISO:
```python
forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'})
```

---

## 4. Critérios de Aceite & Homologação

Ao terminar, o executor deve rodar no terminal:
1. `python manage.py check` (Sem erros de sistema ou imports).
2. `python manage.py test` (Garantir **207/207 testes verdes**).
3. **Verificação Visual no Navegador:**
   - Acessar a tela de cadastro de Projeto (`/cadastros/projetos/novo/` ou `/cadastros/projeto/novo/`).
   - Confirmar que a barra de rolagem do navegador funciona livremente (sem travas forçadas de tela inteira).
   - O menu de passos lateral acompanha a visualização ou rola organicamente.
   - Os editores Quill expandem conforme o texto é digitado.
   - Clicar em "Avançar" e "Voltar" transiciona suavemente entre as 17 etapas via JavaScript.
   - Salvar o formulário persiste os dados corretamente no banco.

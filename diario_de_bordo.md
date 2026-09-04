# Diário de Bordo — ARGUS

## [2026-09-03] Encerramento do Expediente: Estabilização de UX, Quill e Rodapé do Wizard de Projetos

### 1. Resumo do Trabalho Realizado na Sessão
- **Onda 1 de Higiene Técnica (Devin):** Concluída com sucesso — eliminação de 159 linhas duplicadas em `cadastros/views.py` e correção do import canônico de `ValidationError`.
- **Governança do Squad:** Protocolo consolidado (`PROTOCOLO_COLABORACAO_IA.md`, `COPILOT.md`, `DEVIN.md`), unificação de UTF-8 e adição de diretrizes de seleção de modelo (Flash vs Pro) em `GEMINI.md`.
- **Editor RichText (Quill):**
  - Eliminação de modais e sanfonas instáveis em favor do padrão de **Edição Inline Sob Demanda** (toolbar aparece no topo da caixa apenas ao clicar em "Editar").
  - Restauração da capacidade de posicionar **2 ou mais imagens lado a lado na mesma linha** (remoção do `display: block` restritivo e aplicação de `display: inline-block !important; vertical-align: middle; margin: 0.25rem;`).
  - Inclusão do seletor de alinhamento (`[{ 'align': [] }]`) na barra de ferramentas.
- **Micro-Layout e Geometria do Wizard (`form_projeto.html`):**
  - Implementação de rodapé aderente (`position: sticky; bottom: 0;`) para a barra de navegação, mantendo os botões "Voltar" e "Próximo" permanentemente visíveis em todos os 17 passos.
  - Alinhamento milimétrico da base dos botões a exatamente **0,5 cm (~19 px)** acima da linha inferior do quadro branco.
  - Ajuste ergonômico no Passo 4 (Motivação): eliminação do vão residual de 1 cm (remoção do padding-bottom de 1.5rem da row e margens) e expansão da caixa de texto até parar a exatos **0,2 cm (~8,5 px)** da linha superior do rodapé.

### 2. Lista Ostensiva de Alterações de Interface / HTML na Sessão
- **Arquivo Modificado:** `cadastros/templates/cadastros/form_projeto.html`
- **Regras CSS Adicionadas / Alteradas (`<style>`):**
  - `.ql-editor img`: alterado de `display: block; margin: 1rem auto;` para `max-width: 100%; height: auto; display: inline-block !important; vertical-align: middle; margin: 0.25rem; border-radius: 0.375rem;`.
  - `.wizard-content-panel`: adicionado `padding-bottom: 0 !important;`.
  - `.wizard-step.active`: adicionado `padding-bottom: 0 !important;`.
  - `.wizard-step > .border-top`: configurado como `position: sticky !important; bottom: 0 !important; background-color: #ffffff !important; z-index: 1050 !important; margin-top: auto !important; padding-top: 0.85rem !important; padding-bottom: 0.5cm !important; margin-bottom: 0 !important; border-top: 1px solid #dee2e6 !important; box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.05) !important;`.
  - `#step4 .richtext-editor-container, #step4 .ql-container, #step4 .ql-editor`: `max-height: calc(100vh - 418px) !important;`.
  - `#step4 > .row, #step4 > .row.g-4`: `padding-bottom: 0 !important; margin-bottom: 0.2cm !important; --bs-gutter-y: 0 !important;`.
  - `#step4 > .row > .col-md-12, #step4 .richtext-wrapper`: `padding-bottom: 0 !important; margin-bottom: 0 !important;`.
- **Scripts JavaScript Alterados (`<script>`):**
  - Inclusão do módulo de alinhamento em `toolbarOptions`: `[{ 'align': [] }]`.
  - Captura e ocultação inicial da toolbar via `quill.getModule('toolbar').container`.
  - Evento de clique no botão `editBtn`: alterna classe `.is-editing`, aciona `quill.enable(true/false)`, exibe/oculta a toolbar e sincroniza o textarea chamando `autoSave()`.
  - Remoção de código legado de modais (`#richtext-edit-modal`, `#richtext-read-modal`) e classes de preview.

### 3. Fila de Continuidade para Amanhã
1. **Onda 2:** Vinculação formal `User` ↔ `PessoaFisica` (OneToOne) e alinhamento do decorator de permissão SIAPE.
2. **Onda 3:** Testes automatizados de invariantes financeiras (EMBRAPII e SUFRAMA — travas de percentuais e rubricas).
3. **Onda 4:** Planejamento arquitetural para decomposição e modularização do app `cadastros` e consolidação de grupos de RBAC.

---

## [2026-09-03] Ajuste Direto Gemini: Eliminação do Vazio de 1 cm e Calibração dos 0,2 cm no Passo 4

Inversão declarada:
- A pedido do usuário para eliminar o gap de 1 cm visível a 100% de tela e cravar a expansão da textbox a 0,2 cm do rodapé, o Gemini investigou o box model e aplicou as correções no CSS de `cadastros/templates/cadastros/form_projeto.html`.

Causas identificadas e eliminadas:
1. `padding-bottom: 1.5rem` (24px / 0,63cm) em `.wizard-step > .row` — removido exclusivamente para o `#step4`.
2. `margin-bottom` residual em `.col-md-12` e `.richtext-wrapper` — zerados no `#step4`.
3. `max-height` recalibrado para `calc(100vh - 418px)` — considerando a área útil real do navegador com interface desktop (940px de altura útil em 1080p).

Verificação:
- Teste com Playwright na viewport real de desktop (940px) comprovou a distância exata de 8.5px (~0,22 cm) entre a borda inferior da textbox e a linha do rodapé dos botões, preenchendo o vazio de 1 cm anterior com perfeita nitidez visual.

---

## [2026-09-03] Ajuste Direto Gemini: Altura dos Botões 'Próximo' e 'Voltar' a 0,5 cm do Quadro Branco

Inversão declarada:
- A pedido expresso do usuário ("ajuste a altura do botão PROXIMO e VOLTAR para 0,5 cm acima da linha do quadro branco"), o Gemini aplicou o ajuste de micro-layout diretamente no CSS de `cadastros/templates/cadastros/form_projeto.html`.

Alterações realizadas:
1. `.wizard-content-panel`: adicionado `padding-bottom: 0 !important;` para alinhar o término da área rolável com a borda inferior do card.
2. `.wizard-step.active`: ajustado `padding-bottom: 0 !important;`.
3. `.wizard-step > .border-top`: definido `padding-bottom: 0.5cm !important;` e `bottom: 0 !important;`, posicionando o limite inferior dos botões a exatamente 0,5 cm (~19px) da linha inferior do quadro branco.

Verificação:
- Medição via Playwright no Passo 1 e Passo 2 confirmou distância exata de ~19.8px (~0,5 cm) da base dos botões à borda inferior do painel, com altura perfeitamente nivelada e sincronizada.

---

## [2026-09-03] Handoff Gemini → Copilot: Rodapé Fixo de Navegação (Sticky) e Trava Ergonômica da Textbox (48vh)

Objetivo:
Implementar a arquitetura híbrida de visualização no Wizard do Projeto (`cadastros/templates/cadastros/form_projeto.html`):
1. Fixar a barra de navegação dos botões 'Voltar' e 'Próximo' como rodapé aderente (`position: sticky; bottom: 0;`), garantindo que os botões fiquem sempre visíveis e estáveis na base da tela em todos os 17 passos, mesmo quando o conteúdo rolar.
2. Limitar a expansão máxima da caixa de texto rica (Quill) a 48% da altura da tela (`max-height: 48vh; overflow-y: auto;`), permitindo abertura natural para textos curtos/médios, mas ativando rolagem interna suave quando o texto ou fotos forem muito extensos.

Escopo de Implementação em `cadastros/templates/cadastros/form_projeto.html`:
1. No CSS (`<style>`):
   - Atualizar a regra das caixas de texto rico:
     ```css
     .wizard-step .richtext-editor-container,
     .wizard-step .richtext-editor-container .ql-container,
     .wizard-step .richtext-editor-container .ql-editor {
         height: auto !important;
         min-height: 100px;
         max-height: 48vh !important;
         overflow-y: auto !important;
     }
     ```
   - Tornar a barra de botões de navegação aderente na base do painel:
     ```css
     .wizard-step > .border-top {
         position: sticky !important;
         bottom: 0 !important;
         background-color: #ffffff !important;
         z-index: 1050 !important;
         margin-top: auto !important;
         padding-top: 0.85rem !important;
         padding-bottom: 0.85rem !important;
         margin-bottom: 0 !important;
         border-top: 1px solid #dee2e6 !important;
         box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.05) !important;
     }
     ```
   - Garantir respiro de rolagem no conteúdo dos passos para não sobrepor o rodapé:
     ```css
     .wizard-step > .row,
     .wizard-step > .row.g-4 {
         padding-bottom: 1.5rem;
     }
     ```

Arquivos liberados:
- `cadastros/templates/cadastros/form_projeto.html`

Arquivos proibidos:
- Todos os demais

Critério de pronto:
- Em qualquer tela (mesmo com texto longo ou dezenas de itens na tabela), a barra com os botões 'Voltar' e 'Próximo' permanece visível na base da tela sem exigir rolagem para ser encontrada.
- Textos longos no Quill crescem até 48vh e depois ganham rolagem interna suave sem quebrar a proporção da tela.

---

## [2026-09-03] Handoff Gemini → Copilot: Restauração de Fotos Inline e Recursos de Edição no Quill

Objetivo:
Restaurar o comportamento nativo de edição do Quill em `cadastros/templates/cadastros/form_projeto.html`:
1. Permitir que 2 ou mais fotos fiquem lado a lado na mesma linha (inline-block), eliminando o `display: block` e `margin: 1rem auto` que forçavam quebras de linha e texto gigante.
2. Adicionar opção de alinhamento (`[{ 'align': [] }]`) na barra de ferramentas do Quill para facilitar o posicionamento de fotos e textos.
3. Garantir que a exibição/ocultação da barra de ferramentas (toolbar) ao clicar em 'Editar' funcione perfeitamente controlando o container da toolbar diretamente via JS (`quill.getModule('toolbar').container`).

Escopo de Implementação em `cadastros/templates/cadastros/form_projeto.html`:
1. No CSS (`<style>`):
   - Substituir a regra restritiva de `.ql-editor img`:
     ```css
     .ql-editor img {
         max-width: 100%;
         height: auto;
         display: inline-block !important;
         vertical-align: middle;
         margin: 0.25rem;
         border-radius: 0.375rem;
     }
     ```
2. No JavaScript:
   - Adicionar alinhamento em `toolbarOptions`:
     ```javascript
     const toolbarOptions = [
         [{ 'header': [1, 2, 3, false] }],
         ['bold', 'italic', 'underline', 'strike'],
         [{ 'align': [] }],
         [{ 'list': 'ordered'}, { 'list': 'bullet' }],
         [{ 'indent': '-1'}, { 'indent': '+1' }],
         ['link', 'image', 'video'],
         ['clean']
     ];
     ```
   - No controle da toolbar sob demanda:
     Ao instanciar o Quill, capturar a toolbar:
     `const toolbarElem = quill.getModule('toolbar').container;`
     `toolbarElem.style.display = 'none';`
     No evento do botão 'Editar':
     - Se `isEditing`: `toolbarElem.style.display = 'block';`
     - Se concluído: `toolbarElem.style.display = 'none';`

Arquivos liberados:
- `cadastros/templates/cadastros/form_projeto.html`

Arquivos proibidos:
- Todos os demais

Invariante de negócio / UI:
- Imagens inseridas devem poder fluir lado a lado na mesma linha quando couberem na largura da caixa.
- O modo leitura esconde a toolbar; o modo edição exibe a toolbar no topo da respectiva caixa.

Critério de pronto:
- Ao colar ou inserir 2 imagens pequenas consecutivas no Quill, elas permanecem na mesma linha horizontal.
- A barra de menu só aparece ao clicar em 'Editar' e some ao clicar em 'Concluir'.

---

## [2026-09-03] Handoff Gemini → Copilot: Altura Padronizada dos Botões de Navegação (Base Passo 1)

Objetivo:
Fixar a altura dos botões 'Voltar' e 'Próximo' em todas as 17 telas do Wizard usando a altura do Passo 1 como padrão absoluto, eliminando saltos verticais da barra de ações.

Escopo de Implementação em cadastros/templates/cadastros/form_projeto.html:
1. No CSS (<style>):
   - Padronizar a altura mínima do painel de conteúdo:
     .wizard-content-panel {
         min-height: 680px;
         display: flex;
         flex-direction: column;
     }
     .wizard-step {
         display: none;
         flex-direction: column;
         flex-grow: 1;
         min-height: 100%;
     }
     .wizard-step.active {
         display: flex !important;
     }
   - Garantir que todos os containers de botões (.border-top com btn-prev e btn-next) usem:
     margin-top: auto !important;
     padding-top: 1rem;
     padding-bottom: 0.75rem;
     margin-bottom: 0.5rem;

Arquivos liberados:
- cadastros/templates/cadastros/form_projeto.html

Critério de pronto:
- Ao alternar entre o Passo 1 e os demais passos (2, 3, 4, 5, etc.), os botões 'Voltar' e 'Próximo' permanecem exatamente na mesma altura/posição vertical na tela.

---
## [2026-09-03] Handoff Gemini → Copilot: Edição Inline Sob Demanda (Toolbar Toggle on Click)

Objetivo:
Substituir o modal de edição pelo padrão 'Edição Inline Sob Demanda' nos campos RichText em cadastros/templates/cadastros/form_projeto.html:
- Por padrão, a toolbar do Quill fica oculta e o texto em modo somente leitura na página (altura 100% natural).
- Ao clicar no botão 'Editar', a barra de ferramentas do Quill aparece no topo da caixa e o campo fica editável.
- Ao clicar em 'Concluir', a toolbar some novamente, o campo volta para somente leitura e dispara o autoSave.
- Eliminar completamente os modais de rich text (#richtext-edit-modal e #richtext-read-modal).

Escopo de Implementação:
1. No CSS (<style>):
   - .richtext-editor-container:
     - Caixa sempre aberta na totalidade do texto: min-height: 90px; height: auto !important; max-height: none !important;
   - .ql-editor:
     - min-height: 90px; height: auto !important; max-height: none !important; overflow-y: visible !important;
   - Controle da Toolbar:
     - .richtext-editor-container .ql-toolbar { display: none !important; }
     - .richtext-editor-container.is-editing .ql-toolbar { display: block !important; border-top-left-radius: 0.375rem; border-top-right-radius: 0.375rem; background: #f8f9fa; }
   - Imagens responsivas:
     - .ql-editor img { max-width: 100% !important; height: auto !important; display: block; margin: 1rem auto; border-radius: 0.375rem; }

2. No JavaScript:
   - Criar cada Quill com sua toolbar normal (toolbarOptions), mas com quill.enable(false) inicialmente.
   - Botão de ação:
     - Inicia como: <button type="button" class="btn btn-sm btn-outline-primary btn-toggle-edit fw-bold"><i class="fas fa-edit me-1"></i> Editar</button>.
     - Ao clicar:
       - Alterna a classe is-editing no ditorContainer.
       - Se estiver editando:
         - quill.enable(true)
         - quill.focus()
         - Botão vira: <i class="fas fa-check me-1"></i> Concluir (classe tn-success).
       - Se concluiu a edição:
         - quill.enable(false)
         - Botão volta para: <i class="fas fa-edit me-1"></i> Editar (classe tn-outline-primary).
         - Sincroniza o textarea e chama utoSave().
   - Remover código e estruturas de modais (#richtext-edit-modal e #richtext-read-modal).

Arquivos liberados:
- cadastros/templates/cadastros/form_projeto.html

---
## [2026-09-03] Handoff Gemini → Copilot: Caixas Abertas na Totalidade + Edição Focada em Modal

Objetivo:
Simplificar drasticamente a interface dos campos RichText em cadastros/templates/cadastros/form_projeto.html:
1. Caixas na página abertas na totalidade do conteúdo (altura natural automática, sem travas de 80px, sem barras de menu na tela para não poluir).
2. Eliminar os botões de sanfona e lupa.
3. Manter um único botão elegante de 'Editar' (<i class='fas fa-edit me-1'></i> Editar) que abre o modal de edição completo com a barra de ferramentas do Quill.

Escopo de Implementação:
1. No CSS (<style>):
   - .wizard-step .richtext-editor-container.preview-editor,
     .wizard-step .richtext-editor-container.preview-editor .ql-container,
     .wizard-step .richtext-editor-container.preview-editor .ql-editor:
     - Remover travas de 80px!
     - Definir: height: auto !important; min-height: 90px; max-height: none !important; overflow-y: visible !important;
     - Garantir que a toolbar fique escondida na página: .preview-editor .ql-toolbar { display: none !important; }
   - Imagens responsivas:
     .ql-editor img, #richtext-edit-body img {
         max-width: 100% !important;
         height: auto !important;
         display: block;
         margin: 1rem auto;
         border-radius: 0.375rem;
     }
   - Remover classes de sanfona e estilos não utilizados.

2. No JavaScript (inicialização de textareas.richtext):
   - Remover a criação do accordionButton (sanfona) e do previewButton (lupa).
   - Remover o readModal (não é mais necessário, já que a página exibe o texto todo).
   - Manter apenas o botão de Editar:
     const expandButton = document.createElement('button');
     expandButton.type = 'button';
     expandButton.className = 'btn btn-sm btn-outline-primary richtext-expand fw-bold';
     expandButton.innerHTML = '<i class=\"fas fa-pen-to-square me-1\"></i> Editar';
     expandButton.title = 'Editar conteúdo';
     actions.appendChild(expandButton);
   - Manter a abertura do modal #richtext-edit-modal com Quill completo, toolbar, botão de limpar e botão de concluir.
   - Garantir que ao concluir a edição, o Quill da página receba o HTML e se expanda na totalidade do novo texto.

Arquivos liberados:
- cadastros/templates/cadastros/form_projeto.html

---
## [2026-09-03] Handoff Gemini → Copilot: Modal de Leitura Adaptável e Imagens Responsivas

Objetivo:
Tornar o modal de leitura (#richtext-read-modal) adaptável ao conteúdo em cadastros/templates/cadastros/form_projeto.html, garantindo que imagens não vazem para fora da caixa e o modal acomode diagramas amplos com rolagem elegante.

Escopo de Correção:
1. No CSS (<style>):
   - Forçar imagens responsivas no modal e no editor:
     #richtext-read-body img, #richtext-edit-body img, .ql-editor img {
         max-width: 100% !important;
         height: auto !important;
         display: block;
         margin: 1rem auto;
         border-radius: 0.375rem;
         box-shadow: 0 2px 8px rgba(0,0,0,0.1);
     }
   - Configurar o modal para adaptar-se dinamicamente:
     #richtext-read-modal .modal-dialog {
         max-width: min(1200px, 94vw);
     }
     #richtext-read-body {
         max-height: 80vh;
         overflow-y: auto;
         word-break: break-word;
     }

2. No JS/HTML de criação do readModal:
   - Trocar a classe de modal-dialog modal-dialog-centered modal-lg para:
     modal-dialog modal-dialog-centered modal-xl modal-dialog-scrollable

Arquivos liberados:
- cadastros/templates/cadastros/form_projeto.html

---
## [2026-09-03] Handoff Gemini → Copilot: Estabilização do Botão Sanfona (Eventos e Transição)

Objetivo:
Estabilizar o comportamento da Sanfona nos campos RichText em cadastros/templates/cadastros/form_projeto.html, eliminando a oscilação/flicker e garantindo abertura/fechamento 100% confiável e suave.

Causa identificada:
1. Como os botões estão inseridos dentro do <label>, o clique sem .stopPropagation() e .preventDefault() sobe para o label disparando eventos duplicados do navegador (duplo clique fantasma).
2. A substituição via innerHTML destrói o elemento <i> durante o evento do mouse.
3. Ausência de transição CSS suave, causando pulo abrupto do layout.

Escopo de Correção:
1. No JS:
   - Adicionar .preventDefault(); e.stopPropagation(); no evento de clique do ccordionButton, previewButton e xpandButton.
   - Alterar o ícone sem destruir o DOM: apenas alternar as classes a-chevron-down e a-chevron-up no elemento <i> existente.
2. No CSS:
   - Aplicar transição suave de altura (	ransition: max-height 0.3s ease-in-out).
   - Quando recolhido: max-height: 80px; overflow-y: hidden;.
   - Quando expandido (.accordion-expanded): max-height: 3000px !important; height: auto !important; overflow-y: visible !important;.

Arquivos liberados:
- cadastros/templates/cadastros/form_projeto.html

---
## [2026-09-03] Handoff Gemini → Copilot: Tríade RichText (Sanfona + Lupa Leitura + Lápis Edição)

Objetivo:
Implementar a tríade completa de interação dos campos RichText em cadastros/templates/cadastros/form_projeto.html:
1. Botão Sanfona (expandir/recolher inline na página, empurrando o conteúdo)
2. Botão Lupa (abrir modal de visualização/leitura ampla formatada sem toolbar)
3. Botão Lápis (abrir modal de edição com toolbar completo do Quill)

Escopo incluído:
1. Em cadastros/templates/cadastros/form_projeto.html:
   - No CSS:
     - Definir altura compacta padrão para .preview-editor: height: 85px; max-height: 85px; overflow-y: hidden;.
     - Definir expansão da sanfona para .accordion-expanded: height: auto !important; max-height: none !important; overflow-y: visible !important;.
     - Estilo para os 3 botões em .richtext-actions.
   - No HTML/JS:
     - Adicionar o botão de Sanfona (.richtext-accordion) com ícone as fa-chevron-down que alterna para a-chevron-up e adiciona/remove .accordion-expanded no container do editor.
     - Atualizar o botão da Lupa (.richtext-preview) com as fa-search para abrir um modal de LEITURA (#richtext-read-modal), exibindo o título do campo e o conteúdo formatado em HTML com botão "Fechar".
     - Manter o botão do Lápis (.richtext-expand) com as fa-edit para abrir o modal de EDIÇÃO (#richtext-edit-modal) com Quill completo.

Escopo excluído:
- Nenhuma alteração em backend (cadastros/views.py, models, forms).
- Nenhuma alteração fora de cadastros/templates/cadastros/form_projeto.html.

Arquivos liberados:
- cadastros/templates/cadastros/form_projeto.html

Arquivos proibidos:
- cadastros/views.py
- cadastros/models.py
- Qualquer outro arquivo.

Invariante de negócio:
- Manter o utoSave() e sincronização com textareas intactos.
- Os dados digitados no modal de edição devem continuar salvando perfeitamente.

Critério de pronto:
- Usuário vê 3 botões por campo de texto.
- Clicar na sanfona empurra o layout para baixo mostrando o texto todo.
- Clicar na lupa abre o modal limpo de leitura.
- Clicar no lápis abre o modal de edição com toolbar.

---
## [2026-09-03] Handoff Gemini → Copilot

Objetivo:
Testar a Opção B de visualização dos campos RichText no Wizard: expandir o container naturalmente para exibir todo o texto na página sem travas de 80px e sem efeito sanfona da lupa.

Escopo incluído:
1. Em cadastros/templates/cadastros/form_projeto.html:
   - Atualizar as regras CSS de .wizard-step .richtext-editor-container.preview-editor .ql-container e .ql-editor:
     - Alterar height, min-height e max-height para permitir expansão natural: min-height: 120px; height: auto !important; max-height: none !important; overflow-y: visible !important;.
   - No CSS ou no script de criação dos botões, ocultar ou desativar o botão .richtext-preview (a lupa), mantendo apenas o .richtext-expand (o lápis para edição em modal).

Escopo excluído:
- Nenhuma alteração em backend (cadastros/views.py, models, forms).
- Nenhuma alteração nos passos do wizard além do estilo/comportamento do container richtext.

Arquivos liberados:
- cadastros/templates/cadastros/form_projeto.html

Arquivos proibidos:
- cadastros/views.py (recém-higienizado pelo Devin)
- cadastros/models.py
- Qualquer outro arquivo fora do template.

Invariante de negócio:
- O salvamento assíncrono (autoSave) e a sincronização com os textareas ocultos (syncQuills) devem continuar intactos.
- O botão do lápis deve continuar abrindo o modal #richtext-edit-modal normalmente.

Critério de pronto:
- As caixas de texto com conteúdo mostram o texto integral sem rolagem interna ou cortes em 80px.
- O botão da lupa não interfere mais com comportamento sanfona.

---
## [2026-09-03] Auditoria de Conformidade: Onda 1 de Higiene - APROVADA

Status da Auditoria pelo Arquiteto (Antigravity-Gemini):
- Arquivos modificados: Estritamente cadastros/views.py (nenhum arquivo proibido foi tocado).
- Redução de complexidade: 158 linhas de código duplicado eliminadas com sucesso.
- Eliminação de duplicatas: Verificação confirmou 0 funções repetidas.
- Correção de dependência: 0 ocorrências de pydantic. Import de ValidationError normalizado para django.core.exceptions.
- Integridade do sistema: manage.py check executado com 0 erros identificados.

Entrega homologada com sucesso.

---
## [2026-09-03] Handoff Gemini → Devin

Objetivo:
Executar a Onda 1 de Higiene no backend eliminando o bloco duplicado em cadastros/views.py e corrigindo o import de ValidationError.

Escopo incluído:
1. Remover o bloco de código duplicado em cadastros/views.py (linhas 399 a 557). Esse bloco contém redefinições de imports redundantes, home_cadastros, listar_projetos, listar_pessoas_juridicas, listar_processos_global, uma versão defasada de 
ovo_projeto (sem a lógica de 'publicar'), e isualizar_projeto.
2. Na linha 5 de cadastros/views.py, substituir rom pydantic import ValidationError por rom django.core.exceptions import ValidationError.
3. Executar verificação com manage.py check para garantir integridade.

Escopo excluído:
- Qualquer alteração em cadastros/templates/cadastros/form_projeto.html (território do Copilot/usuário).
- Fatiamento de apps ou alteração de models/migrações.
- Qualquer alteração fora de cadastros/views.py.

Arquivos liberados:
- cadastros/views.py

Arquivos proibidos:
- cadastros/templates/cadastros/form_projeto.html
- cadastros/models.py
- Qualquer outro arquivo do projeto.

Invariante de negócio:
- A função 
ovo_projeto ativa deve ser a primeira (linhas 47-146), que preserva a regra de negócio ction == 'publicar'.
- Nenhuma view necessária pode ser excluída (xcluir_projeto, gerenciar_contas, etc. começam na linha 560 e devem ser preservadas).

Riscos / legado:
- Risco zero a dados legados. Sem impacto no banco.

Critério de pronto:
- manage.py check executado com 0 erros.
- Zero views duplicadas em cadastros/views.py.
- Nenhum import de pydantic no arquivo.

Pergunta ao usuário (se houver):
- Nenhuma.

---
## [03/09/2026] - Aprendizado de Recomendação Proativa de Modelos (/learn)

### O que foi feito:
- Adicionada a Seção 10 ao GEMINI.md: o assistente agora avalia proativamente a complexidade da demanda e orienta o usuário a alternar entre Gemini 3.8 Flash (tarefas rotineiras/leves) e Gemini 3.1 Pro / Claude Sonnet (tarefas densas/arquiteturais/Red Team), protegendo as cotas semanais.

---

## [03/09/2026] - Formalização do Squad e Rotina de Inicialização de IAs

### O que foi feito:
- **Rotina Obrigatória de Inicialização:** Criada a seção oficial no PROTOCOLO_COLABORACAO_IA.md exigindo que qualquer IA (Gemini, Copilot ou Devin) execute o checklist de início de sessão (ler manual próprio, ler protocolo, ler diário no topo, git status, respeitar uma IA por arquivo).
- **Manual do Devin:** Criado DEVIN.md na raiz do repositório, alinhado com GEMINI.md e COPILOT.md.
- **Matriz de Papéis:** Atualizada em todos os manuais táticos (PROTOCOLO_COLABORACAO_IA.md, GEMINI.md, COPILOT.md, DEVIN.md). Devin oficializado como o Desenvolvedor Autônomo e de Refatoração Pesada.

### O que ficou pendente:
- Usuário rodar .\scripts\salvar.ps1 para sincronizar os manuais e o protocolo no Git.
- Autorizar a Onda 1 (Higiene de código duplicado no cadastros/views.py) com Handoff para o Devin ou seguir no Wizard.

---
## [03/09/2026] - Manual tático do Gemini

### O que foi feito:
- Reescrito `GEMINI.md` no mesmo nível do `COPILOT.md`: papel (arquitetura,
  não implementação padrão), handoff executável, domínio a defender, o que
  não reabrir (protocolo já consolidado), fila de ondas e Red Team.
- `PROTOCOLO_COLABORACAO_IA.md` cita as três IAs e aponta `GEMINI.md` /
  `COPILOT.md` na precedência.

### O que ficou pendente:
- No próximo chat do Antigravity, pedir: *leia GEMINI.md*.
- Onda 1 de higiene ainda não autorizada.

---

## [03/09/2026] - Manual tático do Copilot

### O que foi feito:
- Criado `COPILOT.md` na raiz: papel do Copilot, início de sessão, arquivos
  quentes, armadilhas reais (`views.py` duplicado, wizard, termos, User↔Pessoa),
  checklist de implementação, proibições e modelo de handoff.
- `.github/copilot-instructions.md` passou a apontar para `COPILOT.md`.
- `PROTOCOLO_COLABORACAO_IA.md` e `GEMINI.md` registram o Cody como terceira
  IA e o arquivo tático do Copilot.

### O que ficou pendente:
- Copilot deve ler `COPILOT.md` no próximo chat (o GitHub só injeta o resumo
  de `.github/copilot-instructions.md` automaticamente).
- Onda 1 de higiene (`cadastros/views.py`) ainda não foi autorizada.

---

## 02/09/2026 (Preventivo - Edição de Projetos)
**Status Atual do Projeto:**
Sistema estabilizado rodando sob o PostgreSQL 18. O formulário de edição de ProjetoPDI (Wizard Caixa Eletrônico) foi plenamente restabelecido e validado, pronto para receber dados reais de produção.

**O que foi feito recentemente (Período/Sessão):**
- **Migração e Recuperação:** Finalizamos o switch para a nova instância do PostgreSQL 18. Todos os dados do banco argus_db permaneceram íntegros.
- **Lista de Alterações Críticas no HTML:**
  - form_projeto.html (Inputs): escopo e eap renomeados para escopo_geral e estrutura_analitica.
  - form_projeto.html (Javascript): Correção do crash no JS (TypeError) no modal que impedia o salvamento AJAX.
  - form_projeto.html (CSS): Modificação style reinjetado para forçar listas do Quill a renderizarem bolinhas (bullet points).
  - form_projeto.html (Layout): Injeção de pb-3 mb-2 no container d-flex justify-content-between nos 17 steps, subindo os botões na tela (~1cm).
  - form_projeto.html (linha 310): Alteração na tag option de tp.concedente.nome para tp.objeto.
  - views.py (linha 161): Remoção do truncamento do termo.objeto, permitindo exibir o nome completo no Select2.

**O que está pendente no nosso radar:**
- **Gestão de Projetos:** Aguardar o preenchimento de dados reais pelo usuário e continuar a evolução do módulo.

---

# Diário de Bordo - ARGUS

## [03/09/2026] - Substituição de IA no Squad

### O que foi feito:
- O **Cursor** foi oficialmente substituído pelo **Cody (Sourcegraph)** como Desenvolvedor de apoio na IDE devido a limites de cota.
- Atualizados GEMINI.md, COPILOT.md e PROTOCOLO_COLABORACAO_IA.md para refletir o Cody como a terceira IA do projeto.

---

## [03/09/2026] - Correção da visualização rich text

### O que foi feito:
- Corrigido o CSS das prévias Quill para iniciar em uma caixa recolhida de 80px, com rolagem interna.
- O botão de lupa agora alterna a expansão da própria caixa existente, exibindo o conteúdo completo sem duplicação ou nova janela.
- Removidas regras específicas conflitantes dos passos 4 e 5.
- `python manage.py check` executado com sucesso.

---

## [03/09/2026] - Fase 2 das rotinas de colaboração

### O que foi feito:
- Reestruturados `scripts/bom_dia.ps1` e `scripts/ate_amanha.ps1` para validar o código de saída de cada etapa.
- A rotina de início do dia agora identifica o maior ID global entre `backups/sql/` e `backups/json/`, informa os arquivos disponíveis e exige a confirmação literal `SUBSTITUIR` antes de qualquer restauração.
- A rotina de encerramento mantém a numeração global de três dígitos, gera SQL antes de JSON, exige `ARGUS_DB_USER`, `ARGUS_DB_NAME` e `ARGUS_DB_PASSWORD` e só publica após validações.
- As skills `github-bom-dia` e `github-ate-amanha` foram alinhadas aos scripts e não documentam mais credenciais fixas.
- A restauração JSON e SQL passou a executar `showmigrations` após a operação para validação.

### O que ficou pendente:
- Executar as rotinas no terminal do usuário quando necessário; a IA não deve executá-las diretamente.
- Validar em ambiente real uma restauração JSON e uma restauração SQL, sempre com confirmação explícita e backup disponível.

---

## [02/09/2026] - Refinamento da interface rich text do ProjetoPDI

### O que foi feito:
- Ajustado o layout do wizard de edição para reduzir espaços vazios e melhorar a ocupação vertical da tela.
- Reposicionado o botão Tela Cheia para a linha de ações do cabeçalho e preparado o modo de expansão do conteúdo na própria tela.
- Em `cadastros/templates/cadastros/form_projeto.html`, os campos rich text dos passos 4, 5 e seguintes passaram a usar prévias somente leitura, com bordas completas, altura adaptável e quebra de texto.
- Adicionados ícones de edição alinhados à direita: no título do passo 4 e nas labels dos subitens 5.1 e 5.2.
- Criado editor Quill separado em modal para edição, com barra de ferramentas, sincronização do conteúdo e botão Limpar com confirmação.
- Adicionada lupa liga/desliga para expandir a caixa de leitura existente, sem criar uma segunda caixa.
- Padronizada a inicialização: toolbar desativada nas prévias e habilitada somente no modal.
- Criado o commit `7b02284` e publicado na branch `main` do GitHub.

### O que ficou pendente:
- Validar visualmente a expansão da caixa existente pela lupa; a última tentativa ainda não apresentou o comportamento esperado.
- Executar a rotina de encerramento do dia no terminal do usuário, incluindo backup SQL/JSON, exportação de dependências, commit e push.

---

## [01/09/2026] - Refatoração UI do Wizard e Tratamento de Desastres (Edição de Projetos)

### 📝 O que foi feito:
- O painel de Plano de Ação (Aba 9) foi totalmente remodelado. Substituiu-se a antiga estrutura de 'Cards' por uma tabela dinâmica e responsiva com a criação de atividades concentrada em um Modal interativo e robusto.
- Implementado sistema de seleção de vigência (Meses Início e Fim) utilizando grid interativo (verde/vermelho).
- Melhorada a interface de inserção de entregáveis com botão '+' no modal.
- Resolvido bug crítico do Django onde 'Salvar Alterações' no backend não capturava as atividades corretamente na view de edição. Adicionado também o Auto-Save via AJAX ao fechar o modal.
- Correção emergencial de colisão de IDs de abas gerada por expressões regulares que haviam embaralhado e duplicado etapas (step6, step7, etc). As 17 abas foram re-mapeadas perfeitamente no backend para coincidir com a UI.

### ⏳ O que ficou pendente:
- **URGENTE / INVESTIGAR:** O usuário relatou que os botões (salvar, avançar, adicionar) **continuam sem funcionar** após a correção dos IDs HTML. Precisamos checar (1) O Console Javascript em busca de erros ocultos na renderização das abas (2) Se algum handler do botão '.btn-next' ou 'btn-add-atividade' foi perdido durante a restauração do arquivo via Git Checkout, ou (3) Se há bloqueios do Bootstrap na invocação do Modal. A prioridade máxima ao retornar é depurar e reativar a interatividade da página 'editar_projeto'.

## [31/08/2026] - Consolidação para repositório único em C:\ARGUS

### 📝 O que foi feito:
- Mesclado a branch `agents/github-ate-amanha-fix` no `main`.
- Consolidado o repositório no diretório principal `C:\ARGUS`.
- Removidos os metadados do Git worktree antigos (a pasta `C:\ARGUS.worktrees` pode ser deletada manualmente, pois está bloqueada por um handle do Windows).

### ⏳ O que ficou pendente:
- Limpar manualmente a pasta `C:\ARGUS.worktrees` se ela persistir (requer liberação de handles do sistema operacional).

## [31/08/2026] - Regra de Negócio Definitiva: Projeto PDI, Termo de Parceria e Termo de Cooperação

### 📝 O que foi definido para amanhã:
- Padronizar a regra de negócio do ARGUS para o módulo de projetos:
  - `ProjetoPDI` pode estar vinculado, opcionalmente, a um `TermoCooperacao` (acordo-mestre / guarda-chuva).
  - `ProjetoPDI` deve ser sempre vinculado a um `TermoDeParceria` (termo operacional específico do projeto).
- Ajustar a camada de domínio e a validação para refletir esta regra sem misturar os dois conceitos.
- Corrigir a tela de edição em `/cadastros/projeto/<id>/editar/` para carregar corretamente o vínculo do termo de parceria e manter o vínculo opcional do termo de cooperação.
- Garantir que o formulário e o backend usem os nomes e relacionamentos corretos: `termo_cooperacao` para o guarda-chuva e `termo_parceria` para o termo obrigatório do projeto.

### ⏳ O que ficou pendente:
- Implementar o ajuste do modelo, da view e do template e validar a persistência correta do vínculo em edição e cadastro do projeto.

## [31/08/2026] - Encerramento de Dia e Backup de Segurança

### 📝 O que foi feito:
- Finalização da rotina de fechamento do dia no projeto ARGUS, com atualização do histórico operacional e geração de backups híbridos para recuperação rápida e segura.
- Exportação das dependências para `requirements.txt` para preservar o estado atual do ambiente Python.
- Verificação do status do repositório e preparação do pacote de envio para sincronização remota.

### ⏳ O que ficou pendente:
- Validar a sincronização final da branch após o push e confirmar que o backup e o commit chegaram ao repositório remoto.

## [28/08/2026] - Desacoplamento do Wizard de Projetos e Polimorfismo

### 📝 O que foi feito:
- Refatoração do modelo de `ProjetoPDI` para incorporar a Chave Estrangeira `concedente` com polimorfismo para a classe-mãe `PessoaJuridica`. Isso resolve a restrição onde a EMBRAPII (Agência de Fomento) não conseguia ser a parceira/financiadora exclusiva de um projeto (ex: Programa de Desenvolvimento de Competências - PDC).
- Separação Arquitetural do "Nascimento" de Projetos e Termos (adequação às regras do SIPAC): a Aba 1 do Wizard não exige e não cadastra mais um Termo em paralelo. O Pesquisador apenas seleciona a Empresa/Agência, as Instituições (IFAM e FAEPI por padrão), e a Aba 2 busca Termos abertos via AJAX.
- Implementação e registro de uma nova entidade mestre no banco e no painel administrativo: `TermoCooperacao` (Acordo Guarda-Chuva). Essa tabela permite relacionar a relação matriz de 5 anos do IFAM-EMBRAPII com os projetos filhos (os PDCs anuais).
- O HTML do Formulário do Wizard foi todo polido: removemos os múltiplos botões "Próximo" duplicados que confundiam a UI, padronizamos as *labels* com a terminologia da Lei de P&D (10.973/04), e o filtro do Concedente agora carrega dividido em grupos (`<optgroup>`) ordenados: Empresas Parceiras e Agências de Fomento, não mostrando mais ICTs ou Fundações na raiz.

### ⏳ O que ficou pendente:
- **Painel Financeiro (Aba 3) / Dashboard Visual:** Implementar a visualização dos dados consolidados do projeto, orçamentos, gráficos e tabelas (Aba 3 da tela visualizar_projeto.html).
- **Validação de Travas Financeiras:** Precisamos programar os gatilhos no formulário de Orçamento para bloquear a submissão se a porcentagem das rubricas não bater a regra de Contrapartida da EMBRAPII (33%) vs Empresa (10%). Atenção: se o projeto for de Capacitação (PDC), a trava da contrapartida empresarial deve ser desativada.
- Criar endpoints da API (ou carregar na própria view) os recursos gráficos/painéis da "Aba 3 Financeiro".



## 27/08/2026 (Parte 3)
**Status Atual do Projeto:**
Regras de negócio de Finanças (SUFRAMA) e P&D (EMBRAPII) foram absorvidas pelo motor do sistema.

**O que foi feito recentemente:**
- **Estudo Legislativo (/learn):** Analisamos a Portaria 9835/2022 (Suframa) e o Manual de Operações (Embrapii). Fixamos o modelo de *7 Rubricas Orçamentárias* e as travas de limites (ex: 30% Terceiros, 15% Suporte Operacional).
- **Trancas de Cronograma:** Adicionamos validação no backend (`AtividadePlanoAcao.clean()`) para garantir que Macroentregas não sobreponham datas no cronograma (regra EMBRAPII). As rubricas de banco de dados foram refatoradas para as 7 categorias exatas.

**O que está pendente no nosso radar:**
- **Gestão de Projetos:** Construir a interface visual e dashboard de detalhamento do projeto (Dashboard do Projeto), onde as Macroentregas e Atividades (Plano de Ação) serão gerenciadas, além da visualização financeira e orçamentária que usará essas novas regras (Aba 3).

---## 27/08/2026 (Parte 2)
**Status Atual do Projeto:**
Modelagem do Plano de Trabalho totalmente concluída no banco e nas telas iniciais de cadastro (Wizard).

**O que foi feito recentemente:**
- **Plano de Trabalho Backend:** Modelamos os 15 itens do plano seguindo padrão EMBRAPII com campos Rich Text e cálculos de calendário relativos (M1, M2...). As migrações (`0044`, `0045`) foram aplicadas.
- **Plano de Trabalho Frontend:** A tela de cadastro (`form_projeto.html`) foi dividida em áreas de Negócio (Motivação, Estratégia, Desafios) com integração nativa da biblioteca `Quill.js` via CDN para permitir edição rica de texto ao usuário, além do `Select2` para indicadores múltiplos.
- **Salvar Nuvem:** Projeto salvo via `/github-salvar`.

**O que está pendente no nosso radar:**
- **Gestão de Projetos:** Construir a interface visual e dashboard de detalhamento do projeto (Dashboard do Projeto), onde as Macroentregas e Atividades (Plano de Ação) serão gerenciadas, além da visualização financeira (Aba 3).

---## 27/08/2026
**Status Atual do Projeto:**
Sessão de arquitetura profunda concluída. Aprovada regra de 'Red Team' (análise crítica obrigatória).

**O que foi feito recentemente:**
- **Gêmeo Digital 2.5D:** Implementada a infraestrutura nos Ambientes (campos `pe_direito`, `perimetro`, `PlantaBaixa`) para permitir orçamentos automatizados de limpeza e pintura, e navegação via mapa SVG/PNG no futuro. Código salvo na nuvem com sucesso.

---

## 26/08/2026
**Status Atual do Projeto:**
O ambiente está limpo e consolidado. Removemos árvores de trabalho sobressalentes sem impactos.

**O que foi feito recentemente:**
- **Limpeza de Repositório:** Analisamos e excluímos uma pasta redundante de worktree (`C:\ARGUS.worktrees`) e a branch obsoleta `agents/git-pull-novidades` que não possuía commits novos em relação à branch `main`.

**O que está pendente no nosso radar:**
- **Gestão de Projetos:** Retomar a definição de como investigar e registrar dados de Relatórios de Atividade (RA) no módulo de gestão de projetos.

---

## 25/08/2026
**Status Atual do Projeto:**
O sistema agora lida de forma dinâmica e hierárquica com ambientes físicos e os relacionamentos de LGPD. As rotinas diárias e banco de dados continuam protegidos e os fluxos ajustados para maior precisão de visualização e busca de dados.

**O que foi feito recentemente:**
- **Central de Serviços (Ambientes):** Implementamos o conceito de Matriz Espacial Mutável. Ambientes agora podem possuir subdivisões (Ambientes Pais/Filhos) para maior precisão na localização de ativos. Adicionado flag `ativo` para soft-delete, resguardando relatórios e histórico financeiro ou ordens de serviço. Ajustamos `AmbienteListView` e `relatorios.html` para exibir e tratar as árvores de ambientes corretamente. DataTables de Ambientes fixado para 50 linhas padrão.
- **Gestão de Projetos:** Corrigido o `FieldError: Cannot resolve keyword 'bolsista' into field` no relatório de atividades, ajustando as consultas nas views para usar `pessoa` (nova nomenclatura baseada no padrão LGPD da plataforma). Também adicionamos anotações do Pyright (pyrefly) nas views para evitar falsos positivos de linting.

**O que está pendente no nosso radar:**
- **Gestão de Projetos:** Investigar e registrar dados de Relatórios de Atividade (RA) ausentes no módulo de gestão de projetos.

---

## 24/08/2026
**Status Atual do Projeto:**
Ambiente totalmente estável, sem alterações estruturais no banco de dados e sincronizado perfeitamente com a nuvem (sem interrupções de token).

**O que foi feito recentemente:**
- **Análise Estrutural:** Fizemos um reconhecimento das entidades e templates do módulo de Gestão de Projetos focados no Relatório de Atividade (RA) (`RelatorioAtividade`, `ItemAtividade`). Identificamos que o CRUD já existe nos arquivos.
- O dia foi encerrado enquanto aguardamos definições de negócio sobre como proceder com a pendência dos RAs (se vamos gerar *mock data*, corrigir bugs de tela ou importar legados).

**O que está pendente no nosso radar:**
- **Gestão de Projetos:** Retomar a definição de como investigar e registrar dados de Relatórios de Atividade (RA) no módulo de gestão de projetos.

---

## 19/08/2026
**Status Atual do Projeto:**
O banco de dados está purificado e as rotinas diárias e o repositório Git estão totalmente blindados contra travamentos e corrupção de caracteres.

**O que foi feito recentemente:**
- **Recuperação de Dados e Enconding:** Identificamos que a restauração anterior de SQL estava inserindo lixo no banco devido ao código de página do Windows. Rodamos um script ORM em python (`fix_db_strings.py`) que corrigiu ao vivo todas as strings do banco sem perder os dados novos da nuvem.
- **Automação Segura:** Atualizamos as *skills* `bom-dia` e `ate-amanha` para forçar `PGCLIENTENCODING=utf8` em todas as operações com `psql` e `pg_dump`. 
- **Autenticação Automática Git:** Configuramos um token PAT na URL remota do repositório, garantindo push/pull invisível e livre de prompts de login no Windows.

**O que está pendente no nosso radar:**
- **Gestão de Projetos:** Iniciar de fato a investigação e o registro de dados de Relatórios de Atividade (RA) ausentes no módulo de gestão de projetos.

---

## 17/08/2026
**Status Atual do Projeto:**
O sistema de backups foi completamente refatorado para garantir maior segurança em transições e migrações. O erro de estáticos locais no modo desenvolvedor foi resolvido.

**O que foi feito recentemente:**
- **Sincronização:** Recebemos uma massiva atualização da nuvem (mais de 50 arquivos), reestruturando completamente Pessoas Físicas e Jurídicas. As migrações foram aplicadas com sucesso.
- **Backups Híbridos:** A regra de backups (`BACKUP_NAMING.md`) e as rotinas diárias foram reescritas para suportar um sistema híbrido. Agora geramos backups SQL e JSON, arquivados em subpastas correspondentes (`backups/sql/` e `backups/json/`).
- **WhiteNoise Local:** O erro 500 no `runserver` foi diagnosticado como ausência de estáticos devido ao `DEBUG=False`. Criamos um arquivo `.env` forçando `DEBUG=True` no ambiente de desenvolvimento local.

**O que está pendente no nosso radar:**
- **Gestão de Projetos:** Investigar e registrar dados de Relatórios de Atividade (RA) ausentes no módulo de gestão de projetos.

---

## 14/08/2026 (Encerramento Extra)
**Status Atual do Projeto:**
O projeto encerra o dia com a consolidação das regras de preservação de histórico.

**O que foi feito recentemente:**
- **Diário de Bordo:** Reforço da regra no `github-ate-amanha` para proibir a sobrescrita do diário e garantir a inserção no topo. Este registro demonstra a regra em ação.

**O que está pendente no nosso radar:**
- **Gestão de Projetos:** Investigar e registrar dados de Relatórios de Atividade (RA) ausentes no módulo de gestão de projetos.

---

## 14/08/2026
**Status Atual do Projeto:**
O projeto está avançando com foco na melhoria da usabilidade (ordenamento espacial) e consolidação de regras rígidas de segurança (backups) e documentação.

**O que foi feito recentemente:**
- **Central de Serviços:** Implementação de ordenação espacial (Drag-and-Drop) utilizando SortableJS na árvore de Relatórios para agrupamento por proximidade física. Inserção do campo `ordem` nos modelos `Predio`, `Andar` e `Ambiente` com reordenação via requisições AJAX (`ReordenarItensView`).
- **Automação e DevOps:** Criação da regra universal rigorosa para backups (`BACKUP_NAMING.md`), estabelecendo o prefixo `NNN_` sequencial obrigatório. As rotinas diárias (`github-bom-dia` e `github-ate-amanha`) foram devidamente atualizadas para obedecer a essa regra.
- **Documentação IA:** Elaboração de um Catálogo de Comandos do Assistente (`CATALOGO_COMANDOS.md`) para padronizar o fluxo Git/Dev em assistentes de IA. As regras de orquestração foram consolidadas no `PROTOCOLO_COLABORACAO_IA.md`.
- **Diário de Bordo:** Estabelecimento da regra de Diário de Bordo na raiz do projeto, integrada diretamente às rotinas "bom dia" e "até amanhã" para controle autônomo de contexto entre sessões.

**O que está pendente no nosso radar:**
- **Gestão de Projetos:** Investigar e registrar dados de Relatórios de Atividade (RA) ausentes no módulo de gestão de projetos.














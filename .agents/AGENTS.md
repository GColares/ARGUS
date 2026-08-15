# Regras de Arquitetura do ARGUS

## Módulos e Home Principal
Sempre que você criar, renomear ou excluir um aplicativo/módulo no projeto ARGUS, você deve obrigatoriamente editar a view `home_argus` localizada em `argus_core/views.py`. 
O dicionário `modulos` dentro dessa view controla os painéis exibidos na tela principal (dashboard) do sistema. O novo módulo só ficará visível e acessível para o usuário final se for adicionado a essa lista.

## Idioma
Responda sempre em **Português do Brasil (pt-BR)**.

## Telas de Cadastro (CRUD)
Sempre que você criar, planejar ou modificar funcionalidades de "Cadastro" (CRUD) no sistema, é OBRIGATÓRIO incluir e implementar a função de "Excluir" (Delete). Todas as telas de listagem ou formulários de edição devem prover um caminho claro e funcional para a exclusão do registro, preferencialmente com confirmação (ex: modal ou página de confirmação do Django) para evitar deleções acidentais.

## Estilo de Tabelas
Os cabeçalhos (`<th>` ou `<thead>`) de todas as tabelas criadas no sistema devem ter os rótulos centralizados obrigatoriamente (por exemplo, utilizando a classe utilitária `text-center` do Bootstrap). As colunas de "Ações" (editar/excluir) também devem acompanhar esse alinhamento para manter a uniformidade visual.

## Navegação e UX (Botão Voltar)
Todas as páginas e telas desenvolvidas para o sistema Argus devem obrigatoriamente conter um link de "Voltar" (Back) padronizado sob o breadcrumb. 
1. O texto deve ser sempre o mesmo: `<i class="fas fa-arrow-left me-1"></i> Voltar` (sem redundâncias como "Voltar para o painel").
2. O direcionamento deve ser **estritamente dinâmico e inteligente** utilizando `javascript:history.back()`. Nunca utilize URLs hardcoded do Django (`{% url ... %}`) em botões de "Voltar", para garantir que o usuário retorne exatamente de onde veio (mantendo filtros, paginações e histórico do navegador).

## Padrão Visual de Telas de Listagem (Padrão Almoxarifado)
Sempre que criar, refatorar ou modificar uma página de listagem de dados (ListView) no ARGUS, você deve obrigatoriamente seguir a anatomia de UI baseada no Almoxarifado:
1. **Breadcrumbs:** Incluir a trilha de navegação (ex: `<nav aria-label="breadcrumb">`) logo no início do container principal.
2. **Link Voltar:** O botão de voltar deve ser um link discreto sem bordas (`text-muted small fw-bold mb-2 d-inline-block`) imediatamente abaixo do breadcrumb.
3. **Cabeçalho (Row de Título e Ações):** Utilizar Flexbox para manter o Título da página + Badge (contagem de itens) agrupados à esquerda. Colocar botões de ação globais (Exportar, Novo Cadastro, etc.) agrupados à direita da mesma linha. Incluir sempre um subtítulo informativo abaixo do título principal.
4. **Filtros (Server-side):** A listagem deve usar o padrão de Formulário (GET) com botão que revela uma "Gaveta de Filtros Avançados" (`data-bs-toggle="collapse"`). O Javascript puro (Client-side) para ordenação e busca inteligente só deve ser usado em tabelas estáticas muito simples, nunca nas telas principais (Listas Mestras).
5. **Margens e Container:** Utilizar o container padrão `<div class="container-fluid px-4 mt-4">`.

## Estética de Dashboards (Homes de Módulos)
As páginas iniciais (Dashboards) dos módulos devem exibir um design mais interativo e moderno (Premium):
1. **Glassmorphism:** Priorizar o uso de backgrounds translúcidos (`rgba(255,255,255, 0.8)`) associados a `backdrop-filter: blur(10px)` para painéis e cards (`.cs-card`), gerando profundidade.
2. **Cores Semânticas:** Usar sempre variáveis nativas do Bootstrap (`var(--bs-primary)`, `var(--bs-success)`) e seus correspondentes RGB para criar fundos opacos suaves (ex: `rgba(var(--bs-success-rgb), 0.1)`). **NUNCA** utilizar cores hexadecimais (HEX) fixadas (ex: `#2c3e50`) no CSS.
3. **Consistência de Interação:** Efeitos de hover devem escalar ícones e alterar a opacidade dos fundos suavemente via `transition`. Evite usar classes utilitárias engessadas (ex: `bg-success`) diretamente no HTML se o elemento já possui uma classe base com animações CSS planejadas.

## Regras de Renderização para DataTables
Sempre que uma tabela HTML for processada via **DataTables (Javascript)** no lado do cliente:
1. **NÃO utilize a tag `{% empty %}`** do Django com colunas fundidas (`colspan`) dentro da tag `<tbody>`.
2. Se a QuerySet for vazia, entregue o `<tbody></tbody>` completamente vazio ao HTML. 
3. O próprio script nativo do DataTables irá detectar a ausência de nós filhos e se encarregará de renderizar de forma segura e responsiva a mensagem de tabela vazia ("Nenhum registro encontrado").

## Agrupamento Semântico de Cadastros Base (Domain-Driven UI)
Sempre que criar modais, menus ou painéis que listem entidades base do sistema (Cadastros Base/Domínios), **evite listas planas**. 
As entidades devem ser obrigatoriamente agrupadas visualmente por **Contexto de Negócio** (Domain-Driven UI) utilizando subtítulos divisores.
Isso é vital para lidar com entidades que possuem nomes genéricos em módulos diferentes (ex: Categoria de Serviço, Categoria de Elemento, Tipo de Ambiente, Tipo de Ativo).
*Exemplo de Grupos:* "Infraestrutura (Espaços)", "Elementos Físicos", "Ativos/Equipamentos", "Parâmetros de O.S.".

## Padronização de Atributos em Cadastros Base
Sempre que criar ou modificar entidades de "Cadastro Base" (Tabelas de Domínio/Paramétricas como Categorias, Tipos, Finalidades, Status, etc.):
1. **Descrição Obrigatória:** Elas devem sempre possuir, além de `nome`, um campo `descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")`. Isso é vital para explicar a outros usuários do sistema *quando* ou *como* usar aquela opção.
2. **Auditoria:** Elas devem sempre incorporar `history = HistoricalRecords()` para rastrear quem adicionou ou editou esses parâmetros centrais do sistema.

## Cobertura Completa de CRUD para Cadastros Base
Todas as entidades de "Cadastro Base" definidas no `models.py` devem obrigatoriamente possuir um fluxo CRUD completo (List, Create, Update, Delete) implementado (com Views, URLs e Templates). Além disso, todas elas devem estar incondicionalmente acessíveis na interface do usuário (ex: dentro do modal "Cadastros Base do Sistema"), organizadas pelo seu Contexto de Negócio. Nenhuma entidade base deve ficar "oculta" ou inacessível no frontend.

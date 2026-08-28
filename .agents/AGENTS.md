# Regras de Arquitetura do ARGUS

## Módulos e Home Principal
Sempre que você criar, renomear ou excluir um aplicativo/módulo no projeto ARGUS, você deve obrigatoriamente editar a view `home_argus` localizada em `argus_core/views.py`. 
O dicionário `modulos` dentro dessa view controla os painéis exibidos na tela principal (dashboard) do sistema. O novo módulo só ficará visível e acessível para o usuário final se for adicionado a essa lista.

## Idioma
Responda sempre em **Português do Brasil (pt-BR)**.

## Telas de Listagem e Ações (CRUD Completo)
Sempre que você criar, planejar ou modificar uma tela contendo uma **lista de registros** (DataTables ou tabelas padrão):
1. A coluna de "Ações" deve obrigatoriamente fornecer ações completas. Para Listas Mestras (telas principais), inclua **Visualizar, Editar e Deletar**. Para listas secundárias (relacionamentos 1:N exibidos em abas ou telas de gerenciamento de entidades vinculadas, como contas de um projeto), inclua obrigatoriamente, no mínimo, **Editar e Deletar**, evitando fluxos sem saída onde o usuário não consegue corrigir um erro de digitação sem deletar e recriar o dado.
2. O botão **Deletar** deve direcionar para um fluxo seguro com confirmação (ex: modal ou página de confirmação do Django) para evitar deleções acidentais.
3. **Limpeza Visual de Listas (Separação de Detalhes):** As telas de listagem principal (ex: lista de Projetos) devem ser limpas e objetivas. Informações pesadas, complexas ou listas de entidades relacionadas (ex: Cotas do Projeto, Processos do Projeto, etc.) **não devem** ser colocadas na tabela principal. Elas devem ser realocadas exclusivamente para a tela de **Visualizar** (Detalhes) daquele registro específico.

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

## Fidelidade de Atributos em Telas (Models vs Views/Forms)
Sempre que você criar, modificar ou refatorar formulários (`forms.py`) e telas de leitura/edição (`_form.html`, `_list.html`), é **OBRIGATÓRIO** garantir que **todos os atributos e campos** daquela entidade definidos no `models.py` estejam contemplados e visíveis na interface do usuário. 
1. Nenhum campo de negócio do modelo deve ficar de fora das telas de leitura e edição.
2. É estritamente proibido omitir campos obrigatórios no `ModelForm` (o que causaria `IntegrityError`), a menos que o preenchimento deles seja automatizado/injetado exclusivamente via backend (ex: `request.user` ou data de criação automática).
3. Se um template HTML renderizar os campos do formulário manualmente (ex: invocando `{{ form.campo_especifico }}` um a um em vez de `{{ form }}` genérico), é **obrigatório** inspecionar e editar diretamente o arquivo HTML para inserir a tag do novo campo sempre que o modelo/formulário correspondente for alterado.

## Migrações Seguras de Modelos (Campos Obrigatórios)
Sempre que adicionar um novo atributo obrigatório (sem `null=True`) a uma entidade já existente e populada, você deve **obrigatoriamente** fornecer um valor padrão através do parâmetro `default=` (ex: `default=1`) no código Python para garantir que os registros antigos recebam esse valor durante a migração, evitando travamentos de `IntegrityError` no banco de dados.

## Campos de Data em Formulários (Inputs HTML5)
Sempre que utilizar `forms.DateInput` com `attrs={'type': 'date'}` no `forms.py`, é **obrigatório** definir o formato ISO explicitamente na instanciação do widget. 
*Exemplo correto:* `forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})`. 
Sem a definição de `format`, o Django renderizará a data no padrão localizado e o navegador não preencherá o input, fazendo com que as datas pareçam estar em branco na tela de edição.

## Nomenclatura e Modelagem de Parcerias
1. **Termo de Parceria vs Convênio:** O termo "Convênio" está obsoleto no sistema. A união de interesses para consecução de projetos PDI é formalizada no **Termo de Parceria**.
2. **Plano de Trabalho:** Todo Termo de Parceria deve possuir um vínculo com um **Plano de Trabalho**, que detalha a abordagem técnica, financeira e o produto a ser entregue. O Plano de Trabalho pode ter mais de uma versão (histórico/aditivos).
3. **Atores (Partícipes):** As parcerias são assinadas por três papéis estritos: **CONCEDENTE** (Empresa financiadora), **CONVENENTE** (IFAM/Polo de Inovação) e **INTERVENIENTE** (Fundação de Apoio, ex: FAEPI). 
4. **Pessoa Jurídica (Herança Multi-tabela):** As entidades participantes abandonaram modelagens rasas e agora seguem estritamente os papéis da Hélice Tríplice da Lei 10.973/04. A entidade base `PessoaJuridica` guarda os dados globais (CNPJ, Endereço, Representante), mas o sistema ramifica-se em 4 filhos diretos: `ICT` (Convenente), `EmpresaParceira` (Concedente), `FundacaoApoio` (Interveniente) e `AgenciaFomento` (Apoiadores). No `TermoDeParceria`, as ForeignKeys apontam estritamente para essas subclasses.

## Fluxo Unificado de Cadastro de Projetos (Wizard)
O conceito de "Projeto" na visão do usuário encapsula a formalização do **Termo de Parceria** e do seu **Plano de Trabalho** correspondente. 
Sempre que você criar, editar ou refatorar o fluxo de cadastro principal de um Projeto PDI:
1. **Interface em Abas (UI):** O formulário deve ser dividido em abas (ex: abas do Bootstrap). 
   - **Aba 1:** Informações do Termo de Parceria (Atores, Vigência, Objeto, Número).
   - **Aba 2:** Informações do Plano de Trabalho (Abordagem Técnica, Financeira, Entregas).
2. **Submissão Única (Backend):** A view responsável por receber o POST (ex: `novo_projeto` ou `editar_projeto`) deve orquestrar a validação múltipla (usando múltiplos formulários de Django: `TermoDeParceriaForm`, `PlanoDeTrabalhoForm` e `ProjetoPDIForm` se necessário) e salvar todas as entidades de forma atômica utilizando `transaction.atomic()`.
3. **Seleção Inteligente:** Não se deve forçar o usuário a cadastrar um Termo de Parceria em uma tela separada para depois vinculá-lo via dropdown na tela de Projeto. A criação do Projeto **é** a criação da Parceria e do seu Plano.
4. **Visualização em Abas (Dashboard do Projeto):** A tela de detalhes do projeto (`visualizar_projeto.html`) deve espelhar o modelo mental do fluxo de cadastro. A leitura dos dados deve ser categorizada obrigatoriamente nas seguintes abas principais:
   - **Aba 1 (Termo de Parceria):** Dados de qualificação, vigência e atores (Concedente, Convenente, Interveniente).
   - **Aba 2 (Plano de Trabalho):** Além das Abordagens (Técnica/Financeira) e Produto, deve obrigatoriamente exibir a tabela de **Equipe do Projeto** (Recursos Humanos Diretos e Indiretos) extraída de `plano_ativo.equipe.all()`.
   - **Aba 3 (Orçamento/Financeiro):** Deve atuar como um painel central de P&D exibindo 4 elementos: (1) Cards com os Aportes Globais (Empresa, EMBRAPII, SEBRAE), (2) Resumo das Rubricas Orçamentárias, (3) Cronograma de Desembolso Financeiro, e (4) Contas Bancárias.

## Layout Fluido para Formulários (Wizards)
Telas de formulários compostos, com abas ou grande número de colunas (como o Cadastro de Projetos), devem obrigatoriamente utilizar o padrão de largura total da tela (`container-fluid px-4 mt-4`), assim como os Dashboards de Visualização. É estritamente proibido limitá-los com containers centrais estreitos (ex: `col-lg-8`), garantindo conforto visual e o aproveitamento do layout horizontal.

## Selects Inteligentes (Select2 Global)
Toda vez que você criar ou modificar um formulário contendo campos `<select>`, é **obrigatório** o uso da classe `.form-select` (do Bootstrap 5). O ARGUS possui uma inicialização global nativa no seu `base.html` que converte automaticamente todos os `.form-select` em instâncias do **Select2**, garantindo suporte à pesquisa, quebra de texto em opções longas e design padronizado. Nunca injete scripts isolados do Select2 nas páginas filhas.

## Arquitetura de Pessoa Física (Party-Role Pattern) e Conformidade LGPD
1. **Entidade Central (Identidade Canônica):** O ARGUS deve possuir um modelo central único `PessoaFisica` contendo exclusivamente dados intrínsecos e universais do indivíduo (Nome, CPF, Data de Nascimento, Gênero, Dados de Contato e Endereço). Este modelo é o núcleo para governança da LGPD, garantindo que a eliminação ou anonimização ocorra em um só lugar.
2. **Separação de Papéis (Roles):** Categorias e vínculos (ex: Servidor, Aluno, Bolsista, Fornecedor PF, Terceirizado, Representante Legal) **não devem** herdar de `PessoaFisica` via herança multi-tabela clássica que force exclusividade. Elas devem ser modeladas como **Perfis/Papéis** vinculados à `PessoaFisica` via `OneToOneField` ou `ForeignKey`. Um indivíduo pode possuir múltiplos papéis simultaneamente.
3. **Minimização de Dados (Lazy Data Collection):** O sistema não deve exigir o preenchimento de dados irrelevantes para o contexto no momento do cadastro. Dados específicos (ex: SIAPE para servidor, Matrícula para aluno) pertencem estritamente aos seus respectivos perfis e não à entidade `PessoaFisica`.
4. **Isolamento de Dados Sensíveis:** Informações de pagamento (Contas Bancárias) devem ser segregadas em um modelo próprio (`DadoBancario`), vinculado à `PessoaFisica`, permitindo controle de acesso granular restrito (RBAC).
5. **Governança e Direito ao Esquecimento:** Todo dado pessoal deve estar atrelado à base legal do papel desempenhado (ex: Execução de Contrato para bolsistas). O encerramento de um vínculo (ex: fim da bolsa) não deleta a `PessoaFisica` caso ela ainda possua outro perfil ativo (ex: Servidor). Quando a exclusão total for devida, aplica-se a **Anonimização Irreversível** (ou Crypto-Shredding) para preservar a integridade das chaves estrangeiras contábeis e de auditoria, sem violar a privacidade.

## Modelagem de Espaços Físicos (Matriz Mutável e Localização)
A infraestrutura do INOVA é mapeada como uma matriz espacial de coordenadas onde limites físicos são fixos, mas a identidade lógica se transforma (ex: Diretoria vira Copa). Além disso, a localização física exata é a única forma eficiente de referenciar dezenas de equipamentos (ex: Ar-Condicionados) em laboratórios massivos (como o LSCN). Ao trabalhar com `Ambiente`, siga rigorosamente:

1. **Hierarquia de Localização (Composite Pattern):** Ambientes devem suportar subdivisões através de `ambiente_pai = models.ForeignKey('self', ...)`. Isso permite que macrolaboratórios contenham micro-ambientes (ex: LSCN > Sala de Pesagem).
2. **Vínculo Granular de Ativos:** Ativos Prediais e Ordens de Serviço devem **sempre** ser vinculados ao nível mais profundo possível da árvore (o sub-ambiente exato), para que equipes de manutenção encontrem o equipamento pela geografia, não pelo número de série.
3. **Ciclo de Vida (Soft-Delete):** É terminantemente proibido deletar permanentemente ou sobrescrever ambientes que sofreram mutação (mudaram de propósito). Eles devem ser inativados (`ativo = models.BooleanField(default=True)`) para preservar o histórico de Ordens de Serviço antigas, criando-se um novo ambiente na mesma "posição matriz".
4. **Nomenclatura Contextual:** A identificação visual (`__str__`) deve refletir a rota do ambiente herdando o nome do pai (ex: "LSCN - Copa") para eliminar ambiguidades no uso do sistema.

## Postura de Análise Crítica (Red Team)
Sempre que o usuário propor uma nova ideia, solução de negócio, modelagem de banco de dados ou arquitetura, é **OBRIGATÓRIO** realizar uma análise crítica profunda antes de executá-la ou concordar.
Sua resposta deve estruturar-se identificando:
1. **Pontos Fortes:** O que faz sentido e resolve o problema.
2. **Erros, Fragilidades e Riscos:** Casos extremos, limitações tecnológicas, gargalos de UX, dívidas técnicas ou falhas lógicas da proposta.
3. **Melhorias e Soluções:** Propostas arquiteturais ou fluxos alternativos que mitiguem os riscos encontrados e elevem o nível técnico do sistema.
Jamais aceite uma ideia complexa passivamente sem submetê-la a esse crivo analítico.


## Orçamento e Cronograma de Projetos (Regras SUFRAMA e EMBRAPII)
Sempre que você modelar, refatorar ou desenvolver o escopo Financeiro (Rubricas) e o Cronograma (Plano de Ação) de um Projeto, você deve aplicar as seguintes travas e regras de negócio extraídas da Portaria SUFRAMA 9835/2022 e do Manual de Operações EMBRAPII:

1. **A Estrutura de Rubricas (Categorias Fixas):**
   Entidades que mapeiem orçamentos (`RubricaOrcamentaria`) não podem usar strings livres. Devem obrigatoriamente possuir um campo de escolha (`choices`) ancorado nas categorias legais conjuntas:
   - Pessoal (RH Direto e Indireto)
   - Material de Consumo
   - Diárias, Passagens e Locomoção
   - Serviços de Terceiros (PF e PJ)
   - Capital e Equipamentos (Atenção: Proibido usar recursos EMBRAPII. Apenas Empresa).
   - Suporte Operacional / Administrativo (Overhead)
   - Outras Despesas Correntes (Utilities, taxas, patentes)
   *(Obras Civis são estritamente proibidas em qualquer fonte).*

2. **Travas Financeiras (Validações de Backend):**
   - **EMBRAPII:** Aporte mínimo de 10% do valor do projeto.
   - **Empresa:** Aporte mínimo de 10% (ou 50% se for obrigação legal de P&D).
   - **Serviços de Terceiros:** A soma não pode ultrapassar 30% do valor total do projeto.
   - **Suporte Operacional (Overhead):** Limitado a 15% do valor total (EMBRAPII) ou 20% (SUFRAMA). **Trava:** Esse custo só pode ser pago com recursos da Empresa parceira ou como contrapartida da Unidade.
   - **Outras Despesas (SUFRAMA):** Limitado a 20% da soma das demais rubricas de custeio e capital.

3. **Cronograma e Macroentregas:**
   - Todo projeto deve focar nos níveis TRL 3 a 6.
   - **Regra de Sequenciamento:** As Macroentregas (Planejamento Físico) **não podem ser sobrepostas no tempo**. O sistema deve validar em cascata que a `data_inicio` da Macroentrega 2 é `>=` à `data_fim` da Macroentrega 1.


## Padronização de Formulários Extensos (Wizard Híbrido)
Sempre que o sistema exigir a entrada de formulários complexos e longos (ex: Gestão de Projetos, Planos de Trabalho):
1. **Foco na Altura da Tela:** É proibido exigir do usuário rolagens intermináveis. O conteúdo deve ser encapsulado em passos (Steps/Abas) que se ajustem à *viewport*.
2. **Salvamento Progressivo Híbrido (Offline-First):** O sistema deve implementar salvamento assíncrono combinando `LocalStorage` (Frontend) para tolerância a quedas de rede, e Sessões/Tabelas de Rascunho (Backend) para garantir a mobilidade do usuário entre dispositivos.
3. **Integridade do Banco (Proibição de Projetos Órfãos):** O salvamento parcial (ao clicar em "Avançar") NUNCA deve acionar o comando `.save()` em tabelas finais de negócio de forma incompleta, burlando a Transação Atômica. Apenas quando o fluxo é finalizado as entidades definitivas devem ser consolidadas.


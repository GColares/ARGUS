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

## Refatoração Segura de Relacionamentos (1:1 para 1:N)
Sempre que você alterar um relacionamento de banco de dados no Django (por exemplo, migrando um campo `OneToOneField` ou FK direta para um `ForeignKey` reverso, o que altera a cardinalidade e o `related_name` padrão, como de `termo_parceria` para `termos_parceria`), você **deve obrigatoriamente**:
1. **Atualizar a ORM (Views/Managers):** Fazer uma varredura (grep/search) no projeto para encontrar e corrigir todas as chamadas de `.filter()`, `.select_related()`, `.prefetch_related()` ou `.order_by()` que ainda usam a string da chave antiga, prevenindo a quebra da página com `FieldError`.
2. **Backward-Compatibility para Templates:** Criar uma `@property` no modelo mestre que preserva o nome exato do atributo antigo (ex: `@property def termo_parceria(self): return self.termos_parceria.first()`). Isso evita a quebra imediata de dezenas de templates HTML que já utilizavam a notação de ponto (ex: `{{ projeto.termo_parceria.numero }}`).

## Campos de Data em Formulários (Inputs HTML5)
Sempre que utilizar `forms.DateInput` com `attrs={'type': 'date'}` no `forms.py`, é **obrigatório** definir o formato ISO explicitamente na instanciação do widget. 
*Exemplo correto:* `forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})`. 
Sem a definição de `format`, o Django renderizará a data no padrão localizado e o navegador não preencherá o input, fazendo com que as datas pareçam estar em branco na tela de edição.

## Nomenclatura e Modelagem de Parcerias
1. **Termo de Parceria vs Convênio:** O termo "Convênio" está obsoleto no sistema. A união de interesses para consecução de projetos PDI é formalizada no **Termo de Parceria**.
2. **Plano de Trabalho:** Todo Termo de Parceria deve possuir um vínculo com um **Plano de Trabalho**, que detalha a abordagem técnica, financeira e o produto a ser entregue. O Plano de Trabalho pode ter mais de uma versão (histórico/aditivos).
3. **Atores (Partícipes):** As parcerias são assinadas por três papéis estritos: **CONCEDENTE** (Empresa financiadora), **CONVENENTE** (IFAM/Polo de Inovação) e **INTERVENIENTE** (Fundação de Apoio, ex: FAEPI). 
4. **Pessoa Jurídica (Herança Multi-tabela):** As entidades participantes abandonaram modelagens rasas e agora seguem estritamente os papéis da Hélice Tríplice da Lei 10.973/04. A entidade base `PessoaJuridica` guarda os dados globais (CNPJ, Endereço, Representante), mas o sistema ramifica-se em 4 filhos diretos: `ICT` (Convenente), `EmpresaParceira` (Concedente), `FundacaoApoio` (Interveniente) e `AgenciaFomento` (Apoiadores). No `TermoDeParceria`, as ForeignKeys apontam estritamente para essas subclasses.
5. **Hierarquia de Fomento Macro (Termo > Programa > Projeto):** Projetos que fazem parte de um fomento maior (Guarda-Chuva) não devem ser vinculados a um campo achatado. A modelagem de dados e a interface devem respeitar estritamente três camadas hierárquicas:
   - **Termo de Cooperação:** O instrumento jurídico matriz assinado com o concedente.
   - **Programa:** (Nova Entidade) A rodada ou subdivisão temática do Termo (Ex: PDC 2025). Pertence a um Termo de Cooperação (1:N).
   - **Projeto PDI:** A pesquisa em si. Quando pertencer a um guarda-chuva, o Projeto deve ter uma ForeignKey obrigatória apontando para o **Programa** (e nunca diretamente para o Termo de Cooperação). No Frontend (Wizard), o dropdown de "Programa" deve constar estritamente na Aba 1 (Dados Cadastrais).

## Separação de Nascimentos (Projeto vs Termo) e Fluxo do Wizard
O ciclo de vida burocrático público (SIPAC) exige que o **ProjetoPDI** e o **TermoDeParceria** nasçam em momentos e por atores diferentes, sendo vinculados depois:
1. **Intenção do Projeto (Pesquisador):** O Pesquisador cria o `ProjetoPDI` e o `PlanoDeTrabalho` via Wizard. Na Aba 1, ele informa qual é a **Empresa Parceira** (Concedente), pois o projeto nasce com uma intenção comercial.
2. **Registro do Termo (Contratos):** O Núcleo de Contratos abre o processo no SIPAC, gerando um número e cadastrando o `TermoDeParceria` no sistema (ainda em tramitação).
3. **Vínculo Inteligente:** Na Aba 2 do Wizard de Projeto, o sistema faz um filtro AJAX buscando Termos de Parceria "em aberto" pertencentes à Empresa informada na Aba 1, permitindo o vínculo imediato.
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
4. **Governança e Perfis de Acesso (RBAC):** Identificar qual Perfil de Usuário (ex: Pesquisador, Gestor de PDI, Administrador do Sistema, Financeiro) deterá a permissão, a alçada ou a responsabilidade para aprovar, executar ou tratar as atividades críticas e os riscos mapeados.
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



## Ciclo de Vida de Projetos PDI (Máquina de Estados)
Todo projeto gerenciado no sistema deve prever uma máquina de estados (campo `fase` ou `status`) que represente fielmente a realidade da gestão pública e os marcos de auditoria. 
Fases obrigatórias (no mínimo):
1. **Prospecção:** Fase de rascunho, ideação e negociação. Dados podem ser alterados livremente.
2. **Execução:** Iniciada após a formalização (Termo Assinado). O escopo técnico (Plano de Trabalho) entra em "congelamento integral".
3. **Prestação de Contas:** Iniciada na conclusão técnica do projeto. Envolve auditoria financeira e entrega de relatórios finais. Regras estritas de travamento financeiro se aplicam.
4. **Encerrado / Arquivado:** Fim do ciclo de vida.

## Catálogo Vivo de Perfis de Acesso (RBAC)
O sistema trabalha com um dicionário de perfis baseados em papéis. Nas Análises Críticas (Red Team), o agente deve sempre recorrer a este catálogo para sugerir quem terá a alçada sobre ações sensíveis.

**1. Gestão e Governança Superior**
- **Reitor / Alta Gestão IFAM:** Instância final, emite autorização formal (ex: Fundo de Reserva).
- **Diretor-Geral do Polo:** Nível máximo local. Assina submissão de propostas e aprova chefias.
- **Gestor do NIT:** Valida e emite parecer técnico de aprovação/rejeição das Prestações de Contas da Fundação de Apoio.
- **Comitê de Inovação:** Avalia estritamente o cumprimento do objeto técnico dos projetos PDI.
- **Pró-Reitoria de Administração (Coord. de Prestação de Contas):** Realiza auditoria contábil e analisa demonstrações financeiras.

**2. Gestão Operacional do Polo**
- **Diretor Administrativo/Financeiro:** Acompanha licitações e execução orçamentária dos Planos de Trabalho Anuais.
- **Coordenador de Projetos (Polo):** Emite parecer técnico prévio sobre projetos apresentados.
- **Núcleo de Gestão de Qualidade / PI:** Avalia grau de inovação e resguarda propriedade intelectual.
- **Coordenador de RH / Seleção:** Gerencia banco de especialistas e processos seletivos de bolsistas.
- **Coordenador de Laboratório:** Gerencia agendamentos da infraestrutura e aprova relatórios de ensaios.
- **Fundação de Apoio (Interveniente):** Efetua pagamentos, gere contas e submete prestações de contas financeiras mensais.

**3. Atores de Execução de Projeto (Equipe)**
- **Gestor de Projeto (GPO) / Programa:** Responsável pela gestão administrativa/financeira da execução.
- **Coordenador de Projeto (CPO):** Líder técnico. Elabora proposta, coordena pesquisa e prestação de contas técnica.
- **Analista Administrativo (AAD):** Faz conciliação contábil do projeto e relatórios financeiros.
- **Pesquisador (PEQ) / Docente:** Executa a pesquisa. **Trava (Docente):** Máximo de 20h/semanais de bolsa. Vedado pagamento para cargo CD-01.
- **Estudante / Bolsista (EST):** Executa tarefas sob supervisão direta. Não tem poder de gestão.


## Ciclo de Vida de Projetos PDI (Máquina de Estados)
Todo projeto gerenciado no sistema deve prever uma máquina de estados (campo `fase` ou `status`) que represente fielmente a realidade da gestão pública e os marcos de auditoria. 
Fases obrigatórias (no mínimo):
1. **Prospecção:** Fase de rascunho, ideação e negociação. Dados podem ser alterados livremente.
2. **Execução:** Iniciada após a formalização (Termo Assinado). O escopo técnico (Plano de Trabalho) entra em "congelamento integral".
3. **Prestação de Contas:** Iniciada na conclusão técnica do projeto. Envolve auditoria financeira e entrega de relatórios finais. Regras estritas de travamento financeiro se aplicam.
4. **Encerrado / Arquivado:** Fim do ciclo de vida.

## Catálogo Vivo de Perfis de Acesso (RBAC)
O sistema trabalha com um dicionário de perfis baseados em papéis. Nas Análises Críticas (Red Team), o agente deve sempre recorrer a este catálogo para sugerir quem terá a alçada sobre ações sensíveis.
*(Nota: Este catálogo será iterativamente preenchido pelo usuário à medida que o sistema evolui).*
- [A PREENCHER PELO USUÁRIO]
- [A PREENCHER PELO USUÁRIO]

## Identificação Visual de Entidades (Sigla vs Nome Longo)
Sempre que uma entidade (especialmente `PessoaJuridica` e suas filhas) for representada no sistema (seja no `__str__` do modelo, em dropdowns do HTML, templates ou listas), é **obrigatório** adotar o padrão de identificação colocando a Sigla (ou Nome Fantasia) antes do Nome Longo/Razão Social.
*Exemplo correto:* `IFAM - Instituto Federal do Amazonas` ou `FAPEAM - Fundação de Amparo...`.
No nível do banco de dados, isso se traduz em criar propriedades ou sobrescrever o `__str__` para testar a existência de `sigla` ou `nome_fantasia` na herança da classe antes de renderizar o `nome` raiz.

## Segregação de Papéis: ICT Executora (Polo/Sede)
Sempre que gerenciar cadastros de entidades jurídicas (ICTs) ou construir formulários de Termos de Parceria e Projetos:
1. **Identificação da Sede:** A instituição matriz do sistema (ex: IFAM) deve obrigatoriamente possuir um identificador booleano (ex: `is_executora=True` no modelo `ICT`) para distingui-la das demais ICTs externas.
2. **Proibição de Autocontratação (Isolamento de Concedentes):** É estritamente proibido que a "ICT Executora" apareça na listagem de seleções para "Concedente/Parceiro" em qualquer formulário do sistema (ex: `TermoCooperacaoForm`, `TermoDeParceriaForm`). No `__init__` desses formulários, o `queryset` do campo correspondente deve utilizar `.exclude(id__in=ids_executoras)` para ocultar a sede.

## Obrigatoriedade de Identificação Curta (Sigla/Nome Fantasia)
Sempre que cadastrar ou modelar entidades jurídicas baseadas em `PessoaJuridica` (como `ICT`, `EmpresaParceira`, `FundacaoApoio`, `AgenciaFomento` e `Fornecedor`), é **obrigatório** garantir que o sistema exija a entrada tanto do nome longo (Razão Social) quanto de uma identificação curta.
1. **Instituições e Entidades Públicas:** O campo `sigla` deve ser sempre obrigatório (jamais utilize `blank=True, null=True` na modelagem do banco).
2. **Empresas Privadas:** O campo `nome_fantasia` deve ser sempre obrigatório.
*Motivação:* Isso garante que a regra de exibição visual (que concatena `{Sigla} - {Razão Social}`) sempre possua dados íntegros para formatar as opções de seleção para o usuário, evitando campos em branco nas listas e quebras de design.

## Modelagem do Aporte SEBRAE (Parceria EMBRAPII)
Sempre que modelar o plano de trabalho e as rubricas financeiras de um projeto que envolva recursos do SEBRAE, aplique estritamente as seguintes regras:
1. **Ausência de Vínculo Contratual Direto:** O SEBRAE **não** é parte signatária (Partícipe/Concedente) do Termo de Cooperação ou Convênio do Projeto. O recurso do SEBRAE é gerido e repassado diretamente pela **EMBRAPII Matriz** para a conta do projeto (gerida pela Fundação/ICT).
2. **Natureza do Recurso:** O aporte do SEBRAE atua como um *subsídio à cota-parte financeira da Empresa*. Logo, a Empresa Concedente deve ser obrigatoriamente classificada como MEI, ME, EPP, MPE ou Startup.
3. **Travas de Rubricas para SEBRAE:**
   - **PROIBIDO** utilizar recursos do SEBRAE para pagamento de **Capital e Equipamentos** (assim como a restrição padrão da EMBRAPII).
   - **PROIBIDO** utilizar recursos do SEBRAE para pagamento de **Suporte Operacional / Administrativo (Overhead)**. Esta rubrica continua sendo de responsabilidade exclusiva dos recursos diretos da Empresa (caixa) ou da Contrapartida da ICT.
   - O recurso SEBRAE deve ser destinado majoritariamente a Despesas de Custeio direto da pesquisa (ex: Recursos Humanos Diretos e Consumo).

## Padronização Tipográfica e Hierarquia Visual (Design System)
Para manter a consistência estética e profissional em todas as telas do ARGUS, evite variações injustificadas de tamanho de fonte e siga uma hierarquia tipográfica estrita usando apenas as classes utilitárias do Bootstrap 5:
1. **Títulos Principais de Páginas (Page Headers):** Devem utilizar <h4> ou <h3> com as classes w-bold e a cor primária do contexto (ex: 	ext-info ou 	ext-primary).
2. **Subtítulos e Divisores de Seção (Block Headers):** Devem utilizar <h6> acompanhado de w-bold text-uppercase small text-muted (ou cor temática). É proibido usar tamanhos gigantes para cabeçalhos de blocos internos (cards/acordeões).
3. **Texto de Corpo e Descrições:** O texto padrão é o de corpo (sem classe extra). Textos de apoio ou instruções devem obrigatoriamente usar a classe small (ou .text-muted) para não poluir visualmente a leitura.
4. **Tamanho de Botões (Action Buttons):** 
   - Nunca use a classe tn-lg para ações dentro de barras de ferramentas (Headers de Cards, Navbars, Listagens), mesmo que seja a ação principal como "Salvar". O uso de tn-lg gera botões desproporcionais e quebra a harmonia da linha de leitura.
   - Botões globais no topo das páginas devem manter o tamanho normal de componente Bootstrap.
   - Use tn-sm estritamente para ações densas dentro de tabelas (DataTables).
5. **Estilos Inline Proibidos:** Confie nas classes s-1 até s-6 do Bootstrap. Evite injetar regras como ont-size: 1.2rem; dentro das tags <style>.


## UX de Alertas e Pendências (Notificações Não-Intrusivas)
Sempre que desenvolver formulários complexos que envolvam validações do backend com múltiplos erros (ex: fluxos de salvamento parcial vs publicação):
1. **Fim dos Alertas Inline Gigantes:** É expressamente proibido renderizar blocos de alerta (ex: `<div class="alert">`) no topo do formulário que empurrem o layout principal da página para baixo.
2. **Uso de Modal Auto-Trigger:** As listas de pendências e erros devem ser renderizadas dentro de um componente genérico de **Modal do Bootstrap**. Se houver erros (`{% if form.errors %}`), um script JS deve exibir esse modal automaticamente no carregamento da página.
3. **Ícone de Notificação Persistente:** Ao lado dos botões de ação principais (ex: Salvar/Publicar), deve ser posicionado um ícone de notificação (ex: sino `fa-bell` com *badge* numérico) que serve de gatilho (`data-bs-toggle="modal"`) para reabrir o modal a qualquer momento.
4. **Campos Obrigatórios Econômicos:** Não utilize o padrão verboso do Django para listar erros embaixo de cada campo (ex: `{{ field.errors }}`). Omitir essas renderizações para economizar altura vertical e utilize apenas um asterisco vermelho discreto (`<span class="text-danger">*</span>`) na *label* dos campos obrigatórios.


## Princípio de UX: Operação "Caixa Eletrônico" (Zero Rolagem)
A experiência do usuário no ARGUS rejeita o padrão web de páginas longas. A arquitetura de interface deve ser pensada sob a ótica de um terminal de autoatendimento:
1. **Telas Estáticas:** Por princípio, todo o conteúdo produtivo (formulários, painéis, wizards) deve ser desenhado para caber confortavelmente em uma única tela (Viewport), eliminando a necessidade de barras de rolagem vertical globais ou locais.
2. **Paginação sobre Rolagem:** Se uma tela ou etapa de formulário possuir campos demais para caber no monitor, é estritamente proibido ativar a rolagem (`overflow-y: auto`). A solução arquitetural correta é "virar a página", ou seja, fatiar o formulário em mais passos/abas (ex: Passo 2.1, Passo 2.2), forçando o usuário a interagir apenas clicando em botões de "Próximo" e "Voltar".

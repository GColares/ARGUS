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




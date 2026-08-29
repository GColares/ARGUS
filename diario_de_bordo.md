# Diário de Bordo - ARGUS

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
- **Documentação IA:** Elaboração de um Catálogo de Comandos do Assistente (`CATALOGO_COMANDOS.md`) e de um prompt exportável (`prompt_rotinas_ia.md`) para padronizar o fluxo Git/Dev em outros assistentes de IA (Gemini, Copilot, etc.).
- **Diário de Bordo:** Estabelecimento da regra de Diário de Bordo na raiz do projeto, integrada diretamente às rotinas "bom dia" e "até amanhã" para controle autônomo de contexto entre sessões.

**O que está pendente no nosso radar:**
- **Gestão de Projetos:** Investigar e registrar dados de Relatórios de Atividade (RA) ausentes no módulo de gestão de projetos.

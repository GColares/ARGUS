# Diário de Bordo - ARGUS

## 27/08/2026
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

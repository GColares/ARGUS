# Diário de Bordo - ARGUS

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

- **27/08/2026**: Sessão de arquitetura profunda. Aprovada regra de 'Red Team' (análise crítica obrigatória). Foi implementada a infraestrutura do 'Gêmeo Digital 2.5D' nos Ambientes (campos pe_direito, perimetro, PlantaBaixa) para permitir orçamentos automatizados de limpeza e pintura, e navegação via mapa SVG/PNG no futuro. Código salvo na nuvem com sucesso.

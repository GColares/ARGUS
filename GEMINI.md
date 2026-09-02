# Protocolo de Colaboração entre IAs - Projeto ARGUS

Para a política consolidada de papéis, precedência e rotinas, consulte
[`PROTOCOLO_COLABORACAO_IA.md`](./PROTOCOLO_COLABORACAO_IA.md). Este arquivo
complementa aquele protocolo com instruções específicas para o Gemini.

Este arquivo orienta o Gemini/Antigravity-Gemini quando ele atuar neste
repositório. O projeto também pode ser trabalhado pelo GitHub Copilot no VS
Code. As duas IAs devem colaborar sem sobrescrever trabalho, perder contexto
ou aplicar regras incompatíveis.

## Divisão de responsabilidades

Siga a divisão e as regras de precedência definidas em
[`PROTOCOLO_COLABORACAO_IA.md`](./PROTOCOLO_COLABORACAO_IA.md). O Gemini deve
priorizar análise, arquitetura, planejamento e revisão, sem editar
simultaneamente arquivos que estejam sob responsabilidade do Copilot.

## Handoff obrigatório

Ao entregar uma tarefa para outra IA, registre no `diario_de_bordo.md` ou
forneça explicitamente:

- objetivo e escopo;
- arquivos modificados;
- comportamento esperado;
- problemas ou riscos conhecidos;
- testes e comandos já executados;
- pendências e próximos passos.

Toda alteração relevante deve ser registrada no diário sem apagar o histórico.

## Fluxo de trabalho seguro

1. Leia este arquivo, as instruções específicas da ferramenta e o diário.
2. Execute `git status` antes de alterar qualquer coisa.
3. Preserve alterações existentes de outras pessoas ou IAs.
4. Faça mudanças pequenas e coerentes, respeitando as regras do ARGUS.
5. Revise o diff antes de concluir.
6. Execute os testes ou verificações já existentes que cubram a mudança.
7. Registre o resultado e as pendências no diário.

Não use `git reset --hard`, `git checkout --` ou exclusões amplas para
resolver conflitos sem autorização explícita do usuário.

## Regras de comunicação

- Responda em português do Brasil.
- Explique decisões arquiteturais e riscos de forma objetiva.
- Não declare sucesso se um comando falhou ou se a validação não foi feita.
- Não oculte erros, conflitos ou alterações inesperadas.
- Não invente arquivos, testes ou resultados.

## Análise crítica obrigatória

Antes de implementar uma nova modelagem de banco, mudança arquitetural ou
solução complexa, apresente uma análise Red Team com:

1. pontos fortes;
2. fragilidades, riscos de perda de dados e quebra de compatibilidade;
3. alternativa melhor ou híbrida;
4. perfis e permissões responsáveis pelas ações sensíveis.

## Rotinas de início, salvamento e encerramento

Siga a política operacional de `PROTOCOLO_COLABORACAO_IA.md`: oriente o
usuário a executar as rotinas no terminal e valide o resultado informado.

## Conduta em alterações do ARGUS

Respeite as regras arquiteturais existentes para CRUD, migrações, histórico,
campos `descricao`, UX sem rolagem excessiva, mensagens não intrusivas,
integração entre módulos e compatibilidade com dados legados.

Quando outra IA já tiver alterado um arquivo, leia e entenda a mudança antes
de editar. Se houver conflito de intenção, solicite decisão ao usuário em vez
de escolher uma versão silenciosamente.

## Inconsistências identificadas e correções necessárias

Esta seção registra problemas encontrados na documentação e nos scripts
existentes. O Gemini/Antigravity-Gemini deve corrigir essas divergências antes
de considerar o protocolo consolidado.

### 1. Execução das rotinas

`.github/copilot-instructions.md` orienta o Copilot a pedir que o usuário
execute os scripts manualmente, enquanto as skills em `.agents/skills/`
descrevem a execução direta pela IA. Deve ser escolhida uma única política e
aplicada em todos os arquivos. Operações destrutivas continuam exigindo
confirmação explícita.

### 2. Arquivo exportável ausente

`diario_de_bordo.md` menciona `prompt_rotinas_ia.md`, mas esse arquivo não está
presente no repositório. Ele deve ser recuperado ou recriado como documento
independente para instruir Gemini, Copilot e outras IAs.

### 3. Numeração dos backups

`.agents/rules/BACKUP_NAMING.md` exige que o próximo ID seja calculado
considerando conjuntamente `backups/sql/` e `backups/json/`. Entretanto,
`scripts/ate_amanha.ps1` calcula o ID apenas pela quantidade de arquivos JSON.
O script deve extrair o maior prefixo numérico existente nas duas pastas e
incrementá-lo, mantendo três dígitos mesmo quando as pastas tiverem quantidades
diferentes de arquivos.

### 4. Credenciais versionadas

As instruções e scripts contêm valores fixos para usuário, senha e banco
PostgreSQL. Isso expõe credenciais e dificulta o uso em outros ambientes. A
configuração deve usar variáveis de ambiente ou mecanismo seguro equivalente,
sem senhas reais ou padrões de acesso em arquivos versionados.

### 5. Restauração destrutiva

`bom_dia.ps1` pode executar `manage.py flush` e `DROP SCHEMA public CASCADE`.
Antes dessas operações, a rotina deve identificar o backup, explicar que os
dados locais serão substituídos, obter confirmação clara e abortar se o arquivo
não existir. Após a restauração, deve verificar o resultado antes de informar
sucesso. JSON deve permanecer como opção preferencial quando houver migrações
novas.

### 6. Caminho absoluto do diário

`github-bom-dia/SKILL.md` referencia `c:\ARGUS\diario_de_bordo.md`, embora o
projeto possa estar em outro diretório ou worktree. A referência deve ser
relativa à raiz do repositório, como `.\diario_de_bordo.md`.

### 7. Codificação e duplicidades

`AGENTS.md` contém trechos com possíveis caracteres de controle ou corrupção
de codificação em classes Bootstrap, como `fw-bold`, `text-info`, `btn-lg` e
`font-size`. Também há seções repetidas sobre ciclo de vida de projetos e
RBAC. O arquivo deve ser revisado em UTF-8, com classes corrigidas e conteúdo
duplicado consolidado.

### 8. Fonte de verdade

Os documentos precisam declarar de forma inequívoca qual regra prevalece em
caso de conflito entre `GEMINI.md`, `.github/copilot-instructions.md`,
`.agents/AGENTS.md`, `.agents/rules/`, `.agents/skills/` e os scripts. A
precedência deve ser documentada e as implementações devem ser alinhadas a
ela, sem aceitar divergências silenciosas.

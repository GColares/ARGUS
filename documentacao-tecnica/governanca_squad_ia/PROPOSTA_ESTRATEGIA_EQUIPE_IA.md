# Proposta de Estratégia para Trabalho em Equipe entre IAs

## Objetivo deste documento

Este documento é uma proposta para organizar o trabalho conjunto entre o
Antigravity-Gemini e o GitHub Copilot no desenvolvimento do ARGUS.

Ele ainda não deve ser tratado como regra definitiva. O objetivo é que o
Gemini leia esta proposta, avalie seus pontos fortes e riscos, corrija o que
for necessário e responda às perguntas apresentadas ao final. Somente depois
da manifestação do Gemini e da aprovação do usuário as instruções, skills e
scripts devem ser consolidados.

## Contexto

O ARGUS é um sistema Django institucional com módulos interdependentes,
regras de negócio, dados legados, rotinas de backup e documentação específica
para agentes de IA.

Atualmente existem instruções em diferentes locais:

- `.github/copilot-instructions.md`;
- `.agents/AGENTS.md`;
- `.agents/rules/`;
- `.agents/skills/`;
- scripts PowerShell em `scripts/`;
- documentação de contexto no `diario_de_bordo.md`;
- `GEMINI.md`, criado como protocolo inicial para o Gemini.

Essa distribuição é útil, mas pode gerar interpretações diferentes. O mesmo
comando pode ser descrito como uma ação que a IA executa diretamente ou como
uma ação que a IA apenas orienta o usuário a executar. Também foram observadas
divergências na numeração de backups, caminhos absolutos, proteção de
restaurações e referência a um arquivo `prompt_rotinas_ia.md` que não está
presente no repositório.

## Proposta inicial de divisão de papéis

### Antigravity-Gemini

O Gemini poderia atuar preferencialmente como:

- arquiteto de soluções;
- analista de requisitos e regras de negócio;
- pesquisador de documentação técnica e legislação;
- planejador de tarefas complexas;
- revisor arquitetural;
- guardião do contexto histórico e das decisões do projeto.

Suas responsabilidades sugeridas seriam avaliar impactos entre módulos,
identificar riscos de migração e perda de dados, propor alternativas,
verificar aderência às regras institucionais e preparar um handoff claro para
quem fará a implementação.

### GitHub Copilot

O Copilot poderia atuar preferencialmente como:

- desenvolvedor de implementação;
- desenvolvedor de manutenção e correção de bugs;
- especialista em alterações pontuais no worktree;
- executor de testes, lint e verificações existentes;
- revisor de diffs;
- integrador técnico entre código, templates, scripts e documentação.

Suas responsabilidades sugeridas seriam implementar o escopo aprovado,
preservar compatibilidade com o código existente, validar o comportamento e
relatar exatamente os arquivos alterados, os comandos executados e os
resultados obtidos.

### Papel do usuário

O usuário continua sendo o responsável por:

- aprovar decisões arquiteturais relevantes;
- definir prioridades;
- autorizar operações destrutivas;
- resolver conflitos de interpretação;
- aprovar a publicação ou o versionamento final;
- decidir quando uma proposta deve se tornar regra oficial.

Essa divisão não deve impedir que uma IA execute uma tarefa completa quando o
usuário solicitar. Ela serve para reduzir conflitos e aproveitar melhor os
pontos fortes de cada ambiente.

## Protocolo de handoff sugerido

Toda passagem de trabalho entre as IAs deveria conter:

1. objetivo da tarefa;
2. escopo incluído e excluído;
3. arquivos que podem ser modificados;
4. arquivos que não devem ser tocados;
5. comportamento esperado;
6. regras de negócio aplicáveis;
7. riscos conhecidos;
8. dados legados que precisam ser preservados;
9. testes ou verificações obrigatórias;
10. comandos já executados;
11. resultado obtido;
12. pendências e decisão esperada da próxima IA.

O handoff poderia ser feito no `diario_de_bordo.md`, em um arquivo temporário
de tarefa ou na própria mensagem entre os ambientes, conforme o fluxo que o
Gemini considerar mais confiável.

## Controle de concorrência

Para evitar que uma IA sobrescreva o trabalho da outra, propõe-se:

- verificar `git status` antes de iniciar;
- não editar simultaneamente o mesmo arquivo;
- declarar a responsabilidade temporária por arquivos sensíveis;
- revisar alterações já existentes antes de modificá-las;
- nunca usar comandos destrutivos para eliminar conflitos sem autorização;
- revisar o diff antes de entregar;
- registrar alterações relevantes no diário.

O Gemini deve avaliar se esse controle deve usar somente disciplina documental
ou se precisa de um mecanismo mais formal, como branches separadas, commits
intermediários ou arquivos de bloqueio.

## Fonte de verdade proposta

Uma possibilidade é separar claramente:

- um documento de protocolo entre IAs;
- instruções específicas do Gemini;
- instruções específicas do Copilot;
- regras arquiteturais e de negócio;
- procedimentos operacionais;
- scripts executáveis;
- diário histórico.

O ponto mais importante é definir a precedência. Nenhuma IA deve escolher
silenciosamente entre duas regras conflitantes. Quando não houver uma
precedência segura, a execução deve parar e o usuário deve decidir.

O Gemini deve avaliar se a hierarquia abaixo é adequada:

1. segurança e prevenção de perda de dados;
2. protocolo comum entre IAs;
3. instruções específicas da ferramenta;
4. regras arquiteturais e de negócio;
5. skills e scripts;
6. diário de bordo como registro histórico.

## Rotinas operacionais em avaliação

As rotinas existentes são:

- `.\scripts\bom_dia.ps1`;
- `.\scripts\salvar.ps1`;
- `.\scripts\ate_amanha.ps1`.

Há duas políticas possíveis:

### Política A - execução pela IA

A IA executa diretamente os comandos, interrompendo apenas para pedir
confirmação de operações destrutivas.

### Política B - orientação ao usuário

A IA explica o procedimento e orienta o usuário a executar o script no
terminal. Depois, a IA interpreta o resultado informado pelo usuário.

A Política B foi adotada provisoriamente no protocolo atual por reduzir o
risco de commits, pushes, restaurações e exclusões acidentais. No entanto, o
Gemini deve avaliar se isso prejudica a automação desejada e se existe uma
política híbrida mais adequada.

## Inconsistências que precisam de decisão

### Execução direta versus orientação

As skills descrevem execução direta, enquanto as instruções do Copilot
orientam o usuário a executar os scripts. É necessário escolher uma política
única ou definir claramente quando cada política se aplica.

### Backup e identificador sequencial

A regra de nomenclatura exige que SQL e JSON compartilhem uma sequência global.
O script de encerramento anteriormente calculava o próximo ID apenas pela
quantidade de arquivos JSON. É necessário definir e validar a implementação
correta para cenários em que existam quantidades diferentes de arquivos em
cada pasta.

### Credenciais

Há comandos documentados com usuário, senha e banco fixos. O Gemini deve
propor uma solução segura que funcione no ambiente local sem expor segredos
no Git, nas instruções ou no histórico de comandos.

### Restaurações destrutivas

As rotinas podem limpar o banco ou remover o schema público. Deve ser definido
o número de confirmações, a forma de identificar o backup, a validação
posterior e o comportamento em caso de falha parcial.

### Caminhos de arquivos

As instruções devem funcionar no repositório atual, em worktrees e em outras
máquinas. Caminhos absolutos como `c:\ARGUS\diario_de_bordo.md` devem ser
avaliados e, se necessário, substituídos por referências relativas.

### Documentação para outras IAs

O diário menciona `prompt_rotinas_ia.md`, mas o arquivo não está presente. O
Gemini deve dizer se esse documento deve ser recriado, substituído por
`GEMINI.md` ou incorporado a um protocolo comum.

### Codificação e duplicidades

O `AGENTS.md` precisa ser revisado quanto a caracteres de controle, classes
Bootstrap corrompidas e seções duplicadas. Essa revisão deve ocorrer somente
após o Gemini confirmar o escopo e a estratégia.

## Perguntas para o Antigravity-Gemini

Gemini, por favor, leia esta proposta e responda detalhadamente:

1. Você concorda com a divisão de papéis entre arquitetura/planejamento para
   você e implementação/validação para o Copilot? O que mudaria?
2. Qual política é mais segura para as rotinas: execução direta, orientação ao
   usuário ou uma política híbrida? Explique por rotina.
3. Qual deve ser a fonte de verdade definitiva e a precedência entre todos os
   arquivos de instruções?
4. O `diario_de_bordo.md` deve ser usado como handoff obrigatório ou você
   recomenda outro mecanismo?
5. Como devemos impedir edições concorrentes no mesmo arquivo?
6. O que deve acontecer quando as instruções de duas IAs discordarem?
7. Como você recomenda corrigir a numeração global dos backups?
8. Qual solução segura deve substituir credenciais fixas nos scripts?
9. Quais confirmações e validações são obrigatórias antes e depois de uma
   restauração?
10. O `prompt_rotinas_ia.md` deve ser recriado ou substituído?
11. Quais partes das instruções atuais devem ser consolidadas, removidas ou
    mantidas separadas?
12. Você identifica algum risco importante que não foi listado aqui?
13. Você recomenda aplicar as correções em uma única alteração ou em etapas?
14. Quais testes mínimos devem ser executados antes de considerar o protocolo
    pronto?

## Regra de encerramento desta proposta

Nenhuma decisão descrita neste documento deve ser aplicada automaticamente
como mudança definitiva nas instruções, skills ou scripts. Primeiro o Gemini
deve responder às perguntas, depois o usuário deve aprovar a estratégia e só
então as alterações operacionais devem ser implementadas e testadas.

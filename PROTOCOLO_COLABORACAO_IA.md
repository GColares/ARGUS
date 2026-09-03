# Protocolo de Colaboração entre IAs - ARGUS

## Objetivo

Este documento define como o Antigravity-Gemini, o GitHub Copilot e o Cody
devem trabalhar no mesmo repositório, preservando contexto, dados legados e
alterações feitas por cada agente.

## Fonte de verdade

Em caso de conflito, siga estritamente esta ordem de precedência:

1. **Princípios de Segurança:** Proteção contra perda de dados, vazamento de credenciais e operações destrutivas.
2. **Protocolo Base:** Este documento (`PROTOCOLO_COLABORACAO_IA.md`), que orquestra a convivência entre as IAs.
3. **Regras Arquiteturais e de Negócio:** Diretrizes em `.agents/AGENTS.md`, `.agents/rules/` e regras de domínio contidas no código.
4. **Instruções Específicas da IA:** `GEMINI.md` (arquitetura), `COPILOT.md`
   (implementação) e `.github/copilot-instructions.md` (resumo automático).
5. **Automação e Execução:** Documentação de _Skills_ (`.agents/skills/`) e os scripts reais (`scripts/`).
6. **Registro Histórico:** `diario_de_bordo.md`, que preserva o contexto temporal e decisões, mas NÃO possui poder normativo para sobrescrever regras formais acima em caso de conflito.

Se a contradição não puder ser resolvida por essa precedência, as IAs devem
parar e solicitar uma decisão ao usuário.

## Divisão de papéis

### Antigravity-Gemini

- analisar requisitos, arquitetura e regras de negócio;
- pesquisar documentação e impactos entre módulos;
- elaborar planos e alternativas;
- revisar conformidade arquitetural e de negócio;
- registrar decisões e pendências no diário.

Instruções táticas de planejamento e domínio: `GEMINI.md`.

### GitHub Copilot

- implementar alterações no worktree;
- corrigir bugs e manter compatibilidade;
- executar testes, lint e verificações já existentes;
- revisar o diff e reportar falhas;
- preparar handoff técnico.

Instruções táticas (armadilhas do repositório, checklist, o que não fazer):
`COPILOT.md`. O resumo automático do VS Code/GitHub está em
`.github/copilot-instructions.md` e aponta para esse arquivo.

### Cody

- implementação cirúrgica, higiene de código, testes de invariante e
  verificação no navegador quando a tarefa for atribuída a ele;
- não edita o mesmo arquivo que o Copilot na mesma sessão.

O usuário pode alterar essa divisão para uma tarefa específica. A atribuição
deve ser informada antes do trabalho começar.

## Regras de sincronização

1. Uma IA por arquivo por vez.
2. Sempre executar `git status` antes de editar.
3. Nunca apagar ou sobrescrever alterações de outra IA sem revisão e autorização.
4. Antes de concluir, revisar o diff e validar o comportamento.
5. Registrar no `diario_de_bordo.md` alterações relevantes, arquivos, testes,
   riscos e pendências.

O handoff deve conter objetivo, escopo, arquivos modificados, comportamento
esperado, comandos executados, resultados e próximos passos.

## Rotinas operacionais

As rotinas são executadas pelo usuário no terminal, após orientação da IA:

- `.\scripts\bom_dia.ps1`
- `.\scripts\salvar.ps1`
- `.\scripts\ate_amanha.ps1`

Isso evita que uma IA execute inadvertidamente comandos destrutivos ou
publique alterações sem revisão. A IA pode inspecionar, explicar e validar os
resultados, mas não deve declarar sucesso antes da confirmação do terminal.

Restaurações que executem `flush` ou `DROP SCHEMA` exigem confirmação explícita,
identificação do arquivo e aviso de substituição dos dados locais.

Backups devem usar `NNN_db_backup_YYYY-MM-DD_HH-MM.ext` e calcular o próximo
ID examinando conjuntamente `backups/sql/` e `backups/json/`. Credenciais
devem vir de variáveis de ambiente ou configuração segura, nunca de valores
fixos versionados.

## Análise crítica obrigatória

Mudanças complexas devem ser precedidas por uma análise Red Team contendo:

- pontos fortes;
- riscos de quebra e perda de dados legados;
- solução alternativa ou híbrida;
- perfis responsáveis pelas ações sensíveis.



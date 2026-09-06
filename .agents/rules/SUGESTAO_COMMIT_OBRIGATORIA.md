# Regra Mandatória: Sugestão Obrigatória de Mensagem de Commit

Sempre que o Antigravity-Gemini (ou qualquer IA do Squad) sugerir ao usuário:
1. A execução de rotinas de salvamento ou encerramento (.\scripts\salvar.ps1, .\scripts\ate_amanha.ps1); OU
2. Qualquer sincronização, commit ou envio de alterações para o GitHub (git commit, git push):

**É MANDATÓRIO** fornecer imediatamente no corpo da resposta uma sugestão de mensagem de commit:
- **Formato:** Clara, semântica (padrão Conventional Commits, ex: feat(...), fix(...), test(...), docs(...)) e contextualizada com os módulos tocados e o número de testes/status de homologação.
- **Apresentação:** Em destaque dentro de um bloco de código, **no ponto de cópia e cola**, para que o usuário possa colar diretamente no prompt do PowerShell quando o script solicitar.

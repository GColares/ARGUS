# Regra Mandatória: Sugestão Obrigatória de Mensagem de Commit

Sempre que o Antigravity-Gemini (ou qualquer IA do Squad) sugerir ao usuário:
1. A execução de rotinas de salvamento ou encerramento (.\scripts\salvar.ps1, .\scripts\ate_amanha.ps1); OU
2. Qualquer sincronização, commit ou envio de alterações para o GitHub (git commit, git push):

**É MANDATÓRIO E INEGOCIÁVEL** fornecer imediatamente, **NA MESMA RESPOSTA**, a sugestão da mensagem de commit:
- **Zero Turnos Extras:** É terminantemente proibido instruir a execução do script e esperar o usuário perguntar pela mensagem. A mensagem deve vir colada logo abaixo da instrução do comando.
- **Formato:** Clara, semântica (padrão Conventional Commits, ex: `feat(...)`, `fix(...)`, `docs(...)`) e contextualizada com os módulos tocados no dia.
- **Apresentação:** Em destaque dentro de um bloco de código ````text ... ````, **no ponto exato de cópia e cola** para que o usuário possa colar diretamente no prompt do PowerShell quando o script solicitar.


---
name: github-contexto-gemini
description: "Carrega o contexto compartilhado entre Gemini e Copilot antes de definir a estratégia de trabalho."
---

# Rotina de Contexto do Gemini

Quando o usuário disser "ler contexto", "preparar contexto do Gemini",
"entender nossa conversa" ou equivalente:

1. Oriente o usuário a executar `.\scripts\gemini_contexto.ps1` na raiz do
   repositório.
2. Leia integralmente os arquivos que a rotina confirmar como presentes,
   começando por `PROPOSTA_ESTRATEGIA_EQUIPE_IA.md`.
3. Responda às perguntas dirigidas ao Antigravity-Gemini nessa proposta.
4. Separe claramente recomendações, decisões que exigem aprovação e ações
   que ainda não devem ser executadas.
5. Não altere instruções, skills, scripts, banco ou histórico antes da
   aprovação explícita do usuário.

Essa rotina é somente de leitura e não substitui o `diario_de_bordo.md`.

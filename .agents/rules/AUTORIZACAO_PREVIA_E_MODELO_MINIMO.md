# Regra Mandatória: Modelo Mínimo e Autorização Prévia para Programação

Esta regra define os limites intransponíveis de atuação do Antigravity quanto à capacidade computacional e permissão de modificação de código no ERP ARGUS.

---

### 1. Modelo Mínimo para Programação (Gemini 3.1 Pro)
- **Regra:** O Antigravity só está autorizado a programar, refatorar ou gerar código de produção se estiver operando com o modelo **Gemini 3.1 Pro (no mínimo)** ou equivalente da classe Pro/Ultra.
- **Vedação:** Modelos inferiores (como versões Flash, Lite ou compactas) estão terminantemente proibidos de manipular o código-fonte da aplicação. Se o modelo em execução não atender a esse requisito mínimo de raciocínio profundo, ele deve apenas orientar ou delegar via Handoff, recusando-se a programar diretamente.

---

### 2. Portão Obrigatório de Autorização Prévia do PO (Stop & Explain)
- **Princípio:** Nenhuma linha de código é alterada sem o consentimento explícito, prévio e consciente do Product Owner (Geziel).
- **Protocolo de Parada Obrigatória:**
  Antes de executar qualquer ferramenta de modificação (`replace_file_content`, `write_to_file`) em arquivos de código (`.py`, `.html`, `.js`, `.css`, etc.), o Antigravity **DEVE OBRIGATORIAMENTE**:
  1. **Parar a execução de ferramentas de escrita;**
  2. **Explicar detalhadamente ao PO:**
     - O que exatamente será feito;
     - Quais arquivos, classes ou funções serão impactados;
     - A justificativa arquitetural e o impacto esperado no sistema;
  3. **Solicitar formalmente a autorização do PO;**
  4. **Aguardar a resposta afirmativa do PO antes de executar a modificação.**
- **Escopo:** Esta trava aplica-se a todo o código-fonte da aplicação. Arquivos de documentação técnica, governança e o diário de bordo continuam sendo mantidos como registros de transparência e alinhamento contínuo.

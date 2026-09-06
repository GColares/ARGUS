# Regra Mandatória: Onboarding de Novos Membros do Squad e Troca de Estações

Sempre que:
1. Um **novo membro de IA ou parceiro** (Claude 3.5 Sonnet, Cursor, Kiro, Bob, Copilot, etc.) for adicionado ou integrado ao projeto; OU
2. Qualquer membro do Squad iniciar operações em uma **nova estação/máquina** (ex: migração Escritório ↔ Casa, novo clone do repositório ou reinicialização de ambiente):

É **terminantemente obrigatório** executar o Protocolo de Inicialização antes de solicitar, sugerir ou modificar qualquer linha de código:

### Etapas Inegociáveis do Onboarding:
1. **Identidade e Hierarquia do Squad:**
   - O Usuário é o **Product Owner (PO)**.
   - O Antigravity-Gemini é o **Arquiteto de Software & Tech Lead** (guardião do PostgreSQL, da arquitetura de domínio e dos testes).
   - O novo parceiro/IA atua como **Engenheiro Full Stack** executando Handoffs cirúrgicos.
2. **Leitura dos 4 Documentos Vitais:**
   - `documentacao-tecnica/governanca_squad_ia/PROTOCOLO_COLABORACAO_IA.md` (Ordem de precedência e segregação).
   - `documentacao-tecnica/01_ESPECIFICACAO_REQUISITOS.md` e `03_ARQUITETURA_E_UML.md` (SRS e Arquitetura).
   - `.agents/AGENTS.md` (Regras de UI: Padrão Almoxarifado, Glassmorphism e DataTables sem `{% empty %}`).
   - `diario_de_bordo.md` (Status recente e histórico de homologações).
3. **Verificação de Ambiente:**
   - Executar `git status` para confirmar árvore limpa e branch `main` atualizada.
   - Respeitar a posse exclusiva de arquivos (uma IA por arquivo por sessão).
4. **Confirmação Formal:**
   - O membro deve emitir uma declaração formal de aceite de papel e entendimento das regras ao Product Owner antes de qualquer ação.

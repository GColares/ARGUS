# Documentação Técnica do Sistema ARGUS

**ERP Institucional do Polo de Inovação IFAM**  
*Unidade EMBRAPII de Automação Industrial e Tecnologias Sustentáveis*

Bem-vindo ao repositório oficial de engenharia de software e arquitetura do **ARGUS**.  
Esta pasta contém os artefatos formais exigidos para auditoria, governança, credenciamento em órgãos de fomento (EMBRAPII, SUFRAMA) e orientações técnicas de desenvolvimento.

---

## 📚 Estrutura dos Artefatos Técnicos

### 1. Documentos Oficiais de Engenharia de Software
| Documento | Descrição | Conteúdo Principal |
|---|---|---|
| [01_ESPECIFICACAO_REQUISITOS.md](01_ESPECIFICACAO_REQUISITOS.md) | **SRS (Software Requirements Specification)** | Requisitos Funcionais (RF), Não-Funcionais (RNF), Regras de Negócio Legais (RN) e Matriz de Rastreabilidade. |
| [02_MER_BANCO_DE_DADOS.md](02_MER_BANCO_DE_DADOS.md) | **Modelo Entidade-Relacionamento** | Diagrama ERD visual (Mermaid), dicionário de tabelas, chaves primárias/estrangeiras e integridade referencial. |
| [03_ARQUITETURA_E_UML.md](03_ARQUITETURA_E_UML.md) | **Arquitetura de Software & Diagramas UML** | Diagrama de Classes, Diagramas de Máquinas de Estados (Ciclo PDI e Parcela) e Diagramas de Sequência (Atesto SIAPE e Liquidação FAEPI). |
| [04_MATRIZ_RBAC_E_GOVERNANCA.md](04_MATRIZ_RBAC_E_GOVERNANCA.md) | **Matriz RBAC & Governança Institucional** | Perfis de acesso, matriz RACI de operações críticas e regras de Segregação de Funções (SoD). |

---

### 2. Subpastas de Suporte e Governança

* **[`der_diagramas/`](der_diagramas/)**: Diagramas de Entidade-Relacionamento (DER) visuais exportados nos formatos SVG, PNG, PDF e HTML interativo.
* **[`governanca_squad_ia/`](governanca_squad_ia/)**: Governança operacional do Squad de Inteligência Artificial:
  - [`PROTOCOLO_COLABORACAO_IA.md`](governanca_squad_ia/PROTOCOLO_COLABORACAO_IA.md): Protocolo mestre de convivência, regras de ouro, precedência e divisão de papéis.
  - [`PROPOSTA_ESTRATEGIA_EQUIPE_IA.md`](governanca_squad_ia/PROPOSTA_ESTRATEGIA_EQUIPE_IA.md): Estratégia de integração contínua do squad.
  - [`manuais_agentes/`](governanca_squad_ia/manuais_agentes/): Manuais individuais de cada IA do time (`GEMINI.md`, `COPILOT.md`, `KIRO.md`, `BOB.md`, `DEVIN.md`).

---

## 🛠️ Como Visualizar os Diagramas
Todos os diagramas deste repositório foram construídos na sintaxe nativa **Mermaid**. Eles são renderizados automaticamente no GitHub, GitLab, VS Code (com extensão Markdown Preview Mermaid Support) ou diretamente em ferramentas online como [mermaid.live](https://mermaid.live).


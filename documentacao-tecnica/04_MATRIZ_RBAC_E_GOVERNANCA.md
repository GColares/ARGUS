# Matriz RBAC e Catálogo de Governança — ARGUS

**Sistema Integrado de Gestão do Polo de Inovação IFAM**  
**Versão:** 1.0  
**Data:** 2026-09-04  
**Responsável:** Antigravity-Gemini (Arquiteto de Software & Guardião do Domínio)

---

## 1. Princípios de Governança e Alçadas

A governança do ARGUS baseia-se nos regulamentos oficiais do Instituto Federal do Amazonas (IFAM) e do Polo de Inovação:
1. **Regimento Interno do Polo de Inovação:** Define as competências da Diretoria Geral, Coordenações de PDI, Administrativa e Comitês Técnicos.
2. **Regulamento de Concessão de Bolsas:** Estabelece os critérios de elegibilidade, carga horária e prestação de contas dos bolsistas.
3. **Regulamento do Fundo de Reserva:** Normatiza a retenção e aplicação do overhead institucional.
4. **Segregação de Funções (SoD):** Ações financeiras, técnicas e de fiscalização são estritamente separadas para atender às recomendações do TCU e CGU.

---

## 2. Catálogo de Perfis de Usuário (Roles)

| Perfil | Descrição & Competências Institucionais | Alçada Legal / Normativa |
|---|---|---|
| **Reitor / Alta Gestão** | Representante máximo do IFAM. Assina Acordos-Mestre de Cooperação e homologa parcerias estratégicas. | Estatuto do IFAM |
| **Diretor Geral do Polo** | Gestor executivo da Unidade EMBRAPII. Aprova a submissão de propostas, formaliza Termos de Parceria e autoriza orçamentos. | Regimento Interno do Polo |
| **Coordenador de PD&I** | Planeja as linhas de pesquisa (Programas), avalia mérito técnico e compatibilidade com o credenciamento EMBRAPII. | Regimento Interno do Polo |
| **Coordenador Admin-Financeiro** | Responsável pelo controle de rubricas orçamentárias, conformidade com tetos (terceiros 30%, overhead 15/20%) e prestação de contas. | Regimento Interno do Polo |
| **Coordenador de Projeto** | Pesquisador responsável pela condução metodológica, gestão da equipe, validação de entregas físicas e aprovação de RAs. | Regulamento de Pesquisa |
| **Servidor Efetivo (SIAPE)** | Servidor público estável com fé pública. Responsável pelo atesto formal de cumprimento de atividades dos bolsistas. | Lei 8.112/1990 |
| **Bolsista / Pesquisador** | Membro executor das atividades laboratoriais/técnicas. Submete mensalmente o Relatório de Atividades circunstanciado. | Regulamento de Bolsas |
| **Fundação de Apoio (FAEPI)** | Interveniente financeira. Efetua a liquidação e baixa em lote das parcelas de bolsas, transferências e pagamentos a fornecedores. | Lei 8.958/1994 |
| **Administrador do Sistema** | Responsável técnico pela infraestrutura de TI, auditoria e autoridade **estrita e exclusiva** para vincular contas `User` a `PessoaFisica`. | Governança de TI / LGPD |

---

## 3. Matriz de Permissões e Operações Críticas

| Operação Crítica do Sistema | Reitor | Diretor Polo | Coord. PDI | Coord. Fin. | Coord. Projeto | Servidor SIAPE | Bolsista | FAEPI | Admin |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Criar / Editar Termo de Cooperação** | R | A | C | C | - | - | - | - | - |
| **Criar / Editar Programa de Fomento** | I | A | R | C | - | - | - | - | - |
| **Formalizar Termo de Parceria (Hélice)** | I | A | C | C | C | - | - | C | - |
| **Criar Intenção de Projeto (Wizard)** | - | - | R | - | R | - | - | - | - |
| **Congelar Plano de Trabalho (Execução)**| - | A | C | C | R | - | - | - | - |
| **Aprovar Retificação / Aditivo de Plano**| - | A | C | C | R | - | - | - | - |
| **Submeter Relatório de Atividade (RA)**| - | - | - | - | - | - | R | - | - |
| **Atestar RA com Carimbo SIAPE** | - | - | - | - | - | R (SoD) | - | - | - |
| **Liquidar / Baixar Folha de Bolsas** | - | - | - | I | - | - | - | R | - |
| **Vincular Credencial User a PessoaFisica**| - | - | - | - | - | - | - | - | R |
| **Cadastrar / Inativar Espaço Físico** | - | - | - | - | - | - | - | - | R |

**Legenda:**
* **R (Responsável):** Quem executa diretamente a operação no sistema.
* **A (Aprovador):** Quem detém a alçada final para autorizar ou assinar.
* **C (Consultado):** Quem opina ou fornece subsídios técnicos/financeiros.
* **I (Informado):** Notificado pelo sistema sobre a conclusão da ação.
* **- (Sem Acesso):** Bloqueado por restrição de perfil ou permissão.

---

## 4. Regras Estritas de Segregação de Funções (SoD)

1. **Auto-atesto Proibido:** O sistema impede que o bolsista beneficiário da bolsa execute a view `atestar_relatorio()`, ainda que ele possua perfil de servidor público efetivo ativo.
2. **Segregação entre Atesto e Pagamento:** Servidores que atestam a execução técnica das atividades não possuem permissão para liquidar ou movimentar contas bancárias na view `liquidar_folha_lote()`, prerrogativa exclusiva da Fundação de Apoio (FAEPI).
3. **Imparcialidade na Concessão de Bolsas:** Coordenadores de Projeto não podem figurar como bolsistas de sua própria cota orçamentária.

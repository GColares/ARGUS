# Especificação de Requisitos de Software (SRS) — ARGUS

**Sistema Integrado de Gestão do Polo de Inovação IFAM**  
*Unidade EMBRAPII de Automação Industrial e Tecnologias Sustentáveis*  
**Versão:** 1.0  
**Data:** 2026-09-04  
**Responsável:** Antigravity-Gemini (Arquiteto de Software & Guardião do Domínio)

---

## 1. Introdução

### 1.1 Objetivo do Documento
Este documento formaliza a Especificação de Requisitos de Software do sistema **ARGUS**, detalhando os requisitos funcionais, requisitos não-funcionais, regras de negócio regulatórias e matriz de rastreabilidade. Serve como fonte primária para desenvolvimento, auditorias de órgãos de controle (TCU, CGU, MEC) e credenciamento perante agências de fomento (EMBRAPII, SUFRAMA, FAPEAM).

### 1.2 Escopo do Sistema
O **ARGUS** é o ERP institucional do Polo de Inovação do Instituto Federal do Amazonas (IFAM), projetado para gerenciar de ponta a ponta o ciclo de vida da pesquisa aplicada, inovação tecnológica e cooperação com o setor produtivo:
1. **Governança de Parcerias:** Instrumentos jurídicos da Lei de Inovação (Lei 10.973/2004 e Decreto 9.283/2018).
2. **Projetos de PD&I:** Gestão de planos de trabalho, macroentregas e atividades físicas.
3. **Execução Orçamentária e Financeira:** Aportes EMBRAPII, empresas e fundações de apoio, rubricas legais e desembolsos.
4. **Gestão de Bolsas e Capital Humano:** Concessão, atesto por servidores públicos efetivos (SIAPE) e liquidação bancária.
5. **Infraestrutura e Laboratórios:** Gestão de espaços físicos, ambientes inteligentes e ordens de serviço.

---

## 2. Requisitos Funcionais (RF)

### 2.1 Módulo: Governança de Parcerias e Fomento Macro
* **RF-01 — Gestão de Termos de Cooperação (Guarda-Chuva):** O sistema deve permitir o cadastro, visualização, edição e arquivamento de Termos de Cooperação técnica/financeira celebrados entre o IFAM e parceiros institucionais.
* **RF-02 — Gestão de Programas de Fomento:** O sistema deve gerenciar Programas vinculados a Termos de Cooperação (relação 1:N), subdividindo rodadas temáticas ou editais (ex: Programa de Desenvolvimento de Competências - PDC).
* **RF-03 — Gestão de Termos de Parceria (Hélice Tríplice):** O sistema deve registrar o instrumento jurídico específico de cada projeto de PD&I, vinculando obrigatoriamente três figuras jurídicas especializadas: Concedente (`EmpresaParceira`), Convenente (`ICT`) e Interveniente Administrativo-Financeiro (`FundacaoApoio`).
* **RF-04 — Separação de Nascimentos (Projeto vs. Termo):** O sistema deve permitir que pesquisadores criem intenções de projetos e planos de trabalho no Wizard de forma assíncrona, vinculando posteriormente o Termo de Parceria registrado pela Coordenação de Contratos (SIPAC).

### 2.2 Módulo: Projetos de PD&I e Planos de Trabalho
* **RF-05 — Ciclo de Vida do Projeto (Máquina de Estados):** O sistema deve controlar a transição de fases do projeto: `PROSPECCAO` -> `EXECUCAO` -> `PRESTACAO_CONTAS` -> `ENCERRADO` (ou `CANCELADO`).
* **RF-06 — Versionamento e Congelamento do Plano de Trabalho:** O sistema deve manter histórico de versões do Plano de Trabalho (`RASCUNHO`, `CONGELADO_VIGENTE`, `RETIFICADO`, `ENCERRADO`). Ao iniciar a fase de `EXECUCAO`, o escopo técnico e financeiro do plano ativo deve ser integralmente congelado.
* **RF-07 — Planejamento Físico em Macroentregas:** O sistema deve decompor o projeto em Macroentregas orientadas aos níveis TRL 3 a 6 (Technology Readiness Level), vinculando atividades físicas e produtos tecnológicos.
* **RF-08 — Painel Central Orçamentário (Aba 3):** O sistema deve consolidar o orçamento do projeto em quatro visões: (1) Aportes Globais (Empresa, EMBRAPII, SEBRAE/ICT), (2) Rubricas Orçamentárias, (3) Cronograma de Desembolso e (4) Contas Bancárias vinculadas.

### 2.3 Módulo: Gestão de Bolsas e Execução Financeira
* **RF-09 — Gestão de Cotas e Termos de Concessão de Bolsas:** O sistema deve controlar cotas orçadas no Plano de Trabalho e gerar Termos de Concessão de Bolsa individuais para estudantes, servidores e pesquisadores externos.
* **RF-10 — Prestação de Contas Mensal (Relatório de Atividades - RA):** Todo bolsista ativo deve submeter mensalmente um Relatório de Atividades circunstanciado vinculado à respectiva parcela de pagamento.
* **RF-11 — Atesto de Frequência e Entrega (SIAPE Obrigatório):** O sistema deve exigir a homologação do RA por um servidor público efetivo com matrícula SIAPE válida, aplicando trava de Segregação de Funções (SoD) para impedir auto-atesto.
* **RF-12 — Liquidação e Baixa em Lote de Parcelas:** A Fundação de Apoio deve dispor de interface para liquidar em lote as parcelas com RA aprovado, informando data de pagamento, conta bancária de débito e upload do comprovante consolidado.

### 2.4 Módulo: Identidade e Infraestrutura Física
* **RF-13 — Identidade Canônica de Pessoas Físicas (Party-Role):** O sistema deve manter um cadastro único para cada cidadão (`PessoaFisica`) sob governança de LGPD, associando múltiplos papéis dinâmicos (`PerfilServidor`, `PerfilBolsista`, `PerfilAluno`, `DadoBancario`).
* **RF-14 — Gestão de Espaços e Ambientes (Composite Pattern):** O sistema deve mapear a infraestrutura predial e laboratorial do Polo em árvore hierárquica (`ambiente_pai`), permitindo alocar equipamentos e ordens de serviço no nível mais granular da localização física.

---

## 3. Requisitos Não-Funcionais (RNF)

* **RNF-01 — Integridade Transacional (ACID):** Todas as operações compostas (finalização do Wizard de Projetos, atesto de relatórios e baixa em lote de folhas de pagamento) devem ser executadas sob transações atômicas (`transaction.atomic`). Em caso de falha em qualquer item, rollback total é obrigatório.
* **RNF-02 — Privacidade e Conformidade LGPD:** 
  - Dados sensíveis e bancários (`DadoBancario`) devem ser segregados e visíveis apenas a perfis autorizados (Financeiro/Admin).
  - A exclusão de pessoas físicas com histórico financeiro/acadêmico deve operar via anonimização irreversível (*crypto-shredding* de CPF e dados de contato), preservando chaves estrangeiras para prestação de contas.
* **RNF-03 — Fidelidade de Interface (Padrão Almoxarifado):**
  - Telas de listagem devem seguir a anatomia: Breadcrumbs -> Link Voltar dinâmico (`javascript:history.back()`) -> Row de Título/Ações com Badges -> Gaveta colapsável de Filtros -> Tabela padronizada.
  - Cabeçalhos de tabelas (`<th>`) e colunas de ações devem ser estritamente centralizados (`text-center`).
  - Tabelas processadas por DataTables client-side nunca devem conter a tag `{% empty %}` com `colspan` no `<tbody>`.
* **RNF-04 — Design Visual & Cores Semânticas:**
  - Telas de dashboard e cartões devem utilizar Glassmorphism com `backdrop-filter: blur(10px)`.
  - Cores devem utilizar estritamente variáveis e utilitários semânticos do Bootstrap (`var(--bs-primary)`, `rgba(var(--bs-success-rgb), 0.1)`). É proibido o uso de valores HEX fixos no CSS.
* **RNF-05 — Rastreabilidade e Auditoria Contínua:** Todos os cadastros mestres e tabelas paramétricas devem incorporar histórico de alterações (`django-simple-history`), registrando autor, data/hora e delta da modificação.
* **RNF-06 — Segurança no Vínculo de Contas de Acesso:** A vinculação entre credenciais de login (`auth.User`) e a entidade canônica `PessoaFisica` é de competência restrita e exclusiva do perfil **Administrador do Sistema**.

---

## 4. Regras de Negócio e Invariantes Legais (RN)

| ID | Regra de Negócio / Invariante | Base Legal / Regulamentar |
|---|---|---|
| **RN-01** | **Exclusão de ICT Executora como Concedente:** A instituição que figura como Convenente Executora (`is_executora=True`) jamais pode ser selecionada como Concedente financeira da mesma parceria. | Lei 10.973/2004, Art. 9º |
| **RN-02** | **Aporte Mínimo EMBRAPII:** Recursos aportados pela EMBRAPII devem compor no mínimo 10% e no máximo 33% do valor total do projeto de inovação. | Manual de Operações EMBRAPII |
| **RN-03** | **Aporte Mínimo da Empresa Concedente:** A empresa parceira deve aportar no mínimo 10% financeiro (ou 50% em casos de cumprimento de obrigação legal de P&D / Lei de Informática). | Portaria SUFRAMA 9835/2022 |
| **RN-04** | **Teto de Serviços de Terceiros:** A soma das despesas com Serviços de Terceiros (Pessoa Física + Pessoa Jurídica) não pode ultrapassar **30%** do valor global do projeto. | Manual EMBRAPII / SUFRAMA |
| **RN-05** | **Teto e Fonte do Suporte Operacional (Overhead):** A taxa de suporte operacional é limitada a **15%** (EMBRAPII) ou **20%** (SUFRAMA). É vedado o custeio de overhead com recursos públicos EMBRAPII; deve ser integralmente suportado pela Empresa Concedente ou contrapartida da Unidade. | Portaria SUFRAMA 9835/2022 |
| **RN-06** | **Vedação de Capital e Equipamentos na EMBRAPII:** Recursos de subvenção EMBRAPII não podem ser alocados para aquisição de Bens de Capital, Máquinas, Veículos ou Obras Civis (exclusividade de custeio/recursos humanos). | Manual de Operações EMBRAPII |
| **RN-07** | **Não-Sobreposição Temporal de Macroentregas:** O planejamento físico não permite sobreposição cronológica entre macroentregas subsequentes: `Data_Inicio(Macroentrega N) >= Data_Fim(Macroentrega N-1)`. | Governança EMBRAPII |
| **RN-08** | **Atesto Obrigatório por Servidor Efetivo SIAPE:** Nenhum bolsista pode ser pago sem homologação expressa de servidor público efetivo estável no SIAPE. | Lei 8.112/1990 e Acórdãos TCU |
| **RN-09** | **Segregação de Funções no Atesto (SoD):** O bolsista que submete o Relatório de Atividades está impedido de atestar o próprio documento, ainda que possua matrícula SIAPE. O atesto deve ser realizado pelo Coordenador do Projeto ou fiscal designado. | Princípio da Segregação de Funções / TCU |
| **RN-10** | **Congelamento do Escopo em Execução:** Uma vez que o projeto atinge a fase de `EXECUCAO`, o Plano de Trabalho não aceita edições diretas. Qualquer alteração deve ocorrer mediante formalização de Termo Aditivo ou Plano Retificado. | Processo Administrativo Federal |
| **RN-11** | **Herança Estrita de Fomento (Termo > Programa > Projeto):** Nenhum Projeto PDI sob fomento guarda-chuva pode ser vinculado diretamente a um Termo de Cooperação. O vínculo deve apontar obrigatoriamente para a subclasse `Programa`. | Diretriz Arquitetural ARGUS |
| **RN-12** | **Impedimento de Duplicidade de Bolsa:** O sistema não permite que um mesmo indivíduo (`PessoaFisica`) receba mais de uma bolsa de mesma modalidade no mesmo período de vigência sem justificativa legal aprovada. | Regulamento de Concessão de Bolsas IFAM |

---

## 5. Matriz de Rastreabilidade

| Requisito Funcional | Regras de Negócio Vinculadas | Módulo Django | Atores Responsáveis |
|---|---|---|---|
| **RF-01, RF-02** | RN-11 | `cadastros` | Gestor de PDI, NIT, Diretor |
| **RF-03, RF-04** | RN-01, RN-11 | `cadastros` | Coordenação de Contratos, Pesquisador |
| **RF-05, RF-06** | RN-07, RN-10 | `cadastros`, `gestao_projetos` | Coordenador de Projeto, Gestor de PDI |
| **RF-07, RF-08** | RN-02, RN-03, RN-04, RN-05, RN-06 | `gestao_projetos` | Coordenador de Projeto, Núcleo Financeiro |
| **RF-09, RF-10** | RN-12 | `gestao_projetos` | Coordenador de Projeto, Bolsista |
| **RF-11** | RN-08, RN-09 | `gestao_projetos` | Servidor Efetivo SIAPE, Coordenador |
| **RF-12** | RN-08, RN-09 | `gestao_projetos` | Fundação de Apoio (FAEPI) |
| **RF-13** | RNF-02, RNF-06 | `cadastros` | Administrador do Sistema |
| **RF-14** | RNF-05 | `espacos` | Gestor de Infraestrutura / Laboratórios |

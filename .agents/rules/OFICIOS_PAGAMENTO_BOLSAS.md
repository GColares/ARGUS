# Diretriz Operacional: Geração de Ofícios de Pagamento de Bolsas

Esta regra estabelece o fluxo canônico, a fonte de dados e a segregação de responsabilidades na elaboração dos ofícios de solicitação de pagamento de bolsas junto à Fundação de Apoio (FAEPI).

---

### 1. Escopo de Atuação e Segregação de Ofícios

1. **Ofício do Coordenador do Projeto:**
   - O ofício de pagamento da bolsa do Coordenador é elaborado por ele próprio e submetido diretamente à assinatura da Direção-Geral (DG / Diretor do Polo).
   - **Regra Geral:** O Squad/Agente **NÃO** confecciona o ofício de pagamento do coordenador, salvo solicitação e autorização excepcional e expressa do PO.

2. **Ofício da Equipe (Demais Bolsistas):**
   - É responsabilidade primordial do nosso fluxo de trabalho cuidar da instrução, consolidação e emissão dos ofícios de pagamento de **todos os demais bolsistas** (pesquisadores, técnicos, desenvolvedores, graduandos e apoio administrativo).
   - O signatário requisitante desse ofício perante a FAEPI é o Coordenador do Projeto.

---

### 2. Fonte Canônica de Dados

- **Arquivo Mestre:** Todas as informações financeiras, contratuais e cadastrais necessárias para a elaboração dos ofícios de pagamento residem estritamente em:
  `gestao_projetos/modelos/relatorios-atividades-cabecalhos.xlsx`
- **Extração de Informações:**
  - Aba de trabalho: `relatorios-de-atividade`
  - Filtro de parcelas da competência: registros com coluna `execucao_financeira = 'a pagar'` (ou filtrados pelo período/mês de referência).
  - Rateio por Fontes e Contas Bancárias: agrupamento conforme as contas informadas na coluna `projeto_conta` (ex: Conta Empresa `15334-6`, Conta SEBRAE `15335-4`, Conta EMBRAPII `15338-9`).
  - Atributos obrigatórios: Nome, CPF, Termo de Bolsa, Modalidade, Atribuição/Função, Período do Relatório, Carga Horária, Número/Total da Parcela e Valor Total (R$).

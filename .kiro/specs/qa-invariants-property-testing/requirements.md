# Requisitos: Property-Testing de Invariantes Legais e Financeiras

## 1. Contexto e Objetivo
O ARGUS gerencia projetos de PD&I complexos com estrita subordinação à Lei nº 8.112/90 (Regime Jurídico Único dos Servidores Públicos Civis da União), Portaria SUFRAMA nº 9835/2022 e Manual de Operações da EMBRAPII.

O objetivo desta especificação é estabelecer uma suíte avançada de **Property-Based Testing** (testes baseados em propriedades e geração generativa de dados) para estressar e blindar os algoritmos críticos do sistema contra casos limítrofes (edge cases) e combinações não lineares.

## 2. Requisitos Funcionais (EARS Notation)

### 2.1. Invariante da Unicidade do Exercício (Lei 8.112/90, Art. 38)
- **REQ-QA-001 (Unicidade de Autoridade):** QUANDO uma consulta por autoridade em exercício (`FuncaoInstitucional.obter_responsavel_em_exercicio`) for disparada para qualquer data arbitrária $D$, O SISTEMA DEVE retornar exatamente UMA pessoa física em exercício para aquela função, ou `None` se todos os designados estiverem afastados.
- **REQ-QA-002 (Hierarquia Estrita de Suplência):** ENQUANTO o titular (prioridade 0) não possuir afastamento ativo na data $D$, O SISTEMA DEVE sempre selecionar o titular, ignorando a disponibilidade dos substitutos.
- **REQ-QA-003 (Cascata Automática de Suplência):** SE o titular estiver afastado e o 1º Substituto estiver ativo na data $D$, O SISTEMA DEVE selecionar o 1º Substituto com o sufixo "Substituto" e a portaria correspondente.
- **REQ-QA-004 (Transição sem Buracos Temporais):** DADO um histórico com múltiplos períodos de férias e licenças intercaladas entre titular, 1º e 2º substitutos, O SISTEMA DEVE resolver a autoridade correta em cada dia da linha do tempo sem ambiguidades de sobreposição.

### 2.2. Invariante das Travas Orçamentárias e Rubricas (SUFRAMA & EMBRAPII)
- **REQ-QA-005 (Teto de Terceiros):** EM QUALQUER projeto PDI, a soma combinada de Serviços de Terceiros (PF + PJ) NUNCA DEVE ultrapassar 30% do valor total do projeto.
- **REQ-QA-006 (Teto e Fonte do Overhead):** O Suporte Operacional / Overhead não pode ultrapassar 15% (EMBRAPII) ou 20% (SUFRAMA) e DEVE ser aportado exclusivamente pela Empresa parceira ou Contrapartida da Unidade (nunca com recursos EMBRAPII).
- **REQ-QA-007 (Aporte Mínimo da Empresa):** A Empresa parceira DEVE aportar no mínimo 10% (recursos financeiros) ou 50% em casos de obrigação legal de P&D (Lei de Informática).

## 3. Critérios de Aceite
1. Execução de testes de propriedade gerando centenas de combinações aleatórias de datas, afastamentos e orçamentos.
2. Taxa de sucesso de 100% nas propriedades declaradas.
3. Zero regressão nos 36 testes existentes de `cadastros` e `gestao_projetos`.

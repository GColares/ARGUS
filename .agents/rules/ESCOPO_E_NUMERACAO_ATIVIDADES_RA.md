# Diretriz Canônica: Escopo e Numeração de Atividades no Relatório de Atividades (RA)

## 1. Princípio Universal Multi-Projeto (Escopo por Vínculo de Cota)
O ARGUS é uma plataforma que gerencia múltiplos projetos PDI, cada qual com seu próprio Plano de Trabalho (PT), quantitativo de atividades, cronograma e estrutura de equipe. O escopo de cada Relatório de Atividades (RA) deve respeitar estritamente a modelagem de dados do sistema:

1. **Coordenador do Projeto:**
   - Possui **escopo integral**: contempla a totalidade das atividades do Plano de Trabalho do respectivo projeto (da Atividade 1 à N-ésima).
2. **Demais Bolsistas e Colaboradores:**
   - Possuem **escopo delimitado**: contemplam estritamente o conjunto de atividades vinculadas à sua cota de bolsa / papel no Plano de Trabalho (`CotaBolsaPT.atividades_vinculadas` ou pelo papel atribuído no projeto).
   - É vedado incluir em um RA atividades que fujam às atribuições e competências do papel contratado (ex: atividades de pesquisa técnica em relatórios de apoio administrativo, ou vice-versa).

---

## 2. Regra Universal de Numeração Sequencial Contextual (1..N)

1. **Início Estrito em 1 (1..N):**
   - Independentemente de quais sejam os índices absolutos das atividades no Plano de Trabalho geral do projeto (ex: bolsista alocado nas atividades originais nº 3, nº 7 e nº 11 do PT), no Relatório de Atividades (RA) desse bolsista (tanto no espelho web HTML quanto nos arquivos DOCX/PDF gerados) as atividades atribuídas a ele devem ser **numeradas de forma contínua e sequencial a partir de 1 em diante (1, 2, 3...)**.
   - As respectivas subtarefas/itens de atividade acompanham a nova numeração (ex: tarefas da 1ª atividade atribuída tornam-se 1.1, 1.2...; tarefas da 2ª atividade tornam-se 2.1, 2.2...).
2. **Vedação a Rótulos de Referência Cruzada:**
   - É **terminantemente proibido** inserir notas, prefixos ou anotações de referência cruzada ao número mestre do Plano de Trabalho (ex: não utilizar *"Ref. Atividade 7 do PT"*). A apresentação ao bolsista deve ser pura, limpa e sequencial.
3. **Integridade Estrutural no Banco de Dados:**
   - No banco de dados (`cadastros.AtividadePlanoAcao` e `gestao_projetos.ItemAtividade`), a chave primária e o campo `numero` do Plano de Trabalho mestre permanecem rigorosamente inalterados.
   - A renumeração sequencial é uma transformação aplicada **exclusivamente na camada de apresentação e serialização (View / Template / Renderizador DOCX)**.

---

## 3. Estudo de Caso de Referência (Projeto Bio Caroço)

Para fins didáticos e de validação, toma-se como referência a estrutura do projeto Bio Caroço:
* **Estrutura no Plano de Trabalho Geral:** 8 atividades no total (Atividade 1 = Gestão Administrativa, Financeira e Operacional; Atividades 2 a 8 = Pacotes Técnicos de P&D).
* **RA do Coordenador do Projeto:** Consolida todas as 8 atividades do projeto (1 a 8).
* **RA do Auxiliar Administrativo:** Contempla exclusivamente a Atividade 1 (Apoio à Gestão Administrativa, Financeira e Operacional), numerada como **1**.
* **RA da Equipe Técnica de P&D (Pesquisadores, Desenvolvedores, Analistas):** Contempla as atividades técnicas vinculadas (antigas Atividades 2 a 8 do PT), numeradas de forma limpa e sequencial de **1 a 7**.

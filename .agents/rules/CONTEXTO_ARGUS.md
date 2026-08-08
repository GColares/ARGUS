# Contexto de Negócio e Estrutura do Sistema ARGUS

Estas diretrizes servem como base de conhecimento para que o Antigravity (IA) compreenda a proposta central, o público-alvo e a arquitetura de negócios do sistema ARGUS. Utilize essas informações para tomar decisões de design, sugerir integrações e entender os fluxos de trabalho do usuário.

## 1. A Proposta Central do ARGUS
O ARGUS é um **Sistema de Gestão Integrada (ERP Institucional)** projetado para apoiar a administração pública. Sua missão é modernizar, unificar e automatizar nichos de processos como:
- Controle de Ativos e Patrimônio
- Gestão de Projetos e Bolsistas
- Manutenção da Infraestrutura do Campus (Central de Serviços)
- Fluxos de Almoxarifado
- Cadastros Base e Institucionais

Ele não é um sistema acadêmico focado apenas no ensino, mas sim uma ferramenta robusta para a **gestão dos bastidores da instituição** (recursos humanos, físicos e financeiros).

## 2. Público-Alvo e Perfis de Usuário
O ARGUS é operado por pessoas inseridas em processos específicos da instituição, abrangendo:
- **Servidores Públicos e Administrativos:** Operam as aprovações, gestão de contratos e orçamentos.
- **Gestores de Manutenção e Infraestrutura:** Usam a Central de Serviços para monitorar Prédios, Salas e Ativos Prediais.
- **Coordenadores de Projetos:** Gerenciam cronogramas, planos de ação e distribuição de cotas para bolsistas.
- **Técnicos e Operadores:** Equipes de ponta (ex: Almoxarifado, Equipes de Manutenção técnica) que executam o trabalho de chão de fábrica (separação de itens, consertos físicos).
*(Nota para a IA: O design das telas deve sempre considerar que o usuário pode variar desde um gestor analisando relatórios executivos até um técnico utilizando o sistema para dar baixa rápida em um estoque).*

## 3. Integração e Ecossistema dos Módulos
A arquitetura de negócios do ARGUS baseia-se em um **ecossistema interdependente**. Os módulos não devem ser tratados como ilhas isoladas. A IA deve sempre buscar aproveitar as integrações entre eles:
- **Módulo `cadastros`:** É a espinha dorsal. Fornece Pessoas (Servidores/Bolsistas), Fornecedores, Contas Bancárias e Parâmetros Base.
- **Módulo `patrimonio` e `incorporacao`:** Gerenciam os bens físicos, suas notas fiscais e tombamentos.
- **Módulo `almoxarifado`:** Controla os insumos consumíveis.
- **Módulo `central_servicos`:** Consome bens do `patrimonio` (como Ativos Prediais que precisam de manutenção) e consome itens do `almoxarifado` (ex: lâmpadas e parafusos que sofrem baixa após uma Ordem de Serviço concluída).
- **Módulo `gestao_projetos`:** Consome os `cadastros` para formar equipes e gerenciar orçamentos/planos de trabalho.

## 4. Como a IA deve se comportar perante esta regra
Sempre que o usuário solicitar o desenvolvimento de uma nova funcionalidade, a IA deve automaticamente consultar esta estrutura e perguntar a si mesma:
- *"Esta nova tabela não deveria estar vinculada ao módulo `cadastros`?"*
- *"Se estamos criando uma funcionalidade de consumo, ela vai refletir no saldo do `almoxarifado`?"*
- *"Esta tela precisa de uma visualização mais gerencial ou mais operacional?"*

Compreender o ARGUS é compreender a integração do campus.

# Arquitetura de Software e Diagramas UML — ARGUS

**Sistema Integrado de Gestão do Polo de Inovação IFAM**  
**Versão:** 1.0  
**Data:** 2026-09-04  
**Responsável:** Antigravity-Gemini (Arquiteto de Software & Guardião do Domínio)

---

## 1. Visão Geral da Arquitetura

O **ARGUS** adota o padrão arquitetural **MVT (Model-View-Template)** do Django sobre o **PostgreSQL**, estruturado segundo os princípios de **Domain-Driven Design (DDD)** para refletir a governança da Lei 10.973/2004 e as diretrizes EMBRAPII/SUFRAMA.

```mermaid
flowchart TB
    subgraph Apresentacao["Camada de Apresentação (Templates & UI)"]
        UI_List["Listas Mestras (Padrão Almoxarifado)"]
        UI_Dash["Dashboards (Glassmorphism + Bootstrap)"]
        UI_Wiz["Wizards Compostos (Draft/Sessão Offline-First)"]
    end

    subgraph Controle["Camada de Aplicação e Controle (Views & URLs)"]
        CBV["Class-Based Views (CRUD Padronizado)"]
        FBV_Trava["Function Views com Travas de Segurança (@servidor_efetivo_required)"]
        Atomic["Transações Atômicas (transaction.atomic)"]
    end

    subgraph Dominio["Camada de Domínio e Negócio (Models & Managers)"]
        App_Cadastros["App: cadastros (Governança, Parcerias, Pessoas)"]
        App_Gestao["App: gestao_projetos (Execução Física, Financeira, Bolsas)"]
        App_Espacos["App: espacos (Matriz Espacial & Laboratórios)"]
    end

    subgraph Persistencia["Camada de Persistência & Auditoria"]
        PG[(PostgreSQL)]
        Hist[(django-simple-history)]
    end

    Apresentacao --> Controle
    Controle --> Dominio
    Dominio --> Persistencia
```

---

## 2. Diagramas de Classes (UML)

### 2.1 Herança Multi-tabela de Pessoa Jurídica (Hélice Tríplice)

```mermaid
classDiagram
    class PessoaJuridica {
        +String cnpj
        +String razao_social
        +String nome_fantasia
        +String email
        +String telefone
    }
    class ICT {
        +Boolean is_executora
        +String sigla
    }
    class EmpresaParceira {
        +String inscricao_estadual
        +String porte
    }
    class FundacaoApoio {
        +String credenciamento_mec_mcti
        +Date data_validade_credenciamento
    }
    class AgenciaFomento {
        +String esfera
    }

    PessoaJuridica <|-- ICT : herança multi-tabela
    PessoaJuridica <|-- EmpresaParceira : herança multi-tabela
    PessoaJuridica <|-- FundacaoApoio : herança multi-tabela
    PessoaJuridica <|-- AgenciaFomento : herança multi-tabela
```

### 2.2 Party-Role Pattern de Pessoa Física (LGPD)

```mermaid
classDiagram
    class PessoaFisica {
        +String nome
        +String cpf
        +String email
        +String telefone
        +User user_auth
    }
    class PerfilServidor {
        +String matricula_siape
        +String cargo
        +Boolean is_efetivo
    }
    class PerfilBolsista {
        +String curriculo_lattes
        +String nivel_titulacao
    }
    class PerfilAluno {
        +String matricula_institucional
        +String curso
    }
    class DadoBancario {
        +String banco
        +String agencia
        +String conta_corrente
        +String chave_pix
    }

    PessoaFisica "1" *-- "0..1" PerfilServidor : papel funcional
    PessoaFisica "1" *-- "0..1" PerfilBolsista : papel acadêmico
    PessoaFisica "1" *-- "0..1" PerfilAluno : papel discente
    PessoaFisica "1" o-- "1..*" DadoBancario : dados segregados
```

---

## 3. Diagramas de Máquinas de Estados (Statechart)

### 3.1 Ciclo de Vida do Projeto de PD&I

```mermaid
stateDiagram-v2
    [*] --> PROSPECCAO : Criação da Proposta (Wizard)
    PROSPECCAO --> EXECUCAO : Termo de Parceria Assinado + Plano Congelado
    EXECUCAO --> PRESTACAO_CONTAS : Conclusão das Macroentregas
    PRESTACAO_CONTAS --> ENCERRADO : Auditoria e Homologação Final (TCU/EMBRAPII)
    PROSPECCAO --> CANCELADO : Desistência / Reprovação
    EXECUCAO --> CANCELADO : Rescisão Contratual

    state EXECUCAO {
        [*] --> PlanoCongelado
        PlanoCongelado --> AditivoProrrogacao : Necessidade de Prazo
        AditivoProrrogacao --> PlanoCongelado
    }
```

### 3.2 Ciclo de Vida da Parcela de Bolsa e Relatório de Atividade

```mermaid
stateDiagram-v2
    [*] --> ParcelaPendente : Geração da Folha Mensal
    ParcelaPendente --> RA_Submetido : Bolsista anexa RA
    RA_Submetido --> RA_Devolvido : Servidor solicita correção
    RA_Devolvido --> RA_Submetido : Bolsista reapresenta
    RA_Submetido --> RA_Concluido : Atesto SIAPE com Carimbo Digital
    RA_Concluido --> ParcelaLiquidada : FAEPI baixa em lote com Comprovante
    ParcelaLiquidada --> [*]
```

---

## 4. Diagramas de Sequência

### 4.1 Atesto de Relatório de Atividades com Segregação de Funções (SoD)

```mermaid
sequenceDiagram
    actor Bolsista as Bolsista (Pesquisador)
    actor Servidor as Servidor Efetivo (SIAPE)
    participant View as atestar_relatorio()
    participant Model as RelatorioAtividade
    participant DB as PostgreSQL

    Bolsista->>Model: submeter_relatorio(resumo, horas)
    Model->>DB: UPDATE status = 'EM_ANALISE'
    
    Servidor->>View: POST /projetos/relatorios/{id}/atestar/
    Note over View: Checagem @servidor_efetivo_required
    Note over View: Trava SoD (Servidor != Bolsista)
    
    alt Tentativa de Auto-atesto
        View-->>Servidor: HTTP 403 (Violação de Segregação de Funções)
    else Validação Aprovada
        View->>Model: registrar_atesto(servidor, matricula_siape)
        Model->>DB: UPDATE status = 'CONCLUIDO', data_atesto = NOW()
        View-->>Servidor: Mensagem de Sucesso (Carimbo Aplicado)
    end
```

### 4.2 Liquidação e Baixa em Lote da Folha de Bolsas pela FAEPI

```mermaid
sequenceDiagram
    actor Gestor as Gestor Financeiro (FAEPI)
    participant View as liquidar_folha_lote()
    participant DB as PostgreSQL
    participant Parcela as Parcela.confirmar_pagamento()

    Gestor->>View: POST parcelas_ids[], data_pagamento, conta_id, comprovante
    Note over View: Abre Transação Atômica (transaction.atomic)
    
    loop Para cada parcela selecionada
        View->>DB: SELECT relatorio_atividade WHERE parcela_id = id
        alt Relatório NÃO Concluído / Sem Atesto SIAPE
            View-->>DB: Rollback Transação
            View-->>Gestor: Erro: Parcela possui pendência técnica
        else Relatório Atestado
            View->>Parcela: confirmar_pagamento()
            Parcela->>DB: UPDATE status = 'PAGO', comprovante = file
        end
    end
    
    View-->>DB: Commit Transação
    View-->>Gestor: Sucesso: N parcelas liquidadas e comprovante anexado
```

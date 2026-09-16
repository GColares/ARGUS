import os

filepath = 'C:\\ARGUS\\diario_de_bordo.md'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

nova_entrada = '''## [2026-09-15] Sprint — Estabilização de Desktop, Otimização UI e Gestão de Diretores

### 1. Entregas Técnicas do Dia

- **Estabilização da Arquitetura Desktop Portable (.exe):**
  * Correção da _race condition_ de fechamento de portas travadas do MS Edge.
  * Ajuste do mecanismo Heartbeat para suportar o _throttling_ de tabs minimizadas no Chromium, estendendo o timeout de morte do servidor para 30 segundos e eliminando fechamentos indesejados (pp_desktop.py, pp.js).
  * Injeção assertiva do favicon estático e do script Batch WSH que gera automaticamente o atalho da Área de Trabalho sempre referenciando o ícone vermelho oficial (Criar_Atalho.bat).

- **CRUD de Autoridades de Assinatura (Diretores):**
  * Criação da tabela 	b_diretores em SQLite com migração que pré-cadastra os dois diretores titulares fixos (is_titular=1).
  * Implementação da rota REST /api/diretores (POST) para gerenciar as ações CRIAR, EDITAR e EXCLUIR de diretores substitutos, com validação e blindagem de segurança para não deletar titulares.
  * Adição das lógicas de fetch e re-renderização (carregarParametros) em JS.
  * Resolução de bug crítico de sintaxe Javascript nas funções injetadas.

- **Refatorações de HTML/Interface (Limpeza Visual e UX):**
  * Remoção de botões redundantes (Gerar Recibo, Excel, Drive) no topo da 	abEntradas, centralizando-os restritamente no footer e simplificando o processo de entrada de NFs.
  * Criação da modal HTML modalDiretor (Cadastro de Diretores Substitutos).
  * Criação de um card widescreen de largura total (col-lg-12) no subGerenciarParametros para a lista de autoridades de assinatura. 
  * Badge condicional: selos de "Titular Fixo" (g-primary) inativando os botões de edição/lixeira quando a pessoa possui um vínculo fixo injetado.

### 2. Próximos Passos (Backlog e Pendências)

- Testes de ponta a ponta para homologar todos os fluxos de Saída e Empréstimos.

'''

content = content.replace('# Diário de Bordo — ARGUS', '# Diário de Bordo — ARGUS\n\n' + nova_entrada, 1)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Diario atualizado!")
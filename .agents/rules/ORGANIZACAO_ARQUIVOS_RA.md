# Organização e Criação Idempotente da Pasta de Documentos do Bolsista

## 1. Princípio Arquitetural
Todo bolsista participante de um projeto PDI possui um repositório dedicado e individualizado de arquivos no sistema. A criação e o particionamento dessas pastas devem seguir rigorosamente o princípio da **antecipação e idempotência**:

1. **Momento da Criação (Gatilho de Cadastro):**
   - As pastas dos bolsistas **não** devem ser criadas tardiamente no momento da emissão do primeiro relatório.
   - A pasta individual do bolsista deve ser criada imediatamente quando ele for **cadastrado/vinculado à equipe do projeto** (`MembroEquipe`, `Bolsista` ou fluxo de contratação).
2. **Idempotência Estrita:**
   - Uma vez criada a pasta do bolsista no projeto (`exist_ok=True` ou verificação de existência), a rotina **não deve recriá-la nem duplicá-la**.
   - Ela atua como repositório perene para todos os documentos daquele bolsista no projeto (Termo de Outorga de Bolsa, Relatórios de Atividades de todas as parcelas, comprovantes de matrícula/titulação, etc.).
3. **Escopo por Projeto:**
   - Como um pesquisador/bolsista pode atuar em múltiplos projetos, a pasta deve ser escopada dentro da hierarquia do respectivo projeto:
     `{base_storage}/projetos/{projeto_id_ou_codigo}/bolsistas/{nome_bolsista}/`
     (ou no diretório operacional correspondente, como em lotes de modelos: `{output_dir}/{nome_bolsista}/`).
4. **Sanitização de Caracteres no Sistema Operacional:**
   - Ao gerar o nome da pasta a partir do nome do bolsista, caracteres proibidos pelo sistema de arquivos (`\`, `/`, `*`, `?`, `:`, `"`, `<`, `>`, `|`) devem ser obrigatoriamente sanitizados ou substituídos por sublinhado `_`.
5. **Geração e Armazenamento de Relatórios de Atividades (RAs):**
   - Rotinas de geração de RAs (`.docx` ou `.pdf`) devem obrigatoriamente salvar o arquivo na subpasta correspondente ao bolsista (`{bolsista_dir}/{nome_arquivo}.docx`), sendo vedado despejar arquivos soltos na raiz de armazenamento.

# Requisito de Sistema: Estrutura Canônica de Armazenamento por Projeto

## 1. Princípio Arquitetural e Segregação de Ambientes
No sistema ARGUS, todos os arquivos operacionais, prestações de contas, ofícios e relatórios devem ser organizados de forma autocontida e estruturada **por projeto**. Fica vedada a dispersão de documentos em diretórios genéricos ou o despejo de instâncias geradas dentro de diretórios de modelos/gabaritos.

1. **Pasta de Modelos (`gestao_projetos/media/modelos/`):**
   - Destinada **exclusivamente a gabaritos e templates em branco** (`.docx`, `.xlsx`, `.pptx`).
   - Nenhuma rotina de geração de relatórios ou script de produção pode salvar arquivos preenchidos neste diretório.

2. **Repositório do Projeto (`gestao_projetos/projetos/<projeto_slug>/`):**
   - Cada projeto possui seu ecossistema próprio identificado pelo seu `slug` simplificado (ex: `bio_caroco`).
   - A anatomia padrão do repositório físico do projeto compõe-se de:
     ```text
     gestao_projetos/projetos/<projeto_slug>/
     ├── documentos/          # Planos de Trabalho, Termos de Parceria e Aditivos
     ├── oficios/             # Ofícios expedidos à Direção-Geral e FAEPI
     ├── execucao_financeira/ # Planilhas de conciliação, demonstrativos e extratos
     └── bolsistas/           # Repositório individual de cada membro da equipe
         └── <Nome_Bolsista>/ # RAs mensais, termos de outorga, comprovantes
     ```

## 2. Ciclo de Vida e Criação Idempotente
1. **Momento do Cadastro (Gatilho Preventivo):**
   - A pasta do projeto e as pastas individuais dos bolsistas devem ser criadas no momento do cadastro do projeto e da alocação de cada colaborador na equipe (`MembroEquipe`/`Bolsista`).
2. **Idempotência Estrita (`exist_ok=True`):**
   - Uma vez criada a pasta do bolsista no projeto, a rotina de arquivos não deve tentar recriá-la nem duplicá-la. Ela permanece como repositório perene para todo o ciclo de vida da pesquisa.
3. **Sanitização de Nomes:**
   - Caracteres proibidos em sistemas de arquivos (`\`, `/`, `*`, `?`, `:`, `"`, `<`, `>`, `|`) devem ser sanitizados para sublinhado `_`.

## 3. Geração de Relatórios de Atividades (RAs)
Toda rotina (CLI ou Django) de emissão de RAs em formato `.docx` ou `.pdf` deve obrigatoriamente direcionar o arquivo para a subpasta do bolsista:
`gestao_projetos/projetos/<projeto_slug>/bolsistas/<Nome_Bolsista>/Relatorio_de_Atividades_<Nome>_-_Parcela_<N>_de_<Total>.docx`

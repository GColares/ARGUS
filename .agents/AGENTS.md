# Regras de Arquitetura do ARGUS

## Módulos e Home Principal
Sempre que você criar, renomear ou excluir um aplicativo/módulo no projeto ARGUS, você deve obrigatoriamente editar a view `home_argus` localizada em `argus_core/views.py`. 
O dicionário `modulos` dentro dessa view controla os painéis exibidos na tela principal (dashboard) do sistema. O novo módulo só ficará visível e acessível para o usuário final se for adicionado a essa lista.

## Idioma
Responda sempre em **Português do Brasil (pt-BR)**.

## Telas de Cadastro (CRUD)
Sempre que você criar, planejar ou modificar funcionalidades de "Cadastro" (CRUD) no sistema, é OBRIGATÓRIO incluir e implementar a função de "Excluir" (Delete). Todas as telas de listagem ou formulários de edição devem prover um caminho claro e funcional para a exclusão do registro, preferencialmente com confirmação (ex: modal ou página de confirmação do Django) para evitar deleções acidentais.

## Estilo de Tabelas
Os cabeçalhos (`<th>` ou `<thead>`) de todas as tabelas criadas no sistema devem ter os rótulos centralizados obrigatoriamente (por exemplo, utilizando a classe utilitária `text-center` do Bootstrap). As colunas de "Ações" (editar/excluir) também devem acompanhar esse alinhamento para manter a uniformidade visual.

## Navegação e UX (Botão Voltar)
Todas as páginas e telas desenvolvidas para o sistema Argus devem obrigatoriamente conter um botão ou link de "Voltar" (Back) funcionando adequadamente. Este botão deve apontar de volta para a tela lógica anterior na hierarquia do sistema ou utilizar mecanismos de fallback do navegador (ex: javascript:history.back()) caso a rota de origem seja dinâmica.

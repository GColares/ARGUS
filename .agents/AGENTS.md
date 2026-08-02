# Regras de Arquitetura do ARGUS

## Módulos e Home Principal
Sempre que você criar, renomear ou excluir um aplicativo/módulo no projeto ARGUS, você deve obrigatoriamente editar a view `home_argus` localizada em `argus_core/views.py`. 
O dicionário `modulos` dentro dessa view controla os painéis exibidos na tela principal (dashboard) do sistema. O novo módulo só ficará visível e acessível para o usuário final se for adicionado a essa lista.

## Idioma
Responda sempre em **Português do Brasil (pt-BR)**.

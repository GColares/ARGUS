# Semântica de Comandos de Execução e Linguagem (Termine vs. Pare)

Para evitar ambiguidades e interrupções indevidas de tarefas de longa duração (testes automatizados, backups, builds, scripts assíncronos):

1. **"Termine" / "Vá até o final" / "Conclua" / "Finalize":**
   - **Significado:** Executar ou aguardar a tarefa até a sua **conclusão total e natural**.
   - **Ação do Agente:** **NUNCA abortar ou matar (`kill`)** o processo. O agente deve acompanhar, aguardar ou deixar a rotina rodar até que ela finalize normalmente e reporte o resultado final consolidado.

2. **"Pare" / "Interrompa" / "Cancele" / "Aborte":**
   - **Significado:** Interrupção imediata, cancelamento deliberado antes do término.
   - **Ação do Agente:** Somente neste caso explícito o agente deve utilizar `manage_task: kill` ou comandos de cancelamento/interrupção da execução.

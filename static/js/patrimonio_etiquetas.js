/**
 * static/js/patrimonio_etiquetas.js
 * Gerenciamento de eventos para impressão de etiquetas patrimoniais
 * Diretriz: Zero JavaScript inline no HTML.
 */
document.addEventListener('DOMContentLoaded', function() {
    const btnImprimir = document.querySelector('[data-action="print-etiquetas"]');
    if (btnImprimir) {
        btnImprimir.addEventListener('click', function() {
            window.print();
        });
    }
});

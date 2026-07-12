// static/js/script.js

document.addEventListener('DOMContentLoaded', function() {
    // Inicialização genérica de tooltips do Bootstrap (caso venha a usar)
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Aqui entrarão as futuras lógicas globais do ARGUS
    console.log("ARGUS Core Scripts carregados com sucesso.");
});
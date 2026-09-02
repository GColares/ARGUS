import re

path = r'c:\ARGUS\cadastros\templates\cadastros\form_projeto.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# First, fix step 6 fields specifically
content = content.replace('{{ form_plano.escopo }}', '{{ form_plano.escopo_geral }}')
content = content.replace('{{ form_plano.eap }}', '{{ form_plano.estrutura_analitica }}')

# Now fix the numbering.
# Let's find all wizard-step blocks.
# We will use regex to find `<div class="wizard-step.*?" id="step.*?">` and the subsequent `<h4>` and `<div class="d-flex justify-content-between mt-auto pt-3 border-top">`
# Actually, since the structure is very predictable, we can split by `<div class="wizard-step` and process them.

parts = content.split('<div class="wizard-step')

titles = [
    "1. Dados Cadastrais",
    "2. Descrição Básica",
    "3. Vigência e Execução",
    "4. Motivação",
    "5. Objetivos e Metas",
    "6. Escopo Técnico",
    "7. Gestão de Riscos",
    "8. Estratégia",
    "9. Plano de Ação",
    "10. Macro-Entregas",
    "11. Indicadores de Resultados",
    "12. Características Inovadoras",
    "13. Resultados Esperados",
    "14. Cronograma",
    "15. Desafios Científicos e Tecnológicos",
    "16. Solução Proposta",
    "17. Orçamento e Aportes Globais"
]

out = parts[0]
step_idx = 1
for part in parts[1:]:
    # Reconstruct the div opening
    part = '<div class="wizard-step' + part
    
    if step_idx <= 17:
        # 1. Fix the ID
        # pattern: id="step..." -> id="step{step_idx}"
        part = re.sub(r'id="step\d+"', f'id="step{step_idx}"', part, count=1)
        
        # 2. Fix the H4 title
        # pattern: <h4 class="fw-bold text-secondary border-bottom pb-2 mb-4">.*?</h4>
        # we want to preserve any <span class="text-danger">*</span> if it exists
        def h4_repl(m):
            inner = m.group(1)
            span = ""
            if '<span' in inner:
                span = " " + inner[inner.find('<span'):]
            return f'<h4 class="fw-bold text-secondary border-bottom pb-2 mb-4">{titles[step_idx-1]}{span}</h4>'
            
        part = re.sub(r'<h4 class="fw-bold text-secondary border-bottom pb-2 mb-4">(.*?)</h4>', h4_repl, part, count=1)
        
        # 3. Fix the buttons
        # data-prev="step..."
        if step_idx > 1:
            part = re.sub(r'data-prev="step\d+"', f'data-prev="step{step_idx-1}"', part, count=1)
        # data-next="step..."
        if step_idx < 17:
            part = re.sub(r'data-next="step\d+"', f'data-next="step{step_idx+1}"', part, count=1)
            
    out += part
    step_idx += 1

with open(path, 'w', encoding='utf-8') as f:
    f.write(out)

print("Done fixing steps.")

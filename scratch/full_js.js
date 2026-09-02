
document.addEventListener("DOMContentLoaded", function() {
    const formId = 'projetoWizardForm';
    const storageKey = 'argus_projeto_draft';
    const isEditMode = {% if projeto %}true{% else %}false{% endif %};
    const form = document.getElementById(formId);
    const quillInstances = {};

    if(typeof jQuery !== 'undefined') {
        jQuery('.select2-multiple').select2({
            theme: 'bootstrap-5',
            width: '100%',
            placeholder: "Selecione as opções..."
        });
        jQuery('.select2-multiple').on('change', function() {
            autoSave();
        });
    }

    const textareas = document.querySelectorAll('textarea.richtext');
    textareas.forEach(function(textarea) {
        textarea.style.display = 'none';
        const editorContainer = document.createElement('div');
        textarea.parentNode.insertBefore(editorContainer, textarea.nextSibling);

        const quill = new Quill(editorContainer, {
            theme: 'snow',
            modules: {
                toolbar: [
                    [{ 'header': [1, 2, 3, false] }],
                    ['bold', 'italic', 'underline', 'strike'],
                    [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                    [{ 'indent': '-1'}, { 'indent': '+1' }],
                    ['link', 'image', 'video'],
                    ['clean']
                ]
            }
        });

        quillInstances[textarea.id] = quill;

        quill.on('text-change', function() {
            textarea.value = quill.root.innerHTML;
            autoSave();
        });
    });

    
    // --- LÓGICA DINÂMICA: PLANO DE AÇÃO (ATIVIDADES) (TABELA + MODAL) ---
    let atividadesList = [];
    let modalAtividadeEditIndex = -1;
    const modalAtividadeInstance = new bootstrap.Modal(document.getElementById('modalAtividade'));
    
    let modalAtividadeStartMonth = null;
    let modalAtividadeEndMonth = null;
    let modalEntregaveisTemp = []; // Store deliverables temporarily while modal is open
    
    function renderMonthGrid() {
        const grid = document.getElementById('modal-atividade-month-grid');
        if (!grid) return;
        const vigenciaInput = document.getElementById('id_vigencia_meses');
        const totalMeses = vigenciaInput && vigenciaInput.value ? parseInt(vigenciaInput.value) : 24;
        
        grid.innerHTML = '';
        for (let i = 1; i <= totalMeses; i++) {
            const wrapper = document.createElement('div');
            wrapper.className = 'd-flex flex-column align-items-center mb-1';
            wrapper.style.width = '45px';
            
            const box = document.createElement('div');
            box.className = 'month-box';
            box.textContent = 'M' + i;
            
            const label = document.createElement('small');
            label.className = 'text-muted fw-bold mt-1';
            label.style.fontSize = '0.65rem';
            label.textContent = ' '; // Non-breaking space to keep height
            
            if (modalAtividadeStartMonth === i && modalAtividadeEndMonth === i) {
                box.classList.add('selected-single');
                label.textContent = 'ÚNICO';
                label.classList.add('text-purple'); // Just reusing a color if possible, or leave muted
            } else if (modalAtividadeStartMonth === i) {
                box.classList.add('selected-start');
                label.textContent = 'INÍCIO';
                label.classList.remove('text-muted');
                label.classList.add('text-success');
            } else if (modalAtividadeEndMonth === i) {
                box.classList.add('selected-end');
                label.textContent = 'FIM';
                label.classList.remove('text-muted');
                label.classList.add('text-danger');
            } else if (modalAtividadeStartMonth && modalAtividadeEndMonth && i > modalAtividadeStartMonth && i < modalAtividadeEndMonth) {
                box.classList.add('in-range');
            }
            
            box.addEventListener('click', () => {
                if (!modalAtividadeStartMonth || (modalAtividadeStartMonth && modalAtividadeEndMonth)) {
                    modalAtividadeStartMonth = i;
                    modalAtividadeEndMonth = null;
                } else {
                    if (i < modalAtividadeStartMonth) {
                        modalAtividadeEndMonth = modalAtividadeStartMonth;
                        modalAtividadeStartMonth = i;
                    } else {
                        modalAtividadeEndMonth = i;
                    }
                }
                
                document.getElementById('modal-atividade-mes-inicio').value = modalAtividadeStartMonth || '';
                document.getElementById('modal-atividade-mes-fim').value = modalAtividadeEndMonth || modalAtividadeStartMonth || '';
                
                if (modalAtividadeStartMonth && modalAtividadeEndMonth) {
                    document.getElementById('modal-atividade-month-error').classList.add('d-none');
                }
                
                renderMonthGrid();
            });
            wrapper.appendChild(box);
            wrapper.appendChild(label);
            grid.appendChild(wrapper);
        }
    }

    function renderEntregaveisList() {
        const listContainer = document.getElementById('modal-atividade-entregaveis-list');
        listContainer.innerHTML = '';
        
        if (modalEntregaveisTemp.length === 0) {
            listContainer.innerHTML = '<small class="text-muted fst-italic">Nenhum entregável adicionado.</small>';
            return;
        }
        
        modalEntregaveisTemp.forEach((ent, idx) => {
            const item = document.createElement('div');
            item.className = 'd-flex justify-content-between align-items-center bg-light border rounded px-2 py-1';
            item.innerHTML = `
                <span class="small"><i class="fas fa-check-circle text-success me-2"></i>${ent}</span>
                <button type="button" class="btn btn-sm text-danger border-0 p-0" title="Remover" onclick="removeTempEntregavel(${idx})"><i class="fas fa-times"></i></button>
            `;
            listContainer.appendChild(item);
        });
    }

    window.removeTempEntregavel = function(idx) {
        modalEntregaveisTemp.splice(idx, 1);
        renderEntregaveisList();
    };

    document.getElementById('btn-add-entregavel').addEventListener('click', function() {
        const input = document.getElementById('modal-atividade-entregavel-input');
        const val = input.value.trim();
        if (val) {
            // Evitar ; no meio do texto para não quebrar nosso split do backend
            modalEntregaveisTemp.push(val.replace(/;/g, ','));
            input.value = '';
            renderEntregaveisList();
        }
    });
    
    document.getElementById('modal-atividade-entregavel-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            document.getElementById('btn-add-entregavel').click();
        }
    });

    // Abrir Modal de Nova Atividade
    document.getElementById('btn-open-modal-atividade').addEventListener('click', function() {
        document.getElementById('modal-atividade-titulo').textContent = 'Nova Atividade #' + (atividadesList.length + 1);
        modalAtividadeEditIndex = -1;
        document.getElementById('modal-atividade-nome').value = '';
        document.getElementById('modal-atividade-descricao').value = '';
        document.getElementById('modal-atividade-justificativa').value = '';
        
        modalEntregaveisTemp = [];
        document.getElementById('modal-atividade-entregavel-input').value = '';
        renderEntregaveisList();
        
        modalAtividadeStartMonth = null;
        modalAtividadeEndMonth = null;
        document.getElementById('modal-atividade-mes-inicio').value = '';
        document.getElementById('modal-atividade-mes-fim').value = '';
        document.getElementById('modal-atividade-month-error').classList.add('d-none');
        renderMonthGrid();
        
        modalAtividadeInstance.show();
    });
    
    // Salvar do Modal para a Tabela Virtual
    document.getElementById('btn-save-atividade-modal').addEventListener('click', function() {
        // Coletar
        const nome = document.getElementById('modal-atividade-nome').value.trim();
        const mes_inicio = document.getElementById('modal-atividade-mes-inicio').value;
        const mes_fim = document.getElementById('modal-atividade-mes-fim').value;
        const descricao = document.getElementById('modal-atividade-descricao').value;
        const justificativa = document.getElementById('modal-atividade-justificativa').value;
        
        // Juntar entregaveis com ;
        const entregaveis = modalEntregaveisTemp.join(';');
        
        if (!nome || !descricao.trim() || !justificativa.trim()) {
            alert('Por favor, preencha todos os campos obrigatórios (*).');
            return;
        }
        
        if (!mes_inicio || !mes_fim) {
            document.getElementById('modal-atividade-month-error').classList.remove('d-none');
            return;
        }
        
        const obj = { nome, mes_inicio, mes_fim, descricao, justificativa, entregaveis };
        
        if (modalAtividadeEditIndex >= 0) {
            atividadesList[modalAtividadeEditIndex] = obj;
        } else {
            atividadesList.push(obj);
        }
        
        renderAtividadesTable();
        modalAtividadeInstance.hide();
        autoSave();
        if (typeof isEditMode !== 'undefined' && isEditMode && window.saveFormAjax) {
            window.saveFormAjax(true);
        }
    });
    
    window.editAtividade = function(index) {
        modalAtividadeEditIndex = index;
        const obj = atividadesList[index];
        document.getElementById('modal-atividade-titulo').textContent = 'Editar Atividade #' + (index + 1);
        document.getElementById('modal-atividade-nome').value = obj.nome;
        document.getElementById('modal-atividade-mes-inicio').value = obj.mes_inicio;
        document.getElementById('modal-atividade-mes-fim').value = obj.mes_fim;
        document.getElementById('modal-atividade-descricao').value = obj.descricao;
        document.getElementById('modal-atividade-justificativa').value = obj.justificativa;
        
        // Popular Entregaveis
        modalEntregaveisTemp = obj.entregaveis ? obj.entregaveis.split(';').filter(e => e.trim().length > 0) : [];
        document.getElementById('modal-atividade-entregavel-input').value = '';
        renderEntregaveisList();
        
        modalAtividadeStartMonth = parseInt(obj.mes_inicio) || null;
        modalAtividadeEndMonth = parseInt(obj.mes_fim) || null;
        document.getElementById('modal-atividade-month-error').classList.add('d-none');
        renderMonthGrid();
        
        modalAtividadeInstance.show();
    };
    
    window.removeAtividade = function(index) {
        if(confirm('Remover esta atividade?')) {
            atividadesList.splice(index, 1);
            renderAtividadesTable();
            autoSave();
        }
    };
    
    function renderAtividadesTable() {
        const tbody = document.querySelector('#tabela-atividades tbody');
        const hiddenInputsContainer = document.getElementById('atividades-hidden-inputs');
        if(!tbody) return;
        
        tbody.innerHTML = '';
        hiddenInputsContainer.innerHTML = '';
        
        if (atividadesList.length === 0) {
            tbody.innerHTML = `<tr id="row-empty-atividade"><td colspan="6" class="text-center text-muted py-4">Nenhuma atividade cadastrada. Clique em "Adicionar Atividade".</td></tr>`;
            return;
        }
        
        atividadesList.forEach((atv, i) => {
            // Embelezar a listagem de entregáveis na tabela mestre
            let entregaveisBadge = '-';
            if (atv.entregaveis) {
                const arr = atv.entregaveis.split(';').filter(e => e.trim() !== '');
                if(arr.length > 0) {
                   entregaveisBadge = arr.map(e => `<span class="badge bg-secondary mb-1 me-1 text-wrap text-start">${e}</span>`).join('');
                }
            }
            
            // Tabela Visual
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="text-center align-middle fw-bold">${i + 1}</td>
                <td class="align-middle">${atv.nome}</td>
                <td class="align-middle">${entregaveisBadge}</td>
                <td class="text-center align-middle">Mês ${atv.mes_inicio}</td>
                <td class="text-center align-middle">Mês ${atv.mes_fim}</td>
                <td class="text-center align-middle">
                    <button type="button" class="btn btn-sm btn-outline-primary" title="Editar" onclick="editAtividade(${i})"><i class="fas fa-edit"></i></button>
                    <button type="button" class="btn btn-sm btn-outline-danger" title="Remover" onclick="removeAtividade(${i})"><i class="fas fa-trash"></i></button>
                </td>
            `;
            tbody.appendChild(tr);
            
            // Inputs Ocultos para Django (Form POST)
            hiddenInputsContainer.innerHTML += `
                <input type="hidden" name="atividade_nome[]" value="${atv.nome.replace(/"/g, '&quot;')}">
                <input type="hidden" name="atividade_mes_inicio[]" value="${atv.mes_inicio}">
                <input type="hidden" name="atividade_mes_fim[]" value="${atv.mes_fim}">
                <input type="hidden" name="atividade_descricao[]" value="${atv.descricao.replace(/"/g, '&quot;')}">
                <input type="hidden" name="atividade_justificativa[]" value="${atv.justificativa.replace(/"/g, '&quot;')}">
                <input type="hidden" name="atividade_entregaveis[]" value="${atv.entregaveis.replace(/"/g, '&quot;')}">
            `;
        });
    }
    
    // CARREGAR ATIVIDADES EXISTENTES NO MODO EDIÇÃO
    {% if plano_ativo and plano_ativo.atividades.all %}
        {% for atividade in plano_ativo.atividades.all %}
            atividadesList.push({
                nome: '{{ atividade.nome|escapejs }}',
                mes_inicio: '{{ atividade.mes_inicio|default_if_none:""|escapejs }}',
                mes_fim: '{{ atividade.mes_fim|default_if_none:""|escapejs }}',
                descricao: `{{ atividade.descricao|escapejs }}`,
                justificativa: `{{ atividade.justificativa|default_if_none:""|escapejs }}`,
                entregaveis: `{% for entregavel in atividade.entregaveis.all %}{{ entregavel.nome|escapejs }}{% if not forloop.last %};{% endif %}{% endfor %}`
            });
        {% endfor %}
        renderAtividadesTable();
    {% endif %}

    // --- LÓGICA DINÂMICA: MACRO-ENTREGAS ---
    const macroentregasContainer = document.getElementById('macroentregas-container');
    const btnAddMacroentrega = document.getElementById('btn-add-macroentrega');
    let macroentregaCount = 0;

    function createMacroentregaCard(data = {}) {
        macroentregaCount++;
        const index = macroentregaCount;
        
        const card = document.createElement('div');
        card.className = 'card border-primary mb-4 shadow-sm macroentrega-card';
        card.innerHTML = `
            <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center py-2">
                <h6 class="mb-0 fw-bold"><i class="fas fa-box-open me-2"></i>Macro-Entrega ${index}</h6>
                <button type="button" class="btn btn-sm btn-danger btn-remover-macroentrega" title="Remover Macro-Entrega"><i class="fas fa-times"></i></button>
            </div>
            <div class="card-body bg-light">
                <div class="row g-3">
                    <div class="col-md-2">
                        <label class="form-label small fw-bold">Número</label>
                        <input type="number" name="macro_numero[]" class="form-control" value="${data.numero || index}" required>
                    </div>
                    <div class="col-md-10">
                        <label class="form-label small fw-bold">Nome da Macro-Entrega</label>
                        <input type="text" name="macro_nome[]" class="form-control" value="${data.nome || ''}" required>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Data Início</label>
                        <input type="date" name="macro_data_inicio[]" class="form-control" value="${data.data_inicio || ''}">
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Data Fim</label>
                        <input type="date" name="macro_data_fim[]" class="form-control" value="${data.data_fim || ''}">
                    </div>
                    <div class="col-md-12">
                        <label class="form-label small fw-bold">Micro-Entregas Relacionadas</label>
                        <textarea name="macro_micro_entregas[]" class="form-control" rows="2" placeholder="Descreva os componentes ou entregas menores que formam esta Macro-Entrega...">${data.micro_entregas || ''}</textarea>
                    </div>
                </div>
            </div>
        `;
        
        card.querySelector('.btn-remover-macroentrega').addEventListener('click', function() {
            card.remove();
            autoSave();
        });
        
        card.querySelectorAll('input, textarea').forEach(input => {
            input.addEventListener('input', autoSave);
        });

        macroentregasContainer.appendChild(card);
    }

    if (btnAddMacroentrega) {
        btnAddMacroentrega.addEventListener('click', function() {
            createMacroentregaCard();
            autoSave();
        });
    }
    
    if (!isEditMode && document.querySelectorAll('.macroentrega-card').length === 0 && macroentregasContainer) {
        createMacroentregaCard();
    }

    
    // --- LÓGICA DINÂMICA: ORÇAMENTO (RUBRICAS) ---
    const orcamentoContainer = document.getElementById('orcamento-container');
    const btnAddRubrica = document.getElementById('btn-add-rubrica');
    let rubricaCount = 0;

    function createRubricaCard(data = {}) {
        rubricaCount++;
        const index = rubricaCount;
        
        const card = document.createElement('div');
        card.className = 'card border-success mb-3 shadow-sm rubrica-card';
        card.innerHTML = `
            <div class="card-header bg-success text-white d-flex justify-content-between align-items-center py-2">
                <h6 class="mb-0 fw-bold"><i class="fas fa-money-bill-wave me-2"></i>Despesa ${index}</h6>
                <button type="button" class="btn btn-sm btn-danger btn-remover-rubrica" title="Remover Rubrica"><i class="fas fa-times"></i></button>
            </div>
            <div class="card-body bg-light">
                <div class="row g-3">
                    <div class="col-md-4">
                        <label class="form-label small fw-bold">Categoria</label>
                        <select name="rubrica_categoria[]" class="form-select" required>
                            <option value="">Selecione...</option>
                            <option value="PESSOAL">Pessoal (RH Direto e Indireto)</option>
                            <option value="CONSUMO">Material de Consumo</option>
                            <option value="DIARIAS">Diárias, Passagens e Locomoção</option>
                            <option value="TERCEIROS">Serviços de Terceiros (PF e PJ)</option>
                            <option value="CAPITAL">Capital e Equipamentos</option>
                            <option value="SUPORTE">Suporte Operacional / Administrativo</option>
                            <option value="OUTRAS">Outras Despesas Correntes</option>
                        </select>
                    </div>
                    <div class="col-md-4">
                        <label class="form-label small fw-bold">Fonte de Recurso</label>
                        <select name="rubrica_fonte[]" class="form-select" required>
                            <option value="">Selecione...</option>
                            <option value="EMPRESA">Empresa Parceira</option>
                            <option value="EMBRAPII">EMBRAPII</option>
                            <option value="SEBRAE">SEBRAE</option>
                            <option value="CONTRAPARTIDA">Contrapartida ICT</option>
                        </select>
                    </div>
                    <div class="col-md-4">
                        <label class="form-label small fw-bold">Valor Previsto (R$)</label>
                        <input type="number" step="0.01" name="rubrica_valor[]" class="form-control" value="${data.valor_previsto || ''}" required>
                    </div>
                    <div class="col-md-12">
                        <label class="form-label small fw-bold">Descrição do Item</label>
                        <input type="text" name="rubrica_descricao[]" class="form-control" placeholder="Descreva brevemente no que será gasto..." value="${data.descricao || ''}">
                    </div>
                </div>
            </div>
        `;
        
        // Restore selects if data exists
        if(data.categoria) {
            card.querySelector(`select[name="rubrica_categoria[]"]`).value = data.categoria;
        }
        if(data.fonte) {
            card.querySelector(`select[name="rubrica_fonte[]"]`).value = data.fonte;
        }

        card.querySelector('.btn-remover-rubrica').addEventListener('click', function() {
            card.remove();
            autoSave();
        });
        
        card.querySelectorAll('input, select').forEach(input => {
            input.addEventListener('change', autoSave);
            input.addEventListener('input', autoSave);
        });

        orcamentoContainer.appendChild(card);
    }

    if (btnAddRubrica) {
        btnAddRubrica.addEventListener('click', function() {
            createRubricaCard();
            autoSave();
        });
    }
    
    if (!isEditMode && document.querySelectorAll('.rubrica-card').length === 0 && orcamentoContainer) {
        createRubricaCard();
    }

    
    // --- LÓGICA AJAX: FILTRAR TERMOS DE PARCERIA PELA EMPRESA ---
    const concedenteSelect = document.querySelector('select[name="concedente"]');
    const termoSelect = document.getElementById('termo_existente');
    // Captura o ID do projeto atual (se editando) e o termo já vinculado (se existir)
    const projetoAtualId = "{{ projeto.id|default:'' }}";
    const termoAtualId = "{{ projeto.termos_parceria.first.id|default:'' }}";
    
    function carregarTermos(concedenteId, termoParaSelecionarId) {
        if (!concedenteId) return;
        
        let url = `/cadastros/api/termos-por-empresa/${concedenteId}/`;
        if (projetoAtualId) url += `?projeto_id=${projetoAtualId}`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                // Preserva a opção vazia
                termoSelect.innerHTML = '<option value="">Nenhum / Continuar em Prospecção Solta</option>';
                data.termos.forEach(termo => {
                    const option = document.createElement('option');
                    option.value = termo.id;
                    option.textContent = termo.display_name;
                    termoSelect.appendChild(option);
                });
                
                // Seleciona o termo correto: prioridade (1) parâmetro passado (2) termo atual do servidor
                const idParaSelecionar = termoParaSelecionarId || termoAtualId;
                if (idParaSelecionar) {
                    termoSelect.value = idParaSelecionar;
                }
            })
            .catch(error => console.error('Erro ao buscar termos:', error));
    }
    
    if (concedenteSelect && termoSelect) {
        // Ao mudar a empresa, recarrega os termos sem pré-seleção
        concedenteSelect.addEventListener('change', function() {
            carregarTermos(this.value, null);
        });
        
        // Ao carregar a página: se há empresa selecionada, carrega os termos e pré-seleciona o atual
        if (concedenteSelect.value) {
            carregarTermos(concedenteSelect.value, termoAtualId);
        }
        
        termoSelect.addEventListener('change', autoSave);
    }

    window.showStepGlobal = function(stepId) { showStep(stepId); };
    function showStep(stepId) {
        syncQuills();
        document.querySelectorAll('.wizard-step').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.vertical-wizard .nav-link').forEach(el => el.classList.remove('active'));
        
        document.getElementById(stepId).classList.add('active');
        document.getElementById(stepId + '-tab').classList.add('active');
        
        // Em vez de rolar a janela (que agora está travada), rola apenas a caixa de conteúdo da direita
        const rightPane = document.querySelector('.custom-scrollbar');
        if (rightPane) {
            rightPane.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        }
        
        autoSave();
    }

    document.querySelectorAll('.btn-next').forEach(btn => {
        btn.addEventListener('click', function() {
            showStep(this.getAttribute('data-next'));
        });
    });

    document.querySelectorAll('.btn-prev').forEach(btn => {
        btn.addEventListener('click', function() {
            showStep(this.getAttribute('data-prev'));
        });
    });
    
    document.querySelectorAll('.vertical-wizard .nav-link').forEach(btn => {
        btn.removeAttribute('disabled');
        btn.addEventListener('click', function() {
            const targetId = this.id.replace('-tab', '');
            showStep(targetId);
        });
    });

    function autoSave() {
        if (isEditMode) return;
        
        const formData = new FormData(form);
        const data = {};
        for (let [key, value] of formData.entries()) {
            if (key === 'csrfmiddlewaretoken') continue;
            if (data[key]) {
                if (!Array.isArray(data[key])) {
                    data[key] = [data[key]];
                }
                data[key].push(value);
            } else {
                data[key] = value;
            }
        }
        localStorage.setItem(storageKey, JSON.stringify(data));
    }

    function loadDraft() {
        if (isEditMode) return;
        
        const draft = localStorage.getItem(storageKey);
        if (draft) {
            try {
                const data = JSON.parse(draft);
                for (let key in data) {
                    const input = form.elements[key];
                    if (!input) continue;
                    
                    const value = data[key];
                    
                    if (input.type === 'checkbox' || input.type === 'radio') {
                        input.checked = (input.value === value);
                    } else if (input.tagName === 'SELECT' && input.multiple) {
                        const vals = Array.isArray(value) ? value : [value];
                        if(typeof jQuery !== 'undefined') {
                            jQuery(input).val(vals).trigger('change');
                        } else {
                            Array.from(input.options).forEach(opt => {
                                opt.selected = vals.includes(opt.value);
                            });
                        }
                    } else if (input.length) {
                        const radio = Array.from(input).find(r => r.value === value);
                        if (radio) radio.checked = true;
                    } else {
                        input.value = value;
                        if (input.classList && input.classList.contains('richtext') && quillInstances[input.id]) {
                            quillInstances[input.id].clipboard.dangerouslyPasteHTML(value);
                        }
                    }
                }
            } catch (e) {
                console.error("Erro ao carregar rascunho:", e);
            }
        }
    }

    form.addEventListener('input', function(e) {
        if(e.target.name !== 'csrfmiddlewaretoken') {
            autoSave();
        }
    });

    function syncQuills() {
        textareas.forEach(function(textarea) {
            if (quillInstances[textarea.id]) {
                textarea.value = quillInstances[textarea.id].root.innerHTML;
            }
        });
    }

    window.saveFormAjax = function(silent = false) {
        syncQuills();
        const formData = new FormData(form);
        formData.append('action', 'salvar'); // Força a ação como rascunho
        
        let btnSave = null;
        let originalBtnHTML = '';
        if (!silent) {
            btnSave = document.querySelector('button[type="submit"]');
            if (btnSave) {
                originalBtnHTML = btnSave.innerHTML;
                btnSave.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Salvando...';
                btnSave.disabled = true;
            }
        }
        
        fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!silent) {
                if (btnSave) {
                    btnSave.innerHTML = originalBtnHTML;
                    btnSave.disabled = false;
                }
            }
            if (response.ok) {
                const toastHTML = `
                <div class="toast align-items-center text-bg-success border-0 shadow-lg mb-2" role="alert" aria-live="assertive" aria-atomic="true">
                    <div class="d-flex">
                        <div class="toast-body fw-bold d-flex align-items-center">
                            <i class="fas fa-check-circle me-2 fs-5"></i>
                            ${silent ? 'Atividade salva no banco de dados!' : 'Alterações salvas com sucesso!'}
                        </div>
                        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                    </div>
                </div>`;
                
                let toastContainer = document.querySelector('.toast-container');
                if (!toastContainer) {
                    toastContainer = document.createElement('div');
                    toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
                    document.body.appendChild(toastContainer);
                }
                
                toastContainer.insertAdjacentHTML('beforeend', toastHTML);
                const toastEl = toastContainer.lastElementChild;
                const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
                toast.show();
                toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
            } else {
                if (!silent) {
                    window.location.reload();
                }
            }
        })
        .catch(error => {
            if (!silent && btnSave) {
                btnSave.innerHTML = originalBtnHTML;
                btnSave.disabled = false;
            }
            console.error('Erro no salvamento AJAX:', error);
            if (!silent) {
                window.location.reload();
            }
        });
    };

    form.addEventListener('submit', function(e) {
        if (!isEditMode) {
            syncQuills();
            localStorage.removeItem(storageKey);
            return;
        }
        
        e.preventDefault();
        
        if (e.submitter && e.submitter.value === 'publicar') {
            syncQuills();
            form.submit();
            return;
        }
        
        window.saveFormAjax(false);
    });


    if (!isEditMode) {
        loadDraft();
    } else {
        textareas.forEach(function(textarea) {
            if (textarea.value && quillInstances[textarea.id]) {
                quillInstances[textarea.id].clipboard.dangerouslyPasteHTML(textarea.value);
            }
        });
    }

    // --- LÓGICA DO MENU LATERAL RETRÁTIL ---
    const btnToggleSidebar = document.getElementById('btn-toggle-sidebar');
    const sidebarCol = document.getElementById('wizard-sidebar-col');
    const contentCol = document.getElementById('wizard-content-col');
    let isSidebarVisible = true;

    if(btnToggleSidebar && sidebarCol && contentCol) {
        btnToggleSidebar.addEventListener('click', function() {
            isSidebarVisible = !isSidebarVisible;
            if(isSidebarVisible) {
                // Mostrar
                sidebarCol.classList.remove('d-none');
                sidebarCol.classList.add('col-md-4', 'col-lg-3');
                contentCol.classList.remove('col-md-12', 'col-lg-12');
                contentCol.classList.add('col-md-8', 'col-lg-9');
                btnToggleSidebar.innerHTML = '<i class="fas fa-expand-arrows-alt me-1"></i> Tela Cheia';
            } else {
                // Ocultar
                sidebarCol.classList.add('d-none');
                sidebarCol.classList.remove('col-md-4', 'col-lg-3');
                contentCol.classList.remove('col-md-8', 'col-lg-9');
                contentCol.classList.add('col-md-12', 'col-lg-12');
                btnToggleSidebar.innerHTML = '<i class="fas fa-compress-arrows-alt me-1"></i> Voltar Menu';
            }
        });
    }

    // --- LÓGICA DO MENU LATERAL RETRÁTIL ---
    const btnToggleSidebar = document.getElementById('btn-toggle-sidebar');
    const sidebarCol = document.getElementById('wizard-sidebar-col');
    const contentCol = document.getElementById('wizard-content-col');
    let isSidebarVisible = true;

    if(btnToggleSidebar && sidebarCol && contentCol) {
        btnToggleSidebar.addEventListener('click', function() {
            isSidebarVisible = !isSidebarVisible;
            if(isSidebarVisible) {
                // Mostrar
                sidebarCol.classList.remove('d-none');
                sidebarCol.classList.add('col-md-4', 'col-lg-3');
                contentCol.classList.remove('col-md-12', 'col-lg-12');
                contentCol.classList.add('col-md-8', 'col-lg-9');
                btnToggleSidebar.innerHTML = '<i class="fas fa-expand-arrows-alt me-1"></i> Tela Cheia';
            } else {
                // Ocultar
                sidebarCol.classList.add('d-none');
                sidebarCol.classList.remove('col-md-4', 'col-lg-3');
                contentCol.classList.remove('col-md-8', 'col-lg-9');
                contentCol.classList.add('col-md-12', 'col-lg-12');
                btnToggleSidebar.innerHTML = '<i class="fas fa-compress-arrows-alt me-1"></i> Voltar Menu';
            }
        });
    }
});

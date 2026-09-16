import re

with open('static/js/app.js', 'r', encoding='utf-8') as f:
    conteudo = f.read()

render_diretores = '''  renderizarListaParametros("listaParamsAmbientes", params.AMBIENTE || [], "AMBIENTE");
  renderizarListaParametros("listaParamsProjetos", params.PROJETO || [], "PROJETO");
  renderizarListaSolicitantes(params.SOLICITANTE || []);
  if(params.diretores) { renderizarListaDiretores(params.diretores); }'''

conteudo = conteudo.replace('''  renderizarListaParametros("listaParamsAmbientes", params.AMBIENTE || [], "AMBIENTE");
  renderizarListaParametros("listaParamsProjetos", params.PROJETO || [], "PROJETO");
  renderizarListaSolicitantes(params.SOLICITANTE || []);''', render_diretores)

funcoes_diretores = r'''
// =========================================================
// DIRETORES & SUBSTITUTOS
// =========================================================
function renderizarListaDiretores(diretores) {
  const tbody = document.getElementById("listaParamsDiretores");
  if (!tbody) return;
  tbody.innerHTML = "";
  
  if (diretores.length === 0) {
    tbody.innerHTML = <tr><td colspan="4" class="text-center text-muted p-3">Nenhum diretor cadastrado.</td></tr>;
    return;
  }
  
  diretores.forEach(d => {
    let tr = document.createElement("tr");
    let btnHtml = "";
    if (d.is_titular === 1) {
        tr.style.backgroundColor = "rgba(var(--bs-primary-rgb), 0.05)";
        btnHtml = <span class="badge bg-primary">Titular Fixo</span>;
    } else {
        btnHtml = 
            <button class="btn-grid" onclick='abrirModalDiretor()' title="Editar Substituto"><i class="fas fa-edit text-primary"></i></button>
            <button class="btn-grid" onclick="excluirDiretor()" title="Excluir Substituto"><i class="fas fa-trash text-danger"></i></button>
        ;
    }
    
    let icone = d.is_titular === 1 ? '<i class="fas fa-check-circle text-primary ms-1" title="Titular Oficial"></i>' : '';
    
    tr.innerHTML = 
      <td class="fw-bold text-dark"></td>
      <td> </td>
      <td class="small text-muted"></td>
      <td class="text-center"></td>
    ;
    tbody.appendChild(tr);
  });
}

window.abrirModalDiretor = function(diretor = null) {
    if (diretor && diretor.id) {
        document.getElementById("tituloModalDiretor").innerHTML = '<i class="fas fa-edit text-primary me-1"></i> Editar Substituto';
        document.getElementById("dirId").value = diretor.id;
        document.getElementById("dirCargo").value = diretor.cargo;
        document.getElementById("dirNome").value = diretor.nome;
        document.getElementById("dirPortaria").value = diretor.portaria;
    } else {
        document.getElementById("tituloModalDiretor").innerHTML = '<i class="fas fa-file-signature text-warning me-1"></i> Novo Substituto';
        document.getElementById("formDiretor").reset();
        document.getElementById("dirId").value = "";
    }
    abrirModal("modalDiretor");
};

window.salvarDiretor = function(e) {
    e.preventDefault();
    const id = document.getElementById("dirId").value;
    const cargo = document.getElementById("dirCargo").value.trim();
    const nome = document.getElementById("dirNome").value.trim();
    const portaria = document.getElementById("dirPortaria").value.trim();
    
    const payload = {
        acao: id ? "EDITAR" : "CRIAR",
        id: id || null,
        cargo: cargo,
        nome: nome,
        portaria: portaria
    };
    
    fetch('/api/diretores', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(res => {
        if(res.sucesso) {
            fecharModal("modalDiretor");
            carregarParametros();
            if(window.carregarCombosCautela) window.carregarCombosCautela();
        } else {
            alert("Erro ao salvar diretor: " + res.erro);
        }
    })
    .catch(err => alert("Erro de rede: " + err));
};

window.excluirDiretor = function(id) {
    if (!confirm("Tem certeza que deseja remover este substituto?")) return;
    fetch('/api/diretores', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ acao: "EXCLUIR", id: id })
    })
    .then(r => r.json())
    .then(res => {
        if(res.sucesso) {
            carregarParametros();
        } else {
            alert("Erro ao excluir: " + res.erro);
        }
    });
};
'''

conteudo += funcoes_diretores

with open('static/js/app.js', 'w', encoding='utf-8') as f:
    f.write(conteudo)
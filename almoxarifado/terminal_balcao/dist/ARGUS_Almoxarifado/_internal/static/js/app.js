// ARGUS Almoxarifado - Frontend JavaScript (4 Etapas Canônicas, WMS 3D, Dupla Unidade & Controle PAO)
let catalogoCache = [];
let parametrosCache = {};
let latasAbertasCache = [];
let operadorAtivo = null;

document.addEventListener("DOMContentLoaded", () => {
  atualizarRelogio();
  setInterval(atualizarRelogio, 30000);
  verificarSessaoAuth();
  carregarStatus();
  carregarParametros();
  carregarHistoricoEntradas();
  carregarFerramentasEmUso();
  carregarLatasAbertas();
});


function atualizarRelogio() {
  const agora = new Date();
  const h = String(agora.getHours()).padStart(2, '0');
  const m = String(agora.getMinutes()).padStart(2, '0');
  document.getElementById("txtHora").innerText = `${h}:${m}`;
}

// ---------------------------------------------------------------------------
// NAVEGAÇÃO ENTRE AS 4 ETAPAS PRINCIPAIS
// ---------------------------------------------------------------------------
function trocarAbaPrincipal(tabId) {
  document.querySelectorAll(".tab-view").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".nav-pill-btn").forEach(el => el.classList.remove("active"));

  const targetTab = document.getElementById(tabId);
  if (targetTab) targetTab.classList.add("active");

  const botoes = Array.from(document.querySelectorAll(".nav-pill-btn"));
  const idx = ["tabEntradas", "tabSaidas", "tabSaldos", "tabGerenciar"].indexOf(tabId);
  if (idx !== -1 && botoes[idx]) {
    botoes[idx].classList.add("active");
  }

  if (tabId === "tabEntradas") carregarHistoricoEntradas();
  if (tabId === "tabSaidas") {
    carregarFerramentasEmUso();
    carregarLatasAbertas();
  }
  if (tabId === "tabSaldos") filtrarSaldos("");
  if (tabId === "tabGerenciar") filtrarGerenciarMateriais("");
}

// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// SUB-ABAS DA ETAPA 2 (SAÍDAS & DEVOLUÇÕES)
// ---------------------------------------------------------------------------
function trocarSubAbaSaidas(subId) {
  const elConsumo = document.getElementById("subSaidaConsumo");
  const elEmprestimo = document.getElementById("subEmprestimo");
  const elRetorno = document.getElementById("subRetornoSobra");

  if (elConsumo) elConsumo.style.display = (subId === "subSaidaConsumo") ? "block" : "none";
  if (elEmprestimo) elEmprestimo.style.display = (subId === "subEmprestimo") ? "block" : "none";
  if (elRetorno) elRetorno.style.display = (subId === "subRetornoSobra") ? "block" : "none";

  const botoes = document.querySelectorAll("#tabSaidas .sub-tabs-bar .sub-tab-btn");
  botoes.forEach(b => b.classList.remove("active"));
  
  if (subId === "subSaidaConsumo" && botoes[0]) {
    botoes[0].classList.add("active");
  }
  if (subId === "subEmprestimo" && botoes[1]) {
    botoes[1].classList.add("active");
  }
  if (subId === "subRetornoSobra" && botoes[2]) {
    botoes[2].classList.add("active");
    carregarLatasAbertas();
  }
}

function trocarSubAbaSaldos(subId) {
  const elSaldos = document.getElementById("subSaldosEstoque");
  const elExtrato = document.getElementById("subExtrato");

  if (elSaldos) elSaldos.style.display = (subId === "subSaldosEstoque") ? "block" : "none";
  if (elExtrato) elExtrato.style.display = (subId === "subExtrato") ? "block" : "none";

  const botoes = document.querySelectorAll("#tabSaldos .sub-tab-btn");
  botoes.forEach(b => b.classList.remove("active"));
  if (subId === "subSaldosEstoque") {
    if (botoes[0]) botoes[0].classList.add("active");
    filtrarSaldos("");
  } else {
    if (botoes[1]) botoes[1].classList.add("active");
    carregarExtrato();
  }
}

function trocarSubAbaGerenciar(subId) {
  const elCat = document.getElementById("subGerenciarCatalogo");
  const elParam = document.getElementById("subGerenciarParametros");

  if (elCat) elCat.style.display = (subId === "subGerenciarCatalogo") ? "block" : "none";
  if (elParam) elParam.style.display = (subId === "subGerenciarParametros") ? "block" : "none";

  const botoes = document.querySelectorAll("#tabGerenciar .sub-tab-btn");
  botoes.forEach(b => b.classList.remove("active"));
  if (subId === "subGerenciarCatalogo") {
    if (botoes[0]) botoes[0].classList.add("active");
    filtrarGerenciarMateriais("");
  } else {
    if (botoes[1]) botoes[1].classList.add("active");
    carregarParametrosListas();
  }
}

function abrirModal(id) {
  document.getElementById(id).style.display = "flex";
}

function fecharModal(id) {
  document.getElementById(id).style.display = "none";
}

// ---------------------------------------------------------------------------
// STATUS E CARGA DE DADOS
// ---------------------------------------------------------------------------
async function carregarStatus() {
  try {
    const res = await fetch("/api/status");
    const d = await res.json();
    document.getElementById("numItens").innerText = d.total_itens;
    if (document.getElementById("badgeTotalGeral")) {
      document.getElementById("badgeTotalGeral").innerText = d.total_itens;
    }
    document.getElementById("numFerramentasEmprestadas").innerText = d.ferramentas_em_uso;
    document.getElementById("countEmpUso").innerText = d.ferramentas_em_uso;
    document.getElementById("numBaixo").innerText = d.itens_baixo;
    if (document.getElementById("countLatasAbertas")) {
      document.getElementById("countLatasAbertas").innerText = d.latas_abertas || 0;
    }
    if (document.getElementById("numLatasAbertas")) {
      document.getElementById("numLatasAbertas").innerText = d.latas_abertas || 0;
    }
  } catch (e) {
    console.error("Erro status:", e);
  }
}

async function carregarParametros() {
  try {
    const res = await fetch("/api/parametros");
    const d = await res.json();
    parametrosCache = d;

    // Popula Selects de Saída Consumo
    preencherSelect("saidaSolicitante", d.solicitantes.map(s => s.valor));
    preencherSelect("saidaProjeto", d.projetos.map(p => p.valor));
    preencherSelect("saidaAmbiente", d.ambientes.map(a => a.valor));

    // Popula Selects de Empréstimo Ferramenta
    preencherSelect("empSolicitante", d.solicitantes.map(s => s.valor));
    preencherSelect("empProjeto", d.projetos.map(p => p.valor));

    // Popula Selects de Entrada
    preencherSelect("entProjeto", d.projetos.map(p => p.valor));

    // Popula Selects de Devolução de Sobras
    preencherSelect("sobraSolicitante", d.solicitantes.map(s => s.valor));
    preencherSelect("sobraProjeto", d.projetos.map(p => p.valor));

    // Itens de Consumo
    const selMat = document.getElementById("saidaItem");
    selMat.innerHTML = "<option value=''>--- Selecione o Insumo ---</option>";
    d.materiais.filter(m => m.categoria === "CONSUMO").forEach(m => {
      const opt = document.createElement("option");
      opt.value = m.id;
      opt.text = `${m.descricao} (${m.unidade_base})`;
      selMat.appendChild(opt);
    });

    // Ferramentas
    const selFer = document.getElementById("empFerramenta");
    selFer.innerHTML = "<option value=''>--- Selecione a Ferramenta ---</option>";
    d.ferramentas.forEach(f => {
      const opt = document.createElement("option");
      opt.value = f.id;
      opt.text = f.descricao;
      selFer.appendChild(opt);
    });

    // Itens para Entrada
    const selEnt = document.getElementById("entMaterial");
    selEnt.innerHTML = "<option value=''>--- Selecione o Material ---</option>";
    d.materiais.forEach(m => {
      const opt = document.createElement("option");
      opt.value = m.id;
      opt.text = `${m.descricao} [${m.embalagem_compra || m.unidade_base}]`;
      selEnt.appendChild(opt);
    });

    // Itens para Retorno de Sobra
    const selSobra = document.getElementById("sobraMaterial");
    selSobra.innerHTML = "<option value=''>--- Selecione o Material / Lata ---</option>";
    d.materiais.forEach(m => {
      const opt = document.createElement("option");
      opt.value = m.id;
      opt.text = `${m.descricao} (${m.unidade_base})`;
      selSobra.appendChild(opt);
    });

  } catch (e) {
    console.error("Erro parametros:", e);
  }
}

function preencherSelect(elemId, lista) {
  const el = document.getElementById(elemId);
  if (!el) return;
  el.innerHTML = "<option value=''>--- Selecione ---</option>";
  lista.forEach(val => {
    const opt = document.createElement("option");
    opt.value = val;
    opt.text = val;
    el.appendChild(opt);
  });
}

// ---------------------------------------------------------------------------
// ETAPA 1: ENTRADAS COM CONVERSÃO DUPLA DE UNIDADE
// ---------------------------------------------------------------------------
function aoSelecionarMaterialEntrada(matId) {
  const mat = parametrosCache.materiais ? parametrosCache.materiais.find(m => m.id === matId) : null;
  const infoEl = document.getElementById("infoEmbalagemEntrada");
  const txtEmb = document.getElementById("txtNomeEmb");
  const txtBase = document.getElementById("txtNomeUnidBase");

  if (!mat) {
    infoEl.innerHTML = "";
    txtEmb.innerText = "Embalagem";
    txtBase.innerText = "UN";
    return;
  }

  txtEmb.innerText = mat.embalagem_compra || "Embalagem";
  txtBase.innerText = mat.unidade_base || "UN";
  infoEl.innerHTML = `📦 <b>Embalagem Comercial:</b> ${mat.embalagem_compra} | 📏 <b>Contém:</b> ${mat.fator_conversao} ${mat.unidade_base}`;
  atualizarPreviewEntrada();
}

function atualizarPreviewEntrada() {
  const matId = document.getElementById("entMaterial").value;
  const qtd = parseFloat(document.getElementById("entQtd").value) || 0;
  const emEmb = document.getElementById("radEntEmb").checked;
  const previewEl = document.getElementById("txtPreviewCreditoBase");

  const mat = parametrosCache.materiais ? parametrosCache.materiais.find(m => m.id === matId) : null;
  if (!mat || qtd <= 0) {
    previewEl.innerHTML = "";
    return;
  }

  const fator = parseFloat(mat.fator_conversao) || 1.0;
  const qtdBase = emEmb ? (qtd * fator) : qtd;
  previewEl.innerHTML = `👉 <b>Serão creditados no estoque:</b> ${qtdBase.toFixed(2)} ${mat.unidade_base}`;
}

async function salvarNovaEntrada(e) {
  e.preventDefault();
  const matId = document.getElementById("entMaterial").value;
  const emEmb = document.getElementById("radEntEmb").checked;

  const payload = {
    material_id: matId,
    quantidade: parseFloat(document.getElementById("entQtd").value),
    em_embalagem: emEmb,
    nf: document.getElementById("entNf").value,
    fornecedor: document.getElementById("entFornecedor").value,
    valor_unit: parseFloat(document.getElementById("entValorUnit").value || 0),
    projeto: document.getElementById("entProjeto").value
  };

  try {
    const res = await fetch("/api/entrada", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const d = await res.json();
    if (d.sucesso) {
      fecharModal("modalNovaEntrada");
      document.getElementById("formEntrada").reset();
      document.getElementById("infoEmbalagemEntrada").innerHTML = "";
      document.getElementById("txtPreviewCreditoBase").innerHTML = "";
      alert("Entrada registrada com sucesso! Saldo de estoque recomposto.");
      carregarHistoricoEntradas();
      carregarStatus();
    } else {
      alert("Erro ao registrar entrada: " + d.erro);
    }
  } catch (err) {
    alert("Falha de conexão com o servidor.");
  }
}

async function carregarHistoricoEntradas() {
  const listaEl = document.getElementById("listaEntradasRecentes");
  listaEl.innerHTML = "<p style='font-size:0.75rem; color:#6B7280;'>Carregando entradas...</p>";

  try {
    const res = await fetch("/api/entradas");
    const entradas = await res.json();
    if (entradas.length === 0) {
      listaEl.innerHTML = "<p style='font-size:0.75rem; color:#6B7280;'>Nenhuma entrada recente registrada.</p>";
      return;
    }

    listaEl.innerHTML = "";
    entradas.forEach(ent => {
      const card = document.createElement("div");
      card.className = "list-item-card";
      card.innerHTML = `
        <div>
          <div style="font-size:0.8rem; font-weight:700;">${ent.material_nome}</div>
          <div style="font-size:0.7rem; color:#6B7280;">NF: ${ent.nf} • ${ent.fornecedor} • ${ent.data_hora}</div>
        </div>
        <div style="text-align:right;">
          <div style="font-size:0.9rem; font-weight:800; color:var(--argus-primary);">+${ent.quantidade_base} ${ent.unidade_base}</div>
          <div style="font-size:0.65rem; color:#6B7280;">${ent.quantidade_compra} ${ent.unidade_compra} • ${ent.projeto}</div>
        </div>
      `;
      listaEl.appendChild(card);
    });
  } catch (e) {
    listaEl.innerHTML = "<p style='color:red;'>Erro ao carregar entradas.</p>";
  }
}

// ---------------------------------------------------------------------------
// ETAPA 2: SAÍDAS DE CONSUMO COM CONTROLE PAO
// ---------------------------------------------------------------------------
function aoSelecionarItemConsumo(matId) {
  const mat = parametrosCache.materiais ? parametrosCache.materiais.find(m => m.id === matId) : null;
  const lblUnid = document.getElementById("lblUnidadeConsumo");
  const infoUnid = document.getElementById("infoUnidadeConsumo");
  const boxPao = document.getElementById("boxPaoConsumo");

  if (!mat) {
    lblUnid.innerText = "UN";
    infoUnid.innerText = "";
    boxPao.style.display = "none";
    return;
  }

  lblUnid.innerText = mat.unidade_base;
  infoUnid.innerText = `Unidade de Medida de Estoque: ${mat.unidade_base} (Embalagem de compra: ${mat.embalagem_compra})`;

  // Se for produto com controle PAO (líquido/tinta)
  if (mat.unidade_base === "L" || (mat.validade_pao_dias && mat.validade_pao_dias > 0)) {
    boxPao.style.display = "block";
  } else {
    boxPao.style.display = "none";
  }
}

async function salvarSaidaConsumo(e) {
  e.preventDefault();
  const matId = document.getElementById("saidaItem").value;
  const abrirLata = document.getElementById("saidaAbrirLata") ? document.getElementById("saidaAbrirLata").checked : false;

  const payload = {
    solicitante: document.getElementById("saidaSolicitante").value,
    siape: document.getElementById("saidaSiape").value,
    projeto: document.getElementById("saidaProjeto").value,
    ambiente: document.getElementById("saidaAmbiente").value,
    material_id: matId,
    quantidade: parseFloat(document.getElementById("saidaQtd").value),
    finalidade: document.getElementById("saidaFinalidade").value,
    abrir_nova_lata: abrirLata
  };

  try {
    const res = await fetch("/api/saida_consumo", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const d = await res.json();
    if (d.sucesso) {
      document.getElementById("formSaidaConsumo").reset();
      document.getElementById("infoUnidadeConsumo").innerText = "";
      document.getElementById("boxPaoConsumo").style.display = "none";

      document.getElementById("sucTitulo").innerText = "Saída de Consumo Confirmada!";
      let textoSuc = `Recibo Nº: ${d.num_recibo}\nItem: ${d.descricao}\nQtd: ${d.quantidade} ${d.unidade}`;
      if (d.fracionado_id) {
        textoSuc += `\n\n🥫 LATA ABERTA REGISTRADA: ${d.fracionado_id}\nEtiqueta lateral gerada com régua de nível!`;
      }
      document.getElementById("sucTexto").innerText = textoSuc;
      document.getElementById("btnVerPdf").href = `/api/comprovante/${d.pdf_nome}`;
      abrirModal("modalSucesso");

      carregarStatus();
      carregarLatasAbertas();
    } else {
      alert("Erro ao registrar saída: " + d.erro);
    }
  } catch (err) {
    alert("Falha na comunicação com o servidor.");
  }
}

// ---------------------------------------------------------------------------
// ETAPA 2: EMPRÉSTIMO & DEVOLUÇÃO DE FERRAMENTAS
// ---------------------------------------------------------------------------
async function salvarEmprestimoFerramenta(e) {
  e.preventDefault();
  const payload = {
    solicitante: document.getElementById("empSolicitante").value,
    siape: document.getElementById("empSiape").value,
    projeto: document.getElementById("empProjeto").value,
    material_id: document.getElementById("empFerramenta").value,
    data_prevista: document.getElementById("empDataPrev").value
  };

  try {
    const res = await fetch("/api/emprestimo_ferramenta", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const d = await res.json();
    if (d.sucesso) {
      document.getElementById("formEmprestimo").reset();
      document.getElementById("sucTitulo").innerText = "Empréstimo Registrado!";
      document.getElementById("sucTexto").innerText = `Termo de Cautela Nº: ${d.num_recibo}\nFerramenta: ${d.equipamento}\nResponsável: ${d.solicitante}`;
      document.getElementById("btnVerPdf").href = `/api/comprovante/${d.pdf_nome}`;
      abrirModal("modalSucesso");
      carregarStatus();
      carregarFerramentasEmUso();
    } else {
      alert("Erro ao registrar empréstimo: " + d.erro);
    }
  } catch (err) {
    alert("Falha na comunicação.");
  }
}

async function carregarFerramentasEmUso() {
  const listaEl = document.getElementById("listaFerramentasEmUso");
  listaEl.innerHTML = "<p style='font-size:0.75rem; color:#6B7280;'>Carregando ferramentas em empréstimo...</p>";

  try {
    const res = await fetch("/api/ferramentas_em_uso");
    const emps = await res.json();
    document.getElementById("countEmpUso").innerText = emps.length;
    document.getElementById("numFerramentasEmprestadas").innerText = emps.length;

    if (emps.length === 0) {
      listaEl.innerHTML = "<p style='padding:16px; text-align:center; color:#10B981; font-weight:700;'>Nenhuma ferramenta emprestada no momento!</p>";
      return;
    }

    listaEl.innerHTML = "";
    emps.forEach(emp => {
      const card = document.createElement("div");
      card.className = "list-item-card";
      card.innerHTML = `
        <div>
          <div style="font-size:0.85rem; font-weight:700;">${emp.ferramenta_nome}</div>
          <div style="font-size:0.75rem; color:#4B5563;">${emp.solicitante} (${emp.projeto})</div>
          <div style="font-size:0.7rem; color:#9CA3AF;">Saída: ${emp.data_saida} • Retorno: ${emp.data_prevista || 'A combinar'}</div>
        </div>
        <button class="btn-action-primary" style="padding:6px 12px; font-size:0.75rem; width:auto;" onclick="abrirChecklistDev('${emp.id}', '${emp.ferramenta_nome}', '${emp.solicitante}')">Devolver</button>
      `;
      listaEl.appendChild(card);
    });
  } catch (e) {
    listaEl.innerHTML = "<p style='color:red;'>Erro ao carregar ferramentas.</p>";
  }
}

function abrirChecklistDev(id, ferramenta, solic) {
  document.getElementById("devEmpId").value = id;
  document.getElementById("devEmpFerramenta").innerText = ferramenta;
  document.getElementById("devEmpSolicitante").innerText = `Responsável: ${solic}`;
  document.getElementById("devEmpObs").value = "";
  toggleObsDev(false);
  abrirModal("modalChecklistDev");
}

function toggleObsDev(mostrar) {
  document.getElementById("boxObsDev").style.display = mostrar ? "flex" : "none";
}

async function confirmarDevolucaoFerramenta() {
  const idEmp = document.getElementById("devEmpId").value;
  const condicao = document.querySelector('input[name="radCondicao"]:checked').value;
  const semAvarias = (condicao === "OK");
  const obs = document.getElementById("devEmpObs").value;

  try {
    const res = await fetch("/api/devolver_ferramenta", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({id_emprestimo: idEmp, sem_avarias: semAvarias, obs: obs})
    });
    const d = await res.json();
    if (d.sucesso) {
      fecharModal("modalChecklistDev");
      alert("Ferramenta devolvida ao almoxarifado! Saldo estornado.");
      carregarFerramentasEmUso();
      carregarStatus();
    } else {
      alert("Erro ao devolver ferramenta.");
    }
  } catch (e) {
    alert("Falha de conexão.");
  }
}

// ---------------------------------------------------------------------------
// ETAPA 2: RETORNO DE SOBRAS (LATAS DE TINTA & CABOS)
// ---------------------------------------------------------------------------
function aoSelecionarMaterialSobra(matId) {
  const mat = parametrosCache.materiais ? parametrosCache.materiais.find(m => m.id === matId) : null;
  const boxLata = document.getElementById("boxNivelLata");
  const boxManual = document.getElementById("boxQtdManualSobra");
  const lblUnid = document.getElementById("lblUnidadeSobra");

  if (!mat) {
    boxLata.style.display = "none";
    boxManual.style.display = "none";
    return;
  }

  lblUnid.innerText = mat.unidade_base;

  // Se for líquido/tinta com embalagem (L), mostra os 4 botões de frações
  if (mat.unidade_base === "L") {
    boxLata.style.display = "flex";
    boxManual.style.display = "none";
    document.querySelectorAll(".btn-fracao").forEach(b => b.classList.remove("selected"));
    document.getElementById("sobraFracao").value = "";
    document.getElementById("txtSobraCalculada").innerText = "";
  } else {
    // Se for cabo (m) ou outro, mostra o campo manual
    boxLata.style.display = "none";
    boxManual.style.display = "block";
  }
}

function selecionarFracao(valor, texto, elem) {
  document.querySelectorAll(".btn-fracao").forEach(b => b.classList.remove("selected"));
  elem.classList.add("selected");
  document.getElementById("sobraFracao").value = valor;

  const matId = document.getElementById("sobraMaterial").value;
  const mat = parametrosCache.materiais ? parametrosCache.materiais.find(m => m.id === matId) : null;
  if (mat) {
    const fator = parseFloat(mat.fator_conversao) || 18.0;
    const vol = valor * fator;
    document.getElementById("txtSobraCalculada").innerText = `✅ Retornarão ao estoque: ${vol.toFixed(2)} ${mat.unidade_base} (${texto})`;
  }
}

async function salvarRetornoSobra(e) {
  e.preventDefault();
  const matId = document.getElementById("sobraMaterial").value;
  const mat = parametrosCache.materiais ? parametrosCache.materiais.find(m => m.id === matId) : null;
  if (!mat) return alert("Selecione o material.");

  const payload = {
    solicitante: document.getElementById("sobraSolicitante").value,
    projeto: document.getElementById("sobraProjeto").value,
    material_id: matId
  };

  if (mat.unidade_base === "L") {
    const fracao = document.getElementById("sobraFracao").value;
    if (fracao === "") return alert("Selecione o nível na régua tátil (75%, 50%, 25% ou 0%)!");
    payload.fracao = parseFloat(fracao);
  } else {
    const qtdManual = parseFloat(document.getElementById("sobraQtdManual").value);
    if (!qtdManual || qtdManual <= 0) return alert("Digite a quantidade de metros/peças devolvidas!");
    payload.quantidade = qtdManual;
  }

  try {
    const res = await fetch("/api/retorno_sobra", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const d = await res.json();
    if (d.sucesso) {
      document.getElementById("formRetornoSobra").reset();
      document.getElementById("boxNivelLata").style.display = "none";
      document.getElementById("boxQtdManualSobra").style.display = "none";
      document.getElementById("txtSobraCalculada").innerText = "";
      alert(`Sobra registrada com sucesso!\n• Recomposto no estoque: +${d.qtd_retornada} ${d.unidade}`);
      carregarStatus();
      carregarLatasAbertas();
    } else {
      alert("Erro ao registrar retorno: " + d.erro);
    }
  } catch (err) {
    alert("Falha de conexão.");
  }
}

async function carregarLatasAbertas() {
  const listaEl = document.getElementById("listaLatasAbertas");
  if (!listaEl) return;
  listaEl.innerHTML = "<p style='font-size:0.75rem; color:#6B7280;'>Carregando latas abertas...</p>";

  try {
    const res = await fetch("/api/fracionados_abertos");
    const latas = await res.json();
    latasAbertasCache = latas;

    if (document.getElementById("countLatasAbertas")) {
      document.getElementById("countLatasAbertas").innerText = latas.length;
    }

    if (latas.length === 0) {
      listaEl.innerHTML = "<p style='font-size:0.75rem; color:#10B981; font-weight:600;'>Nenhuma lata aberta pendente no momento.</p>";
      return;
    }

    listaEl.innerHTML = "";
    latas.forEach(l => {
      const card = document.createElement("div");
      card.className = "list-item-card";
      card.innerHTML = `
        <div style="flex:1;">
          <div style="font-size:0.85rem; font-weight:700;">${l.descricao}</div>
          <div style="font-size:0.72rem; color:#4B5563;"><b>${l.id}</b> • Abertura: ${l.data_abertura}</div>
          <div style="display:flex; gap:6px; margin-top:3px; align-items:center;">
            <span class="badge-pao">⏱️ Vence PAO: ${l.data_vencimento_pao}</span>
            <span style="font-size:0.7rem; font-weight:700; color:var(--argus-primary);">Nível: ${l.nivel_atual} (~${l.saldo_remanescente} ${l.unidade_base})</span>
          </div>
        </div>
        <div style="display:flex; flex-direction:column; gap:4px;">
          <button class="btn-action-primary" style="padding:4px 8px; font-size:0.7rem;" onclick="prepararDevolucaoLata('${l.material_id}', '${l.aberto_por}')">↩️ Devolver</button>
          <a class="btn-etiqueta" href="/api/etiqueta_lata/${l.id}" target="_blank">🥫 Etiqueta</a>
        </div>
      `;
      listaEl.appendChild(card);
    });
  } catch (e) {
    listaEl.innerHTML = "<p style='color:red;'>Erro ao carregar latas abertas.</p>";
  }
}

function prepararDevolucaoLata(matId, solic) {
  document.getElementById("sobraMaterial").value = matId;
  aoSelecionarMaterialSobra(matId);
  if (solic) {
    document.getElementById("sobraSolicitante").value = solic;
  }
  window.scrollTo({top: 0, behavior: 'smooth'});
}

// ---------------------------------------------------------------------------
// ETAPA 3: SALDOS COM ENDEREÇO WMS 3D & ETIQUETAS (TABELA CORPORATIVA)
// ---------------------------------------------------------------------------
let timerBuscaSaldo = null;
function filtrarSaldos(termo) {
  clearTimeout(timerBuscaSaldo);
  timerBuscaSaldo = setTimeout(async () => {
    const tbody = document.getElementById("tabelaSaldosBody");
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="8" class="text-center py-3 text-muted"><i class="fas fa-spinner fa-spin me-2"></i>Consultando saldos físicos...</td></tr>';

    try {
      const res = await fetch(`/api/catalogo?filtro=${encodeURIComponent(termo)}`);
      const itens = await res.json();

      if (itens.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-muted"><i class="fas fa-box-open me-2"></i>Nenhum item encontrado no estoque.</td></tr>';
        return;
      }

      tbody.innerHTML = "";
      itens.forEach(it => {
        const isBaixo = (it.status_estoque === "BAIXO");
        const isLiquido = (it.unidade_base === "L");
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td class="text-center">
            <span class="badge bg-light text-dark border font-monospace"><b>${it.id}</b></span>
          </td>
          <td>
            <div class="fw-bold text-dark">${it.descricao}</div>
            <div class="small text-muted" style="font-size:0.7rem;">CATMAT: ${it.codigo_catmat || 'N/A'} • PDM: ${it.nome_basico || '-'}</div>
          </td>
          <td class="text-center">
            <span class="badge-cat ${it.categoria === 'FERRAMENTA' ? 'badge-cat-ferramenta' : 'badge-cat-consumo'}">${it.categoria}</span>
          </td>
          <td>
            <span class="badge-wms-tag"><i class="fas fa-location-dot text-danger"></i> ${it.endereco_3d || it.localizacao}</span>
          </td>
          <td class="text-center fw-bold" style="font-size:0.95rem; color:${isBaixo ? 'var(--bs-danger)' : 'var(--bs-primary)'};">
            ${it.saldo} <small class="text-muted" style="font-size:0.75rem;">${it.unidade_base}</small>
          </td>
          <td class="text-center small">
            ${it.embalagem_compra} <span class="text-muted">(x${it.fator_conversao})</span>
          </td>
          <td class="text-center">
            <span class="badge ${isBaixo ? 'bg-danger text-white' : 'bg-success text-white'}" style="font-size:0.68rem;">
              ${isBaixo ? 'CRÍTICO' : 'NORMAL'}
            </span>
          </td>
          <td class="text-center">
            <div class="d-flex justify-content-center gap-1">
              <a class="btn-etiqueta" href="/api/etiqueta_prateleira/${it.id}" target="_blank" title="Etiqueta WMS 3D"><i class="fas fa-barcode"></i> WMS</a>
              ${isLiquido ? `<a class="btn-etiqueta" href="/api/etiqueta_lata/${it.id}" target="_blank" title="Etiqueta PAO Régua"><i class="fas fa-paint-roller"></i></a>` : ''}
            </div>
          </td>
        `;
        tbody.appendChild(tr);
      });
    } catch (e) {
      tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-danger">Erro ao carregar saldos.</td></tr>';
    }
  }, 150);
}

async function carregarExtrato() {
  const tbody = document.getElementById("tabelaExtratoBody");
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="7" class="text-center py-3 text-muted"><i class="fas fa-spinner fa-spin me-2"></i>Carregando extrato de movimentações...</td></tr>';

  try {
    const res = await fetch("/api/extrato");
    const movs = await res.json();

    if (movs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">Nenhuma movimentação registrada até o momento.</td></tr>';
      return;
    }

    tbody.innerHTML = "";
    movs.forEach(m => {
      const isEntrada = (m.tipo === "ENTRADA");
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="text-center small text-muted">${m.data}</td>
        <td class="text-center">
          <span class="badge ${isEntrada ? 'bg-success text-white' : 'bg-danger text-white'}" style="font-size:0.7rem;">
            ${m.tipo}
          </span>
        </td>
        <td class="fw-bold small">${m.material}</td>
        <td class="small">${m.agente}</td>
        <td class="small text-muted">${m.projeto}</td>
        <td class="text-center fw-bold ${isEntrada ? 'text-success' : 'text-danger'}" style="font-size:0.9rem;">
          ${isEntrada ? '+' : '-'}${m.quantidade} ${m.unidade}
        </td>
        <td class="text-center small font-monospace text-muted">${m.ref_doc || '-'}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-danger">Erro ao carregar extrato.</td></tr>';
  }
}

// ---------------------------------------------------------------------------
// ETAPA 4: GERENCIAR (CRUD COMPLETO DO LEGADO COM PDM & WMS 3D)
// ---------------------------------------------------------------------------
let timerBuscaGerenciar = null;
function filtrarGerenciarMateriais(termo) {
  clearTimeout(timerBuscaGerenciar);
  timerBuscaGerenciar = setTimeout(async () => {
    const tbody = document.getElementById("tabelaGerenciarBody");
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="9" class="text-center py-3 text-muted"><i class="fas fa-spinner fa-spin me-2"></i>Carregando catálogo completo...</td></tr>';

    try {
      const res = await fetch(`/api/catalogo?filtro=${encodeURIComponent(termo)}&todos=1`);
      const itens = await res.json();
      catalogoCache = itens;

      if (itens.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center py-4 text-muted"><i class="fas fa-boxes-packing me-2"></i>Nenhum material cadastrado.</td></tr>';
        return;
      }

      tbody.innerHTML = "";
      itens.forEach(it => {
        const inativo = (it.ativo === 0);
        const tr = document.createElement("tr");
        if (inativo) tr.style.opacity = "0.5";

        tr.innerHTML = `
          <td class="text-center">
            <span class="badge bg-light text-dark border font-monospace"><b>${it.id}</b></span>
          </td>
          <td class="text-center small font-monospace">${it.codigo_catmat || '-'}</td>
          <td>
            <div class="fw-bold text-dark">${it.descricao} ${inativo ? '<span class="badge bg-secondary ms-1">INATIVO</span>' : ''}</div>
            <div class="small text-muted" style="font-size:0.7rem;">${it.nome_basico || ''} ${it.nome_modificador ? '• ' + it.nome_modificador : ''}</div>
          </td>
          <td class="text-center">
            <span class="badge-cat ${it.categoria === 'FERRAMENTA' ? 'badge-cat-ferramenta' : 'badge-cat-consumo'}">${it.categoria}</span>
          </td>
          <td class="text-center fw-bold">${it.unidade_base}</td>
          <td class="text-center small">${it.embalagem_compra} <span class="text-muted">(x${it.fator_conversao})</span></td>
          <td>
            <span class="badge-wms-tag"><i class="fas fa-location-dot text-danger"></i> ${it.endereco_3d || it.localizacao}</span>
          </td>
          <td class="text-center fw-bold">${it.saldo}</td>
          <td class="text-center">
            <div class="d-flex justify-content-center gap-1">
              <button class="btn-crud-edit" style="padding:4px 8px; font-size:0.75rem;" onclick="abrirModalEditarMaterial('${it.id}')" title="Editar Material"><i class="fas fa-pen"></i></button>
              <button class="btn-crud-delete" style="padding:4px 8px; font-size:0.75rem;" onclick="excluirMaterial('${it.id}', '${it.descricao}')" title="Excluir Material"><i class="fas fa-trash"></i></button>
            </div>
          </td>
        `;
        tbody.appendChild(tr);
      });
    } catch (e) {
      tbody.innerHTML = '<tr><td colspan="9" class="text-center py-4 text-danger">Erro ao carregar catálogo.</td></tr>';
    }
  }, 150);
}

function abrirModalNovoMaterial() {
  document.getElementById("titModalMaterial").innerText = "➕ Cadastrar Novo Material";
  document.getElementById("matCrudId").value = "";
  document.getElementById("matCrudCatmat").value = "";
  document.getElementById("matCrudCat").value = "CONSUMO";
  document.getElementById("matCrudNomeBasico").value = "";
  document.getElementById("matCrudNomeModificador").value = "";
  document.getElementById("matCrudDesc").value = "";
  document.getElementById("matCrudUnidBase").value = "UN";
  document.getElementById("matCrudEmbCompra").value = "UN";
  document.getElementById("matCrudFator").value = "1.0";
  document.getElementById("matCrudEstoqueIni").value = "0";
  document.getElementById("matCrudEstoqueMin").value = "2";
  document.getElementById("matCrudPao").value = "0";
  document.getElementById("matCrudAmbiente").value = "ALMOXARIFADO CENTRAL";
  document.getElementById("matCrudEstrutura").value = "ESTANTE 01";
  document.getElementById("matCrudPosicao").value = "PRATELEIRA 01";
  document.getElementById("matCrudMotivo").value = "Cadastro PDM inicial";
  abrirModal("modalFormMaterial");
}

function abrirModalEditarMaterial(id) {
  const item = catalogoCache.find(i => i.id === id);
  if (!item) return;

  document.getElementById("titModalMaterial").innerText = `✏️ Editar SKU: ${item.id}`;
  document.getElementById("matCrudId").value = item.id;
  document.getElementById("matCrudCatmat").value = item.codigo_catmat || "";
  document.getElementById("matCrudCat").value = item.categoria;
  document.getElementById("matCrudNomeBasico").value = item.nome_basico || "";
  document.getElementById("matCrudNomeModificador").value = item.nome_modificador || "";
  document.getElementById("matCrudDesc").value = item.descricao;
  document.getElementById("matCrudUnidBase").value = item.unidade_base || "UN";
  document.getElementById("matCrudEmbCompra").value = item.embalagem_compra || "UN";
  document.getElementById("matCrudFator").value = item.fator_conversao || 1.0;
  document.getElementById("matCrudEstoqueIni").value = item.estoque_inicial;
  document.getElementById("matCrudEstoqueMin").value = item.estoque_minimo;
  document.getElementById("matCrudPao").value = item.validade_pao_dias || 0;
  document.getElementById("matCrudAmbiente").value = item.local_ambiente || "ALMOXARIFADO CENTRAL";
  document.getElementById("matCrudEstrutura").value = item.local_estrutura || "ESTANTE 01";
  document.getElementById("matCrudPosicao").value = item.local_posicao || "PRATELEIRA 01";
  document.getElementById("matCrudMotivo").value = item.motivo_ajuste || "Revisão e normalização PDM";
  abrirModal("modalFormMaterial");
}

async function salvarMaterialCrud(e) {
  e.preventDefault();
  const idMat = document.getElementById("matCrudId").value;
  const payload = {
    codigo_catmat: document.getElementById("matCrudCatmat").value,
    categoria: document.getElementById("matCrudCat").value,
    nome_basico: document.getElementById("matCrudNomeBasico").value,
    nome_modificador: document.getElementById("matCrudNomeModificador").value,
    descricao: document.getElementById("matCrudDesc").value,
    unidade_base: document.getElementById("matCrudUnidBase").value,
    embalagem_compra: document.getElementById("matCrudEmbCompra").value,
    fator_conversao: parseFloat(document.getElementById("matCrudFator").value || 1.0),
    estoque_inicial: parseFloat(document.getElementById("matCrudEstoqueIni").value || 0),
    estoque_minimo: parseFloat(document.getElementById("matCrudEstoqueMin").value || 2),
    validade_pao_dias: parseInt(document.getElementById("matCrudPao").value || 0),
    local_ambiente: document.getElementById("matCrudAmbiente").value,
    local_estrutura: document.getElementById("matCrudEstrutura").value,
    local_posicao: document.getElementById("matCrudPosicao").value,
    motivo_ajuste: document.getElementById("matCrudMotivo").value
  };

  const url = idMat ? `/api/material/${idMat}` : `/api/material`;
  const metodo = idMat ? "PUT" : "POST";

  try {
    const res = await fetch(url, {
      method: metodo,
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const d = await res.json();
    if (d.sucesso) {
      fecharModal("modalFormMaterial");
      alert(idMat ? "Material atualizado com sucesso!" : `Novo material cadastrado com código: ${d.id}`);
      filtrarGerenciarMateriais("");
      carregarParametros();
      carregarStatus();
    } else {
      alert("Erro ao salvar: " + d.erro);
    }
  } catch (err) {
    alert("Falha de conexão com o servidor.");
  }
}

async function excluirMaterial(id, desc) {
  if (!confirm(`Tem certeza que deseja excluir/inativar o material:\n"${desc}"?`)) {
    return;
  }

  try {
    const res = await fetch(`/api/material/${id}`, {method: "DELETE"});
    const d = await res.json();
    if (d.sucesso) {
      alert(d.acao === "INATIVADO" ? "Item inativado (preservando histórico de saídas)." : "Item removido com sucesso!");
      filtrarGerenciarMateriais("");
      carregarParametros();
      carregarStatus();
    } else {
      alert("Erro ao excluir: " + d.erro);
    }
  } catch (e) {
    alert("Falha na requisição.");
  }
}

// ---------------------------------------------------------------------------
// CRUD DE PARÂMETROS
// ---------------------------------------------------------------------------
async function carregarParametrosListas() {
  await carregarParametros();
  renderListaParams("listaParamsSolicitantes", parametrosCache.solicitantes, "SOLICITANTE");
  renderListaParams("listaParamsProjetos", parametrosCache.projetos, "PROJETO");
  renderListaParams("listaParamsAmbientes", parametrosCache.ambientes, "AMBIENTE");
}

function renderListaParams(containerId, itens, tipo) {
  const c = document.getElementById(containerId);
  if (!c) return;
  c.innerHTML = "";
  itens.forEach(item => {
    const div = document.createElement("div");
    div.style.display = "flex";
    div.style.justifyContent = "space-between";
    div.style.alignItems = "center";
    div.style.padding = "6px 10px";
    div.style.background = "#F9FAFB";
    div.style.borderRadius = "6px";
    div.style.border = "1px solid #E5E7EB";
    div.style.fontSize = "0.75rem";

    if (tipo === "SOLICITANTE") {
      div.innerHTML = `
        <div style="flex:1; overflow:hidden;">
          <div class="fw-bold text-dark text-truncate">${item.nome_completo || item.valor}</div>
          <div class="text-muted" style="font-size:0.7rem;">
            <i class="fas fa-id-card me-1 text-primary"></i>${item.cpf_formatado ? 'CPF: ' + item.cpf_formatado : 'Sem CPF registrado'}
          </div>
        </div>
        <div style="display:flex; gap:4px; margin-left:8px;">
          <button class="btn-aux" style="padding:2px 6px;" title="Editar" onclick="editarSolicitanteModal(${item.id}, '${item.nome_completo || item.valor}', '${item.cpf || ''}')">✏️</button>
          <button class="btn-aux" style="padding:2px 6px; color:red;" title="Inativar" onclick="excluirSolicitantePrompt(${item.id}, '${item.nome_completo || item.valor}')">🗑️</button>
        </div>
      `;
    } else {
      div.innerHTML = `
        <span class="text-truncate">${item.valor}</span>
        <div style="display:flex; gap:4px; margin-left:8px;">
          <button class="btn-aux" style="padding:2px 6px;" title="Editar" onclick="editarParamPrompt(${item.id}, '${item.valor}')">✏️</button>
          <button class="btn-aux" style="padding:2px 6px; color:red;" title="Excluir" onclick="excluirParamPrompt(${item.id}, '${item.valor}')">🗑️</button>
        </div>
      `;
    }
    c.appendChild(div);
  });
}

function aoSelecionarSolicitante(origem, valor) {
  if (!parametrosCache || !parametrosCache.solicitantes) return;
  const s = parametrosCache.solicitantes.find(item => item.valor === valor || item.nome_completo === valor);
  const inputSiape = (origem === "saida") ? document.getElementById("saidaSiape") : document.getElementById("empSiape");
  if (s && inputSiape && s.cpf_formatado) {
    inputSiape.value = `CPF: ${s.cpf_formatado}`;
  }
}

function abrirModalNovoSolicitante(targetSelectId = "") {
  document.getElementById("solicTargetSelectId").value = targetSelectId || "";
  document.getElementById("solicEditId").value = "";
  document.getElementById("solicNome").value = "";
  document.getElementById("solicCpf").value = "";
  document.getElementById("titModalSolicitante").innerHTML = '<i class="fas fa-user-plus text-primary me-1"></i> Cadastrar Solicitante';
  abrirModal("modalNovoSolicitante");
}

function editarSolicitanteModal(id, nome, cpf) {
  document.getElementById("solicTargetSelectId").value = "";
  document.getElementById("solicEditId").value = id;
  document.getElementById("solicNome").value = nome;
  document.getElementById("solicCpf").value = formatarMascaraCpf(cpf || "");
  document.getElementById("titModalSolicitante").innerHTML = '<i class="fas fa-pen-to-square text-primary me-1"></i> Editar Solicitante';
  abrirModal("modalNovoSolicitante");
}

async function salvarNovoSolicitante(e) {
  e.preventDefault();
  const editId = document.getElementById("solicEditId").value;
  const targetSelect = document.getElementById("solicTargetSelectId").value;
  const nome = document.getElementById("solicNome").value.trim();
  const rawCpf = document.getElementById("solicCpf").value.trim();
  const cpf = rawCpf.replace(/\D/g, "");

  if (!nome) return alert("O Nome Completo é obrigatório.");
  if (cpf.length !== 11) return alert("O CPF deve conter exatamente 11 dígitos numéricos.");

  const url = editId ? `/api/solicitante/${editId}` : `/api/solicitante`;
  const metodo = editId ? "PUT" : "POST";

  try {
    const res = await fetch(url, {
      method: metodo,
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({nome: nome, cpf: cpf})
    });
    const d = await res.json();
    if (d.sucesso) {
      fecharModal("modalNovoSolicitante");
      await carregarParametrosListas();

      if (targetSelect) {
        const el = document.getElementById(targetSelect);
        if (el) {
          el.value = nome.toUpperCase();
          if (targetSelect === "saidaSolicitante") aoSelecionarSolicitante("saida", el.value);
          if (targetSelect === "empSolicitante") aoSelecionarSolicitante("emp", el.value);
        }
      }
      alert(editId ? "Solicitante atualizado com sucesso!" : "Solicitante cadastrado com sucesso!");
    } else {
      alert("Erro ao salvar solicitante: " + (d.erro || "Tente novamente."));
    }
  } catch (err) {
    alert("Falha de conexão com o servidor.");
  }
}

async function excluirSolicitantePrompt(id, nome) {
  if (!confirm(`Deseja realmente inativar o solicitante "${nome}"?`)) return;
  try {
    const res = await fetch(`/api/solicitante/${id}`, {method: "DELETE"});
    const d = await res.json();
    if (d.sucesso) {
      await carregarParametrosListas();
    } else {
      alert("Erro ao inativar solicitante: " + d.erro);
    }
  } catch (e) {
    alert("Falha de conexão com o servidor.");
  }
}

function abrirModalNovoParametro(tipo) {
  document.getElementById("paramTipo").value = tipo;
  document.getElementById("paramId").value = "";
  document.getElementById("paramValor").value = "";
  document.getElementById("titModalParam").innerText = `➕ Novo ${tipo}`;
  abrirModal("modalParamCrud");
}

async function salvarParametroCrud() {
  const tipo = document.getElementById("paramTipo").value;
  const id = document.getElementById("paramId").value;
  const valor = document.getElementById("paramValor").value.trim();

  if (!valor) return alert("Digite um valor!");

  const url = id ? `/api/parametro/${id}` : `/api/parametro`;
  const metodo = id ? "PUT" : "POST";

  try {
    const res = await fetch(url, {
      method: metodo,
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({tipo: tipo, valor: valor})
    });
    const d = await res.json();
    if (d.sucesso) {
      fecharModal("modalParamCrud");
      carregarParametrosListas();
    } else {
      alert("Erro ao salvar: " + d.erro);
    }
  } catch (e) {
    alert("Falha de conexão.");
  }
}

async function editarParamPrompt(id, valorAntigo) {
  const novo = prompt("Editar nome:", valorAntigo);
  if (novo && novo.trim() && novo.trim() !== valorAntigo) {
    await fetch(`/api/parametro/${id}`, {
      method: "PUT",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({valor: novo.trim()})
    });
    carregarParametrosListas();
  }
}

async function excluirParamPrompt(id, valor) {
  if (confirm(`Excluir parâmetro "${valor}"?`)) {
    await fetch(`/api/parametro/${id}`, {method: "DELETE"});
    carregarParametrosListas();
  }
}

// ---------------------------------------------------------------------------
// FECHAMENTO DIÁRIO & PASTAS
// ---------------------------------------------------------------------------
async function fecharExpediente() {
  if (!confirm("Deseja encerrar o expediente de trabalho?\n\nO sistema irá gerar a planilha Excel oficial consolidada e copiar o backup para o Google Drive.")) {
    return;
  }

  const btn = document.querySelector(".btn-footer-closing") || document.querySelector(".btn-drive-closing");
  const orig = btn ? btn.innerHTML : "";
  if (btn) {
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Gerando Excel e backup...';
    btn.disabled = true;
  }

  try {
    const res = await fetch("/api/fechar_expediente", {method: "POST"});
    const d = await res.json();
    if (d.sucesso) {
      alert(`Expediente encerrado com sucesso!\n\n• Planilha Atualizada: Almoxarifado_ARGUS_Consolidado.xlsx\n• Backup Gerado: ${d.arquivo_backup}\n${d.caminho_drive ? '• Copiado para o Google Drive: ' + d.caminho_drive : '• Cópia arquivada em backups_drive/'}`);
    } else {
      alert("Erro no encerramento: " + d.erro);
    }
  } catch (e) {
    alert("Falha ao comunicar com o servidor.");
  } finally {
    if (btn) {
      btn.innerHTML = orig;
      btn.disabled = false;
    }
  }
}

function abrirPasta(tipo) {
  fetch(`/api/abrir_pasta?tipo=${tipo}`);
}

async function carregarConfig() {
  try {
    const res = await fetch("/api/config");
    const d = await res.json();
    if (d && document.getElementById("cfgDrivePath")) {
      document.getElementById("cfgDrivePath").value = d.pasta_google_drive || "";
    }
  } catch (e) {
    console.error("Erro ao carregar config:", e);
  }
}

async function salvarConfig() {
  const pasta = document.getElementById("cfgDrivePath").value.trim();
  try {
    const res = await fetch("/api/config", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({pasta_google_drive: pasta})
    });
    const d = await res.json();
    if (d.sucesso) {
      fecharModal("modalConfig");
      alert("Configuração de pasta salva com sucesso!");
    } else {
      alert("Erro ao salvar configuração: " + d.erro);
    }
  } catch (e) {
    alert("Falha ao salvar configuração.");
  }
}

// ---------------------------------------------------------------------------
// SELETOR NATIVO DO WINDOWS EXPLORER PARA BACKUP NO GOOGLE DRIVE
// ---------------------------------------------------------------------------
async function selecionarPastaDriveWindows() {
  const btn = document.getElementById("btnBuscarDrive");
  const origHtml = btn ? btn.innerHTML : "";
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> <span>Aguardando Windows Explorer...</span>`;
  }

  try {
    const res = await fetch("/api/selecionar_pasta_drive");
    const d = await res.json();
    if (d.sucesso && d.pasta) {
      const input = document.getElementById("cfgDrivePath");
      if (input) input.value = d.pasta;
      alert(`Pasta do Google Drive selecionada:\n\n${d.pasta}\n\nA pasta já foi gravada nas configurações do sistema.`);
    } else if (d.cancelado) {
      // O usuário cancelou a seleção na janela do Windows
    } else {
      alert("Não foi possível obter o caminho da pasta.");
    }
  } catch (e) {
    console.error("Erro ao abrir Windows Explorer:", e);
    alert("Falha ao acionar o seletor de pastas do Windows.");
  } finally {
    if (btn) {
      btn.innerHTML = origHtml;
      btn.disabled = false;
    }
  }
}

// ---------------------------------------------------------------------------
// GESTÃO DE OPERADORES & AUTENTICAÇÃO CANÔNICA (PESSOAFISICA ARGUS)
// ---------------------------------------------------------------------------
async function verificarSessaoAuth() {
  try {
    const res = await fetch("/api/auth/status");
    const d = await res.json();

    if (d.operador_ativo) {
      operadorAtivo = d.operador_ativo;
      entrarNoSistema(operadorAtivo);
    } else {
      sairDoSistema();
      mostrarAbaLogin('login');
    }
  } catch (e) {
    console.error("Erro ao verificar sessão de autenticação:", e);
    sairDoSistema();
    mostrarAbaLogin('login');
  }
}


function entrarNoSistema(op) {
  const loginScreen = document.getElementById("loginScreen");
  const appContainer = document.getElementById("appContainer");
  if (loginScreen) loginScreen.style.display = "none";
  if (appContainer) appContainer.style.display = "block";
  atualizarBadgeOperador(op);
}

function sairDoSistema() {
  const loginScreen = document.getElementById("loginScreen");
  const appContainer = document.getElementById("appContainer");
  if (appContainer) appContainer.style.display = "none";
  if (loginScreen) loginScreen.style.display = "flex";
  atualizarBadgeOperador(null);
}

function atualizarBadgeOperador(op) {
  const lblNome = document.getElementById("txtOperadorNome");
  const lblPapel = document.getElementById("txtOperadorPapel");
  if (!lblNome || !lblPapel) return;

  if (op) {
    lblNome.innerText = op.nome_completo;
    lblPapel.innerText = `${op.tipo_vinculo || 'OPERADOR'} • ${op.cargo_funcao || 'Almoxarifado'}`;
  } else {
    lblNome.innerText = "Identificar Operador";
    lblPapel.innerText = "Nenhuma sessão ativa";
  }
}

function abrirModalAuth() {
  // Quando clica no badge do topo para alternar operador
  sairDoSistema();
  mostrarAbaLogin('login');
}

function mostrarAbaLogin(aba) {
  const secLogin = document.getElementById("secFormLogin");
  const secCad = document.getElementById("secFormCadastro");
  const tabLogin = document.getElementById("tabBtnLogin");
  const tabCad = document.getElementById("tabBtnCadastro");

  if (aba === 'cadastro') {
    if (secLogin) secLogin.style.display = "none";
    if (secCad) secCad.style.display = "block";
    if (tabLogin) tabLogin.classList.remove("active");
    if (tabCad) tabCad.classList.add("active");
    setTimeout(() => {
      const el = document.getElementById("screenCadNome");
      if (el) el.focus();
    }, 100);
  } else {
    if (secLogin) secLogin.style.display = "block";
    if (secCad) secCad.style.display = "none";
    if (tabLogin) tabLogin.classList.add("active");
    if (tabCad) tabCad.classList.remove("active");
    setTimeout(() => {
      const el = document.getElementById("screenLoginIdentificador");
      if (el) el.focus();
    }, 100);
  }
}

function alternarCamposVinculoScreen(tipo) {
  const divTerc = document.getElementById("screenDivEmpresaTerc");
  const divSiape = document.getElementById("screenDivSiape");
  const divOutro = document.getElementById("screenDivOutroVinculo");
  if (!divTerc || !divSiape) return;

  if (tipo === "SERVIDOR") {
    divTerc.style.display = "none";
    divSiape.style.display = "block";
    if (divOutro) divOutro.style.display = "none";
    const el = document.getElementById("screenCadSiape");
    if (el) el.focus();
  } else if (tipo === "TERCEIRIZADO") {
    divTerc.style.display = "block";
    divSiape.style.display = "none";
    if (divOutro) divOutro.style.display = "none";
    const el = document.getElementById("screenCadEmpresaTerc");
    if (el) el.focus();
  } else {
    divTerc.style.display = "none";
    divSiape.style.display = "none";
    if (divOutro) divOutro.style.display = "block";
  }
}

async function executarLoginScreen() {
  const login = document.getElementById("screenLoginIdentificador").value.trim();
  const senha = document.getElementById("screenLoginSenha").value;
  const btn = document.getElementById("btnScreenSubmitLogin");

  if (!login || !senha) {
    alert("Por favor, preencha o login/CPF e a senha de acesso.");
    return;
  }

  btn.disabled = true;
  btn.innerHTML = `<i class="fas fa-spinner fa-spin me-1"></i> Autenticando...`;

  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({login: login, senha: senha})
    });
    const d = await res.json();
    if (d.sucesso && d.operador) {
      operadorAtivo = d.operador;
      entrarNoSistema(operadorAtivo);
      document.getElementById("screenLoginSenha").value = "";
    } else {
      alert("Falha na autenticação: " + (d.erro || "Credenciais inválidas."));
    }
  } catch (e) {
    alert("Erro ao conectar com o servidor para autenticação.");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i class="fas fa-arrow-right-to-bracket text-white"></i> <span>Entrar no Sistema</span>`;
  }
}

async function executarCadastroScreen() {
  const nome = document.getElementById("screenCadNome").value.trim();
  const cpf = document.getElementById("screenCadCpf").value.trim();
  const email = document.getElementById("screenCadEmail").value.trim();
  const telefone = document.getElementById("screenCadTelefone").value.trim();
  const tipoVinculo = document.getElementById("screenCadTipoVinculo").value;
  const cargo = document.getElementById("screenCadCargo").value.trim();
  const empresaTerc = document.getElementById("screenCadEmpresaTerc") ? document.getElementById("screenCadEmpresaTerc").value.trim() : "";
  const siape = document.getElementById("screenCadSiape") ? document.getElementById("screenCadSiape").value.trim() : "";
  const senha = document.getElementById("screenCadSenha").value;
  const senhaConfirma = document.getElementById("screenCadSenhaConfirma").value;
  const btn = document.getElementById("btnScreenSubmitCadastro");

  if (senha !== senhaConfirma) {
    alert("As senhas digitadas não coincidem. Por favor, verifique.");
    document.getElementById("screenCadSenhaConfirma").focus();
    return;
  }

  if (senha.length < 4) {
    alert("A senha de acesso deve possuir pelo menos 4 caracteres.");
    document.getElementById("screenCadSenha").focus();
    return;
  }

  const cpfNumeros = cpf.replace(/\D/g, "");
  if (cpfNumeros.length !== 11) {
    alert("O CPF deve conter exatamente 11 dígitos numéricos.");
    document.getElementById("screenCadCpf").focus();
    return;
  }

  btn.disabled = true;
  btn.innerHTML = `<i class="fas fa-spinner fa-spin me-1"></i> Cadastrando Usuário...`;

  try {
    const payload = {
      nome_completo: nome,
      cpf: cpfNumeros,
      email: email,
      telefone: telefone,
      tipo_vinculo: tipoVinculo,
      cargo_funcao: cargo,
      empresa_contratada: empresaTerc,
      siape: siape,
      login: cpfNumeros,
      senha: senha
    };

    const res = await fetch("/api/auth/cadastro", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const d = await res.json();
    if (d.sucesso && d.operador) {
      operadorAtivo = d.operador;
      entrarNoSistema(operadorAtivo);
      alert(`Cadastro concluído com sucesso!\n\nBem-vindo(a), ${operadorAtivo.nome_completo}.\nVocê já está autenticado(a) e seus lançamentos serão devidamente registrados em sua autoria.`);
    } else {
      alert("Erro ao cadastrar operador: " + (d.erro || "Tente novamente."));
    }
  } catch (e) {
    alert("Erro ao conectar com o servidor para realizar o cadastro.");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i class="fas fa-user-check text-white"></i> <span>Cadastrar e Entrar no Sistema</span>`;
  }
}

async function fazerLogout() {
  if (!confirm("Deseja realmente encerrar a sessão do operador atual?")) return;
  try {
    await fetch("/api/auth/logout", {method: "POST"});
  } catch (e) {}
  operadorAtivo = null;
  sairDoSistema();
  mostrarAbaLogin('login');
}

// Máscaras Dinâmicas Canônicas: CPF e Telefone
function formatarMascaraCpf(valor) {
  let v = (valor || "").replace(/\D/g, "").substring(0, 11);
  if (v.length > 9) {
    return v.replace(/^(\d{3})(\d{3})(\d{3})(\d{1,2})$/, "$1.$2.$3-$4");
  } else if (v.length > 6) {
    return v.replace(/^(\d{3})(\d{3})(\d{1,3})$/, "$1.$2.$3");
  } else if (v.length > 3) {
    return v.replace(/^(\d{3})(\d{1,3})$/, "$1.$2");
  }
  return v;
}

function formatarMascaraTelefone(valor) {
  let v = (valor || "").replace(/\D/g, "").substring(0, 11);
  if (v.length > 10) {
    return v.replace(/^(\d{2})(\d{5})(\d{4})$/, "($1) $2-$3");
  } else if (v.length > 6) {
    return v.replace(/^(\d{2})(\d{4})(\d{0,4})$/, "($1) $2-$3");
  } else if (v.length > 2) {
    return v.replace(/^(\d{2})(\d{0,5})$/, "($1) $2");
  }
  return v;
}

document.addEventListener("input", (e) => {
  if (!e.target) return;
  const id = e.target.id;
  if (id === "screenCadCpf" || id === "cadCpf" || id === "solicCpf") {
    e.target.value = formatarMascaraCpf(e.target.value);
  } else if (id === "screenLoginIdentificador") {
    const val = e.target.value;
    const clean = val.replace(/\D/g, "");
    if (clean.length > 0 && /^[0-9.\-]+$/.test(val)) {
      e.target.value = formatarMascaraCpf(val);
    }
  } else if (id === "screenCadTelefone" || id === "cadTelefone") {
    e.target.value = formatarMascaraTelefone(e.target.value);
  }
});


// Carrega a configuração ao inicializar
carregarConfig();


// ===========================================================================
// ARGUS SORTER — Motor de Ordenação Client-Side (Todas as Tabelas)
// ===========================================================================
const ArgusSorter = (() => {
  // Estado de ordenação por tabela
  const estado = {};

  // Extrai o texto puro de uma célula (ignora HTML interno)
  function textoCell(td) {
    return (td.innerText || td.textContent || '').trim();
  }

  // Compara dois valores conforme o tipo declarado no th
  function comparar(a, b, tipo, desc) {
    let va = a, vb = b;
    if (tipo === 'num') {
      va = parseFloat(a.replace(',', '.')) || 0;
      vb = parseFloat(b.replace(',', '.')) || 0;
    } else {
      va = a.toLowerCase();
      vb = b.toLowerCase();
    }
    if (va < vb) return desc ? 1 : -1;
    if (va > vb) return desc ? -1 : 1;
    return 0;
  }

  // Ordena a tbody do theadId pela coluna clicada
  function ordenar(theadId, colIdx, tipo) {
    const thead = document.getElementById(theadId);
    if (!thead) return;
    const tbody = thead.parentElement.querySelector('tbody');
    if (!tbody) return;

    const key = theadId + '_' + colIdx;
    const isDesc = (estado[key] === 'asc');
    estado[key] = isDesc ? 'desc' : 'asc';

    // Atualiza ícones em todos os th do thead
    thead.querySelectorAll('.th-sort').forEach(th => {
      const icon = th.querySelector('.sort-icon');
      if (!icon) return;
      const thCol = parseInt(th.dataset.col, 10);
      if (thCol === colIdx) {
        icon.textContent = isDesc ? '↑' : '↓';
        th.classList.add('th-sort--active');
      } else {
        icon.textContent = '↕';
        th.classList.remove('th-sort--active');
      }
    });

    // Coleta e ordena as linhas
    const rows = Array.from(tbody.querySelectorAll('tr'));
    // Ignora linhas de estado (colspan — vazias/loading)
    const linhasValidas = rows.filter(tr => tr.querySelectorAll('td').length > 1);
    const linhasEstado = rows.filter(tr => tr.querySelectorAll('td').length <= 1);

    linhasValidas.sort((ra, rb) => {
      const cellA = ra.querySelectorAll('td')[colIdx];
      const cellB = rb.querySelectorAll('td')[colIdx];
      if (!cellA || !cellB) return 0;
      return comparar(textoCell(cellA), textoCell(cellB), tipo, isDesc);
    });

    // Remonta tbody com linhas de estado no topo (se existirem)
    linhasEstado.forEach(tr => tbody.appendChild(tr));
    linhasValidas.forEach(tr => tbody.appendChild(tr));
  }

  // Liga os listeners nos ths de um thead específico
  function inicializar(theadId) {
    const thead = document.getElementById(theadId);
    if (!thead) return;
    thead.querySelectorAll('.th-sort').forEach(th => {
      th.style.cursor = 'pointer';
      th.addEventListener('click', () => {
        const col = parseInt(th.dataset.col, 10);
        const tipo = th.dataset.type || 'str';
        ordenar(theadId, col, tipo);
      });
    });
  }

  // Inicializa todas as tabelas conhecidas
  function inicializarTodos() {
    inicializar('theadSaldos');
    inicializar('theadExtrato');
    inicializar('theadGerenciar');
  }

  return { inicializarTodos, inicializar, ordenar };
})();

// Inicia após o DOM estar pronto
document.addEventListener('DOMContentLoaded', () => {
  ArgusSorter.inicializarTodos();
});

// ===========================================================================
// GESTÃO E EMISSÃO DE TERMO DE CAUTELA EM DOCX (MODELO INSTITUCIONAL IFAM)
// ===========================================================================

let catalogoMateriaisCautela = [];
let contadorLinhasCautela = 0;

function abrirModalCautelaDocx() {
  abrirModal('modalCautelaDocx');
  mudarAbaCautela('abaCautelaGeral');

  const hoje = new Date();
  const hojeIso = hoje.toISOString().split('T')[0];

  const fimVigencia = new Date();
  fimVigencia.setDate(hoje.getDate() + 180); // 6 meses padrão
  const fimVigenciaIso = fimVigencia.toISOString().split('T')[0];

  const inEmissao = document.getElementById('cautelaDataEmissao');
  if (inEmissao && !inEmissao.value) inEmissao.value = hojeIso;

  const inVigIni = document.getElementById('cautelaVigenciaInicio');
  if (inVigIni && !inVigIni.value) inVigIni.value = hojeIso;

  const inVigFim = document.getElementById('cautelaVigenciaFim');
  if (inVigFim && !inVigFim.value) inVigFim.value = fimVigenciaIso;

  const inAno = document.getElementById('cautelaAno');
  if (inAno && !inAno.value) inAno.value = hoje.getFullYear();

  carregarProximoNumeroCautela();
  carregarParametrosCautela();
  carregarSolicitantesCautela();
  carregarCatalogoParaCautela();
  carregarHistoricoCautelas();

  // Garante ao menos uma linha de equipamento
  const tbody = document.getElementById('tbodyItensCautela');
  if (tbody && tbody.children.length === 0) {
    adicionarLinhaEquipamentoCautela();
  }
}

function mudarAbaCautela(abaId) {
  document.querySelectorAll('.btn-tab-cautela').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-pane-cautela').forEach(p => {
    p.classList.remove('active');
    p.style.display = 'none';
  });

  const pane = document.getElementById(abaId);
  if (pane) {
    pane.classList.add('active');
    pane.style.display = 'block';
  }

  const mapaBotoes = {
    'abaCautelaGeral': 'tabBtnGeral',
    'abaCautelaPartes': 'tabBtnPartes',
    'abaCautelaGestao': 'tabBtnGestao',
    'abaCautelaEquipamentos': 'tabBtnEquipamentos',
    'abaCautelaHistorico': 'tabBtnHistorico'
  };

  const btnId = mapaBotoes[abaId];
  if (btnId) {
    const btn = document.getElementById(btnId);
    if (btn) btn.classList.add('active');
  }
}

async function carregarProximoNumeroCautela() {
  const ano = document.getElementById('cautelaAno')?.value || new Date().getFullYear();
  try {
    const res = await fetch(`/api/termo_cautela/proximo_numero?ano=${ano}`);
    const d = await res.json();
    if (d && d.proximo_numero) {
      const input = document.getElementById('cautelaNumero');
      if (input) input.value = d.proximo_numero;
    }
  } catch (e) {
    console.error('Erro ao buscar próximo número:', e);
  }
}

async function carregarParametrosCautela() {
  try {
    const res = await fetch('/api/termo_cautela/parametros');
    const d = await res.json();
    if (d) {
      if (d.direcao_nome) document.getElementById('cautelaDirNome').value = d.direcao_nome;
      if (d.direcao_cargo) document.getElementById('cautelaDirCargo').value = d.direcao_cargo;
      if (d.direcao_ato_tipo) document.getElementById('cautelaDirAtoTipo').value = d.direcao_ato_tipo;
      if (d.direcao_ato_numero) document.getElementById('cautelaDirAtoNum').value = d.direcao_ato_numero;
      if (d.direcao_ato_origem) document.getElementById('cautelaDirAtoOrigem').value = d.direcao_ato_origem;
      if (d.direcao_ato_data) document.getElementById('cautelaDirAtoData').value = d.direcao_ato_data;

      if (d.coord_nome) document.getElementById('cautelaCoordNome').value = d.coord_nome;
      if (d.coord_locus) document.getElementById('cautelaCoordLocus').value = d.coord_locus;
      if (d.coord_siape) document.getElementById('cautelaCoordSiape').value = d.coord_siape;
      if (d.coord_ato) document.getElementById('cautelaCoordAto').value = d.coord_ato;
    }
  } catch (e) {
    console.error('Erro ao carregar parâmetros da cautela:', e);
  }
}

async function carregarSolicitantesCautela() {
  try {
    const res = await fetch('/api/solicitantes');
    const lista = await res.json();
    const select = document.getElementById('cautelaSelectSolicitante');
    if (!select) return;

    select.innerHTML = '<option value="">--- Selecione um solicitante cadastrado para preenchimento automático ---</option>';
    lista.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s.id;
      opt.textContent = s.rotulo || s.nome_completo;
      select.appendChild(opt);
    });
  } catch (e) {
    console.error('Erro ao carregar solicitantes:', e);
  }
}

async function aoMudarSolicitanteCautela(id) {
  if (!id) return;
  try {
    const res = await fetch(`/api/termo_cautela/solicitante/${id}`);
    const s = await res.json();
    if (!s) return;

    document.getElementById('cautelaSolicNome').value = s.nome_completo || '';
    document.getElementById('cautelaSolicCpf').value = s.cpf_formatado || s.cpf || '';
    document.getElementById('cautelaSolicVinculo').value = s.tipo_vinculo || 'Servidor do IFAM';
    document.getElementById('cautelaSolicSiape').value = s.siape || '';
    document.getElementById('cautelaSolicCargo').value = s.cargo || '';
    document.getElementById('cautelaSolicFuncao').value = s.funcao_projeto || '';
    document.getElementById('cautelaSolicOrigem').value = s.unidade_origem || '';

    const inProj = document.getElementById('cautelaProjeto');
    if (inProj && !inProj.value && s.projeto_padrao) {
      inProj.value = s.projeto_padrao;
    }

    aoMudarVinculoSolicitante(s.tipo_vinculo);
  } catch (e) {
    console.error('Erro ao buscar dados completos do solicitante:', e);
  }
}

function aoMudarVinculoSolicitante(valor) {
  const inSiape = document.getElementById('cautelaSolicSiape');
  if (!inSiape) return;
  if (valor === 'Servidor do IFAM') {
    inSiape.placeholder = 'Matrícula SIAPE do Servidor (obrigatório para servidor)';
    inSiape.style.background = '#FFFFFF';
  } else {
    inSiape.placeholder = 'Não aplicável (Colaborador Externo/Bolsista)';
    inSiape.style.background = '#F8FAFC';
  }
}

function formatarCpfInput(input) {
  let v = input.value.replace(/\D/g, '');
  if (v.length > 11) v = v.substring(0, 11);
  if (v.length > 9) {
    input.value = `${v.substring(0,3)}.${v.substring(3,6)}.${v.substring(6,9)}-${v.substring(9)}`;
  } else if (v.length > 6) {
    input.value = `${v.substring(0,3)}.${v.substring(3,6)}.${v.substring(6)}`;
  } else if (v.length > 3) {
    input.value = `${v.substring(0,3)}.${v.substring(3)}`;
  } else {
    input.value = v;
  }
}

async function carregarCatalogoParaCautela() {
  try {
    const res = await fetch('/api/catalogo?todos=1');
    catalogoMateriaisCautela = await res.json();

    // Popula datalist de projetos
    const resParams = await fetch('/api/parametros');
    const params = await resParams.json();
    const dlProj = document.getElementById('dlProjetosCautela');
    if (dlProj && params.projetos) {
      dlProj.innerHTML = '';
      params.projetos.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.valor;
        dlProj.appendChild(opt);
      });
    }
  } catch (e) {
    console.error('Erro ao carregar catálogo para cautela:', e);
  }
}

function adicionarLinhaEquipamentoCautela(itemPadrao = null) {
  contadorLinhasCautela++;
  const tbody = document.getElementById('tbodyItensCautela');
  if (!tbody) return;

  const tr = document.createElement('tr');
  tr.id = `rowCautelaItem_${contadorLinhasCautela}`;

  const descVal = itemPadrao?.descricao || '';
  const serieVal = itemPadrao?.numero_serie || '';
  const estadoVal = itemPadrao?.estado_conservacao || 'Bom estado de conservação e funcionamento';
  const acessVal = itemPadrao?.acessorios || '';

  // Opções para datalist de materiais
  const dlId = `dlMateriaisCautela_${contadorLinhasCautela}`;

  tr.innerHTML = `
    <td class="text-center fw-bold text-muted item-num-cautela" style="vertical-align: middle;">
      ${tbody.children.length + 1}
    </td>
    <td>
      <input type="text" class="form-input cautela-item-desc" list="${dlId}" placeholder="Nome ou SKU do equipamento / material" value="${descVal}" required style="font-size: 0.78rem;">
      <datalist id="${dlId}">
        ${catalogoMateriaisCautela.map(m => `<option value="${m.descricao} (SKU ${m.id})">${m.categoria} • ${m.local_ambiente || ''}</option>`).join('')}
      </datalist>
    </td>
    <td>
      <input type="text" class="form-input text-center cautela-item-serie" placeholder="Nº de Série / Patrimônio" value="${serieVal}" style="font-size: 0.78rem;">
    </td>
    <td>
      <select class="form-select cautela-item-estado" style="font-size: 0.78rem;">
        <option value="Excelente estado de conservação e funcionamento" ${estadoVal.includes('Excelente') ? 'selected' : ''}>Excelente estado</option>
        <option value="Bom estado de conservação e funcionamento" ${estadoVal.includes('Bom') ? 'selected' : ''}>Bom estado (regular)</option>
        <option value="Novo (lacrado / sem uso anterior)" ${estadoVal.includes('Novo') ? 'selected' : ''}>Novo / Sem uso</option>
        <option value="Usado - com marcas normais de uso" ${estadoVal.includes('Usado') ? 'selected' : ''}>Usado operacional</option>
        <option value="Avariado leve - operacional" ${estadoVal.includes('Avariado') ? 'selected' : ''}>Avariado leve</option>
      </select>
    </td>
    <td>
      <input type="text" class="form-input cautela-item-acess" placeholder="Cabos, fonte, estojo, maleta, etc." value="${acessVal}" style="font-size: 0.78rem;">
    </td>
    <td class="text-center" style="vertical-align: middle;">
      <button type="button" class="btn-aux" onclick="removerLinhaEquipamentoCautela(this)" title="Remover este item" style="padding: 4px 8px; color: #DC2626;">
        <i class="fas fa-trash-can"></i>
      </button>
    </td>
  `;

  tbody.appendChild(tr);
  atualizarNumeracaoItensCautela();
}

function removerLinhaEquipamentoCautela(btn) {
  const tr = btn.closest('tr');
  if (tr) {
    tr.remove();
    atualizarNumeracaoItensCautela();
  }
}

function atualizarNumeracaoItensCautela() {
  const tbody = document.getElementById('tbodyItensCautela');
  if (!tbody) return;
  const linhas = tbody.querySelectorAll('tr');
  linhas.forEach((tr, idx) => {
    const tdNum = tr.querySelector('.item-num-cautela');
    if (tdNum) tdNum.textContent = idx + 1;
  });
  const badge = document.getElementById('badgeQtdEquipamentos');
  if (badge) badge.textContent = linhas.length;
}

async function gerarTermoCautelaSubmit(event) {
  event.preventDefault();

  const tbody = document.getElementById('tbodyItensCautela');
  const linhas = tbody ? Array.from(tbody.querySelectorAll('tr')) : [];

  if (linhas.length === 0) {
    alert('Por favor, adicione ao menos um equipamento na Aba 4 (Equipamentos Cautelados).');
    mudarAbaCautela('abaCautelaEquipamentos');
    return;
  }

  const itens = [];
  for (const tr of linhas) {
    const desc = tr.querySelector('.cautela-item-desc')?.value?.trim();
    if (!desc) {
      alert('Preencha a descrição de todos os equipamentos antes de gerar o termo.');
      mudarAbaCautela('abaCautelaEquipamentos');
      return;
    }
    itens.push({
      descricao: desc,
      numero_serie: tr.querySelector('.cautela-item-serie')?.value?.trim() || 'S/N',
      estado_conservacao: tr.querySelector('.cautela-item-estado')?.value || 'Bom estado de conservação e funcionamento',
      acessorios: tr.querySelector('.cautela-item-acess')?.value?.trim() || '-'
    });
  }

  const btnGerar = document.getElementById('btnGerarCautelaDocx');
  const btnOriginalHtml = btnGerar ? btnGerar.innerHTML : '';
  if (btnGerar) {
    btnGerar.disabled = true;
    btnGerar.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Gerando documento Word...';
  }

  const solicSelect = document.getElementById('cautelaSelectSolicitante');
  const solicId = solicSelect ? solicSelect.value : null;

  const payload = {
    numero: document.getElementById('cautelaNumero')?.value?.trim() || '001',
    ano: parseInt(document.getElementById('cautelaAno')?.value) || new Date().getFullYear(),
    data_emissao: document.getElementById('cautelaDataEmissao')?.value || '',
    processo_sipac: document.getElementById('cautelaProcessoSipac')?.value?.trim() || '',
    vigencia_inicio: document.getElementById('cautelaVigenciaInicio')?.value || '',
    vigencia_fim: document.getElementById('cautelaVigenciaFim')?.value || '',
    projeto: document.getElementById('cautelaProjeto')?.value?.trim() || '',
    solicitante_id: solicId ? parseInt(solicId) : null,
    solicitante: {
      nome: document.getElementById('cautelaSolicNome')?.value?.trim() || '',
      cpf: document.getElementById('cautelaSolicCpf')?.value?.trim() || '',
      vinculo: document.getElementById('cautelaSolicVinculo')?.value || 'Servidor do IFAM',
      cargo: document.getElementById('cautelaSolicCargo')?.value?.trim() || '',
      funcao: document.getElementById('cautelaSolicFuncao')?.value?.trim() || '',
      siape: document.getElementById('cautelaSolicSiape')?.value?.trim() || '',
      origem: document.getElementById('cautelaSolicOrigem')?.value?.trim() || '',
      projeto: document.getElementById('cautelaProjeto')?.value?.trim() || ''
    },
    direcao: {
      nome: document.getElementById('cautelaDirNome')?.value?.trim() || '',
      cargo: document.getElementById('cautelaDirCargo')?.value?.trim() || 'Diretor Geral do Polo de Inovação Manaus',
      ato_tipo: document.getElementById('cautelaDirAtoTipo')?.value?.trim() || 'Portaria',
      ato_numero: document.getElementById('cautelaDirAtoNum')?.value?.trim() || '',
      ato_origem: document.getElementById('cautelaDirAtoOrigem')?.value?.trim() || 'GR/IFAM',
      ato_data: document.getElementById('cautelaDirAtoData')?.value?.trim() || ''
    },
    coordenacao: {
      nome: document.getElementById('cautelaCoordNome')?.value?.trim() || '',
      locus: document.getElementById('cautelaCoordLocus')?.value?.trim() || 'Laboratório / Setor Técnico',
      siape: document.getElementById('cautelaCoordSiape')?.value?.trim() || '',
      ato: document.getElementById('cautelaCoordAto')?.value?.trim() || ''
    },
    itens: itens,
    salvar_parametros_padrao: document.getElementById('chkSalvarPadraoGestao')?.checked || false,
    atualizar_cadastro_solicitante: document.getElementById('chkAtualizarCadastroSolicitante')?.checked || false
  };

  try {
    const res = await fetch('/api/termo_cautela/gerar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const d = await res.json();

    if (d.sucesso && d.download_url) {
      // 1. Dispara o download automático do arquivo .docx
      const link = document.createElement('a');
      link.href = d.download_url;
      link.download = d.nome_arquivo || `Termo_Cautela_${d.numero}_${d.ano}.docx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // 2. Notifica o usuário
      alert(
        `✅ Termo de Cautela Nº ${d.codigo_cautela} gerado com sucesso!\n\n` +
        `Arquivo: ${d.nome_arquivo}\n\n` +
        `O download do documento Word (.docx) foi iniciado automaticamente no seu computador.`
      );

      // 3. Atualiza o histórico
      carregarHistoricoCautelas();
      mudarAbaCautela('abaCautelaHistorico');
    } else {
      alert(`Erro ao gerar Termo de Cautela: ${d.erro || 'Falha na requisição'}`);
    }
  } catch (e) {
    console.error('Erro na requisição de geração do termo:', e);
    alert('Ocorreu um erro ao comunicar com o servidor do balcão.');
  } finally {
    if (btnGerar) {
      btnGerar.disabled = false;
      btnGerar.innerHTML = btnOriginalHtml;
    }
  }
}

async function carregarHistoricoCautelas() {
  const tbody = document.getElementById('tbodyHistoricoCautelas');
  if (!tbody) return;

  try {
    const res = await fetch('/api/termo_cautela/historico');
    const lista = await res.json();

    if (!lista || lista.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-3">Nenhum termo de cautela emitido até o momento.</td></tr>';
      return;
    }

    tbody.innerHTML = lista.map(c => `
      <tr>
        <td class="text-center fw-bold text-primary">${c.codigo_cautela}</td>
        <td class="text-center">${c.data_emissao}</td>
        <td>
          <div class="fw-bold">${c.solicitante_nome}</div>
          <small class="text-muted">${c.solicitante_cpf || ''}</small>
        </td>
        <td class="text-center text-muted" style="font-family: monospace; font-size: 0.72rem;">${c.processo_sipac || '-'}</td>
        <td class="text-center">${c.total_equipamentos} item(ns)</td>
        <td class="text-center">
          <a href="/api/termo_cautela/download?arquivo=${encodeURIComponent(c.arquivo_gerado)}" class="btn-footer-action" style="text-decoration: none; padding: 3px 8px; font-size: 0.72rem;" download>
            <i class="fas fa-download text-primary me-1"></i> .docx
          </a>
        </td>
      </tr>
    `).join('');
  } catch (e) {
    console.error('Erro ao buscar histórico:', e);
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger py-3">Falha ao carregar histórico.</td></tr>';
  }
}

// ===========================================================================
// SINCRONIZAÇÃO DE CICLO DE VIDA (HEARTBEAT DESKTOP)
// ===========================================================================
// Envia ping contínuo para manter o servidor ativo enquanto a janela estiver aberta
function enviarHeartbeatApp() {
  fetch('/api/heartbeat', { method: 'POST' }).catch(() => {});
}
enviarHeartbeatApp();
setInterval(enviarHeartbeatApp, 2000);

// Notifica encerramento imediato do processo desktop ao fechar a janela (X)
window.addEventListener('beforeunload', () => {
  if (navigator.sendBeacon) {
    navigator.sendBeacon('/api/encerrar_sessao');
  }
});






// =========================================================
// DIRETORES & SUBSTITUTOS
// =========================================================
function renderizarListaDiretores(diretores) {
  const tbody = document.getElementById("listaParamsDiretores");
  if (!tbody) return;
  tbody.innerHTML = "";
  
  if (diretores.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted p-3">Nenhum diretor cadastrado.</td></tr>`;
    return;
  }
  
  diretores.forEach(d => {
    let tr = document.createElement("tr");
    let btnHtml = "";
    if (d.is_titular === 1) {
        tr.style.backgroundColor = "rgba(var(--bs-primary-rgb), 0.05)";
        btnHtml = `<span class="badge bg-primary">Titular Fixo</span>`;
    } else {
        btnHtml = `
            <button class="btn-grid" onclick='abrirModalDiretor(${JSON.stringify(d)})' title="Editar Substituto"><i class="fas fa-edit text-primary"></i></button>
            <button class="btn-grid" onclick="excluirDiretor(${d.id})" title="Excluir Substituto"><i class="fas fa-trash text-danger"></i></button>
        `;
    }
    
    let icone = d.is_titular === 1 ? '<i class="fas fa-check-circle text-primary ms-1" title="Titular Oficial"></i>' : '';
    
    tr.innerHTML = `
      <td class="fw-bold text-dark">${d.cargo}</td>
      <td>${d.nome} ${icone}</td>
      <td class="small text-muted">${d.portaria}</td>
      <td class="text-center">${btnHtml}</td>
    `;
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

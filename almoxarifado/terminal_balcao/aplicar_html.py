import re

with open('static/index.html', 'r', encoding='utf-8') as f:
    conteudo = f.read()

nova_div = '''              </div> <!-- Fim da row das 3 colunas -->

              <div class="row mt-4">
                <!-- Diretores e Substitutos -->
                <div class="col-lg-12 mb-3">
                  <article class="cs-card h-100">
                    <div class="cs-card__header">
                      <h3 class="cs-card__title"><i class="fas fa-file-signature text-warning me-1"></i> Autoridades / Diretores</h3>
                      <button class="btn-aux" onclick="abrirModalDiretor()">➕ Adicionar Substituto</button>
                    </div>
                    <p class="text-muted small mb-2" style="font-size:0.72rem;">Titulares e Substitutos designados para assinar os Termos de Cautela e Documentos do Polo:</p>
                    
                    <div class="argus-table-card">
                      <div class="argus-table-responsive" style="max-height: 250px; overflow-y: auto;">
                        <table class="argus-table mb-0">
                          <thead style="position: sticky; top: 0; z-index: 1;">
                            <tr>
                              <th style="width: 25%;">Cargo / Função</th>
                              <th style="width: 35%;">Nome do Servidor</th>
                              <th style="width: 30%;">Portaria de Designação</th>
                              <th class="text-center" style="width: 10%;">Ações</th>
                            </tr>
                          </thead>
                          <tbody id="listaParamsDiretores">
                            <!-- Injetado via JS -->
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </article>
                </div>
              </div>
'''

conteudo = conteudo.replace('                    <div id="listaParamsSolicitantes"\n                      style="max-height:300px; overflow-y:auto; display:flex; flex-direction:column; gap:4px;"></div>\n                  </article>\n                </div>\n              </div>', 
'''                    <div id="listaParamsSolicitantes"
                      style="max-height:300px; overflow-y:auto; display:flex; flex-direction:column; gap:4px;"></div>
                  </article>
                </div>''' + nova_div)

# Preciso adicionar o MODAL de Adicionar Diretor
modal_diretor = '''
  <!-- MODAL DE DIRETOR -->
  <div id="modalDiretor" class="modal-overlay">
    <div class="modal-content" style="max-width: 500px;">
      <div class="modal-header">
        <h3 id="tituloModalDiretor"><i class="fas fa-file-signature text-warning me-1"></i> Novo Diretor / Substituto</h3>
        <button class="modal-close" onclick="fecharModal('modalDiretor')">✕</button>
      </div>
      <div class="modal-body">
        <form id="formDiretor" onsubmit="salvarDiretor(event)">
          <input type="hidden" id="dirId">
          <div class="form-group mb-3">
            <label class="form-label">Cargo / Função *</label>
            <input type="text" id="dirCargo" class="form-input" placeholder="Ex: Diretor-Geral Substituto" required>
          </div>
          <div class="form-group mb-3">
            <label class="form-label">Nome Completo *</label>
            <input type="text" id="dirNome" class="form-input" placeholder="Ex: Fulano de Tal" required>
          </div>
          <div class="form-group mb-3">
            <label class="form-label">Portaria de Designação *</label>
            <input type="text" id="dirPortaria" class="form-input" placeholder="Ex: PORTARIA Nº 001, DE..." required>
          </div>
          <div class="d-flex justify-content-end mt-4">
            <button type="button" class="btn-aux me-2" onclick="fecharModal('modalDiretor')">Cancelar</button>
            <button type="submit" class="btn-argus-primary">Salvar Substituto</button>
          </div>
        </form>
      </div>
    </div>
  </div>
'''

conteudo = conteudo.replace('  <!-- MODAL: REGISTRAR NOVA ENTRADA -->', modal_diretor + '\n  <!-- MODAL: REGISTRAR NOVA ENTRADA -->')

with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(conteudo)

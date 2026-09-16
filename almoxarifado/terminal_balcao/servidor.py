# -*- coding: utf-8 -*-
"""
Servidor HTTP e API REST do Terminal de Balcao do Almoxarifado.
Implementa o fluxo de 4 Etapas:
1 - Entradas (Recebimento)
2 - Saídas (Consumo e Empréstimo de Ferramentas)
3 - Saldos / Relatórios
4 - Gerenciar (CRUD Completo de Materiais e Parâmetros)
"""
import os
import sys
import json
import urllib.parse
import tempfile
import mimetypes
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess
import time
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from banco import (
    get_indicadores, get_parametros, get_catalogo, obter_material,
    criar_material, editar_material, excluir_material,
    registrar_entrada, get_historico_entradas,
    registrar_saida_consumo, registrar_retorno_sobra, registrar_emprestimo_ferramenta,
    get_ferramentas_em_uso, devolver_ferramenta,
    get_fracionados_abertos, obter_fracionado,
    get_extrato, adicionar_parametro, editar_parametro, excluir_parametro,
    get_solicitantes, cadastrar_solicitante, editar_solicitante, excluir_solicitante,
    get_solicitante_por_id, atualizar_dados_completos_solicitante,
    get_cautela_parametros, salvar_cautela_parametros,
    get_proximo_numero_cautela, salvar_registro_cautela, listar_cautelas,
    cadastrar_operador, autenticar_operador, ha_operadores, listar_operadores,
    init_db, DB_PATH
)
from gerador_pdf import (
    gerar_recibo_saida, gerar_termo_cautela,
    gerar_etiqueta_lata_pdf, gerar_etiqueta_prateleira_pdf, PDF_DIR
)
from gerador_cautela import (
    gerar_termo_cautela_docx, DIR_SAIDA_CAUTELAS
)
from exportador_excel import exportar_planilha_completa, DIR_EXCEL, DIR_DRIVE

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
def carregar_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"porta": 5500, "pasta_google_drive": "", "operador_ativo": None}

CONFIG = carregar_config()
PORT = CONFIG.get("porta", 5500)

ULTIMO_HEARTBEAT = time.time()
HEARTBEAT_RECEBIDO = False


def abrir_dialogo_pasta_windows():
    """Abre a janela nativa do Windows Explorer (IFileOpenDialog - Vista+) para seleção de pasta.

    Usa o seletor moderno via COM (IFileOpenDialog) em vez do FolderBrowserDialog legado,
    garantindo que a janela sempre apareça visível em primeiro plano.
    """
    # Script PowerShell que invoca o IFileOpenDialog moderno via COM.
    # Roda em um processo COM Single-Threaded Apartment (STA), obrigatório para dialogs Win32.
    ps_cmd = (
        "Add-Type -AssemblyName System.Windows.Forms | Out-Null; "
        "$dialog = New-Object System.Windows.Forms.OpenFileDialog; "
        "$dialog.Title = 'Selecione a pasta do Google Drive para backup'; "
        "$dialog.Filter = 'Pasta|*.none'; "
        "$dialog.FileName = 'Selecione esta pasta e clique em Abrir'; "
        "$dialog.CheckFileExists = $false; "
        "$dialog.CheckPathExists = $true; "
        "$dialog.ValidateNames = $false; "
        # Mantém janela visível no topo usando -sta (Single-Threaded Apartment)
        "if ($dialog.ShowDialog() -eq 'OK') { "
        "  $pasta = [System.IO.Path]::GetDirectoryName($dialog.FileName); "
        "  if (-not $pasta) { $pasta = $dialog.FileName }; "
        "  Write-Output $pasta "
        "}"
    )
    cmd = [
        "powershell",
        "-NoProfile",
        "-STA",          # ← STA obrigatório para dialogs COM
        "-Command",
        ps_cmd
    ]
    try:
        # NÃO usar CREATE_NO_WINDOW — dialogs COM precisam de contexto de janela visível
        res = subprocess.check_output(cmd, timeout=120)
        caminho = res.decode("utf-8", errors="ignore").strip()
        if caminho and os.path.isdir(caminho):
            return caminho
        return None
    except Exception as e:
        print(f"Aviso ao abrir diálogo de pasta Windows: {e}")
        return None


class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True

class AlmoxarifadoHandler(BaseHTTPRequestHandler):

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def responder_json(self, status_code, dados):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def responder_pdf(self, pdf_path, nome_arquivo):
        if os.path.exists(pdf_path):
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Disposition", f"inline; filename={nome_arquivo}")
            with open(pdf_path, "rb") as f:
                conteudo = f.read()
            self.send_header("Content-Length", str(len(conteudo)))
            self.end_headers()
            self.wfile.write(conteudo)
        else:
            self.send_error(404, "PDF nao encontrado")

    def responder_docx(self, docx_path, nome_arquivo):
        if os.path.exists(docx_path):
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            self.send_header("Content-Disposition", f'attachment; filename="{nome_arquivo}"')
            with open(docx_path, "rb") as f:
                conteudo = f.read()
            self.send_header("Content-Length", str(len(conteudo)))
            self.end_headers()
            self.wfile.write(conteudo)
        else:
            self.send_error(404, "Arquivo DOCX nao encontrado")


    def do_GET(self):
        global ULTIMO_HEARTBEAT, HEARTBEAT_RECEBIDO
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Página Principal
        if path in ["/", "/index.html"]:
            index_path = os.path.join(BASE_DIR, "static", "index.html")
            if os.path.exists(index_path):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                with open(index_path, "rb") as f:
                    conteudo = f.read()
                self.send_header("Content-Length", str(len(conteudo)))
                self.end_headers()
                self.wfile.write(conteudo)
                return
            self.send_error(404, "index.html nao encontrado")
            return

        if path == "/favicon.ico":
            fav_path = os.path.join(BASE_DIR, "static", "img", "icone_almoxarifado.ico")
            if os.path.exists(fav_path):
                self.send_response(200)
                self.send_header("Content-Type", "image/x-icon")
                with open(fav_path, "rb") as f:
                    conteudo = f.read()
                self.send_header("Content-Length", str(len(conteudo)))
                self.end_headers()
                self.wfile.write(conteudo)
                return
            self.send_response(204)
            self.end_headers()
            return

        # Arquivos Estáticos
        if path.startswith("/static/"):
            rel_path = path[len("/static/"):].replace("/", os.sep)
            file_path = os.path.join(BASE_DIR, "static", rel_path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                mime = "text/plain"
                if file_path.endswith(".css"): mime = "text/css"
                elif file_path.endswith(".js"): mime = "application/javascript"
                elif file_path.endswith(".html"): mime = "text/html"
                self.send_response(200)
                self.send_header("Content-Type", mime)
                with open(file_path, "rb") as f:
                    conteudo = f.read()
                self.send_header("Content-Length", str(len(conteudo)))
                self.end_headers()
                self.wfile.write(conteudo)
                return
            self.send_error(404, "Arquivo estatico nao encontrado")
            return

        # APIs
        if path == "/api/heartbeat":
            ULTIMO_HEARTBEAT = time.time()
            HEARTBEAT_RECEBIDO = True
            self.responder_json(200, {"ok": True, "ts": ULTIMO_HEARTBEAT})
            return

        if path == "/api/encerrar_sessao":
            self.responder_json(200, {"ok": True, "msg": "Encerrando"})
            def _desligar_get():
                time.sleep(0.3)
                lock_f = os.path.join(tempfile.gettempdir(), "argus_almoxarifado.lock")
                if os.path.exists(lock_f):
                    try:
                        os.remove(lock_f)
                    except:
                        pass
                os._exit(0)
            threading.Thread(target=_desligar_get, daemon=True).start()
            return

        if path == "/api/status":
            self.responder_json(200, get_indicadores())
            return

        if path == "/api/parametros":
            self.responder_json(200, get_parametros())
            return

        if path == "/api/solicitantes":
            self.responder_json(200, get_solicitantes(apenas_ativos=True))
            return

        if path == "/api/catalogo":
            filtro = query.get("filtro", [""])[0]
            apenas_ativos = query.get("todos", ["0"])[0] != "1"
            self.responder_json(200, get_catalogo(filtro=filtro, apenas_ativos=apenas_ativos))
            return

        if path == "/api/config":
            self.responder_json(200, CONFIG)
            return

        if path.startswith("/api/material/"):
            id_mat = path[len("/api/material/"):]
            mat = obter_material(id_mat)
            if mat:
                self.responder_json(200, mat)
            else:
                self.responder_json(404, {"erro": "Material nao encontrado"})
            return

        if path == "/api/entradas":
            self.responder_json(200, get_historico_entradas())
            return

        if path == "/api/ferramentas_em_uso":
            self.responder_json(200, get_ferramentas_em_uso())
            return

        if path == "/api/fracionados_abertos":
            self.responder_json(200, get_fracionados_abertos())
            return

        if path == "/api/extrato":
            mat_id = query.get("material_id", [None])[0]
            self.responder_json(200, get_extrato(material_id=mat_id))
            return

        # Rotas GET - Termo de Cautela de Equipamento (.docx)
        if path == "/api/termo_cautela/parametros":
            self.responder_json(200, get_cautela_parametros())
            return

        if path == "/api/termo_cautela/proximo_numero":
            ano = query.get("ano", [None])[0]
            self.responder_json(200, {"proximo_numero": get_proximo_numero_cautela(ano)})
            return

        if path.startswith("/api/termo_cautela/solicitante/"):
            try:
                s_id = int(path[len("/api/termo_cautela/solicitante/"):])
                solic = get_solicitante_por_id(s_id)
                if solic:
                    self.responder_json(200, solic)
                else:
                    self.responder_json(404, {"erro": "Solicitante não encontrado"})
            except Exception as e:
                self.responder_json(400, {"erro": str(e)})
            return

        if path == "/api/termo_cautela/historico":
            self.responder_json(200, listar_cautelas())
            return

        if path == "/api/termo_cautela/download":
            arq_nome = query.get("arquivo", [None])[0]
            if arq_nome:
                nome_limpo = os.path.basename(arq_nome)
                docx_path = os.path.join(DIR_SAIDA_CAUTELAS, nome_limpo)
                self.responder_docx(docx_path, nome_limpo)
            else:
                self.responder_json(400, {"erro": "Parâmetro arquivo é obrigatório"})
            return

        if path.startswith("/api/comprovante/"):

            nome_arquivo = path[len("/api/comprovante/"):]
            pdf_path = os.path.join(PDF_DIR, nome_arquivo)
            self.responder_pdf(pdf_path, nome_arquivo)
            return

        if path.startswith("/api/etiqueta_lata/"):
            id_frac = path[len("/api/etiqueta_lata/"):]
            frac = obter_fracionado(id_frac)
            if not frac:
                mat = obter_material(id_frac)
                if mat:
                    from datetime import datetime, timedelta
                    pao_dias = mat.get('validade_pao_dias') or 60
                    venc = (datetime.now() + timedelta(days=pao_dias)).strftime("%d/%m/%Y")
                    frac = {
                        "id": f"LATA-{mat['id']}",
                        "material_id": mat['id'],
                        "codigo_catmat": mat.get('codigo_catmat', '-'),
                        "descricao": mat['descricao'],
                        "volume_nominal": mat.get('embalagem_compra', '18L'),
                        "validade_pao_dias": pao_dias,
                        "data_abertura": datetime.now().strftime("%d/%m/%Y"),
                        "data_vencimento_pao": venc,
                        "aberto_por": "ALMOXARIFADO CENTRAL"
                    }
            if frac:
                caminho_pdf, nome_arq = gerar_etiqueta_lata_pdf(frac)
                self.responder_pdf(caminho_pdf, nome_arq)
            else:
                self.responder_json(404, {"erro": "Lata ou material nao encontrado"})
            return

        if path.startswith("/api/etiqueta_prateleira/"):
            id_mat = path[len("/api/etiqueta_prateleira/"):]
            mat = obter_material(id_mat)
            if mat:
                caminho_pdf, nome_arq = gerar_etiqueta_prateleira_pdf(mat)
                self.responder_pdf(caminho_pdf, nome_arq)
            else:
                self.responder_json(404, {"erro": "Material nao encontrado"})
            return

        if path == "/api/abrir_pasta":
            tipo = query.get("tipo", ["comprovantes"])[0]
            alvo = PDF_DIR if tipo == "comprovantes" else DIR_EXCEL
            if os.name == "nt":
                subprocess.Popen(f'explorer.exe "{alvo}"', shell=True)
            self.responder_json(200, {"sucesso": True})
            return

        if path == "/api/auth/status":
            self.responder_json(200, {
                "ha_operadores": ha_operadores(),
                "operador_ativo": CONFIG.get("operador_ativo")
            })
            return

        if path == "/api/auth/operadores":
            self.responder_json(200, listar_operadores())
            return

        if path == "/api/selecionar_pasta_drive":
            pasta = abrir_dialogo_pasta_windows()
            if pasta:
                CONFIG["pasta_google_drive"] = pasta
                try:
                    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                        json.dump(CONFIG, f, ensure_ascii=False, indent=2)
                except:
                    pass
                self.responder_json(200, {"sucesso": True, "pasta": pasta})
            else:
                self.responder_json(200, {"sucesso": False, "cancelado": True})
            return

        self.send_error(404, "Rota GET nao encontrada")


    def ler_payload(self):
        content_len = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_len) if content_len > 0 else b"{}"
        try:
            return json.loads(post_data.decode("utf-8")) if post_data else {}
        except:
            return {}

    def do_POST(self):
        global ULTIMO_HEARTBEAT, HEARTBEAT_RECEBIDO
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        dados = self.ler_payload()

        # Ciclo de Vida e Sessão
        if path == "/api/heartbeat":
            ULTIMO_HEARTBEAT = time.time()
            HEARTBEAT_RECEBIDO = True
            self.responder_json(200, {"ok": True, "ts": ULTIMO_HEARTBEAT})
            return

        if path == "/api/encerrar_sessao":
            self.responder_json(200, {"ok": True, "msg": "Encerrando processo"})
            def _desligar_post():
                time.sleep(0.3)
                lock_f = os.path.join(tempfile.gettempdir(), "argus_almoxarifado.lock")
                if os.path.exists(lock_f):
                    try:
                        os.remove(lock_f)
                    except:
                        pass
                os._exit(0)
            threading.Thread(target=_desligar_post, daemon=True).start()
            return

        # Autenticação e Gestão de Operador
        if path == "/api/auth/cadastro":
            try:
                novo_op = cadastrar_operador(dados)
                CONFIG["operador_ativo"] = novo_op
                try:
                    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                        json.dump(CONFIG, f, ensure_ascii=False, indent=2)
                except:
                    pass
                self.responder_json(200, {"sucesso": True, "operador": novo_op})
            except Exception as e:
                self.responder_json(400, {"sucesso": False, "erro": str(e)})
            return

        if path == "/api/auth/login":
            try:
                login = dados.get("login") or dados.get("cpf")
                senha = dados.get("senha")
                op = autenticar_operador(login, senha)
                CONFIG["operador_ativo"] = op
                try:
                    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                        json.dump(CONFIG, f, ensure_ascii=False, indent=2)
                except:
                    pass
                self.responder_json(200, {"sucesso": True, "operador": op})
            except Exception as e:
                self.responder_json(400, {"sucesso": False, "erro": str(e)})
            return

        if path == "/api/auth/logout":
            CONFIG["operador_ativo"] = None
            try:
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(CONFIG, f, ensure_ascii=False, indent=2)
            except:
                pass
            self.responder_json(200, {"sucesso": True})
            return

        # ETAPA 1: Entrada

        if path == "/api/entrada":

            try:
                registrar_entrada(dados)
                self.responder_json(200, {"sucesso": True})
            except Exception as e:
                self.responder_json(400, {"sucesso": False, "erro": str(e)})
            return

        # ETAPA 2: Saída de Consumo
        if path == "/api/saida_consumo" or path == "/api/saida":
            try:
                res_banco = registrar_saida_consumo(dados)
                caminho_pdf, nome_pdf = gerar_recibo_saida(res_banco)
                res_banco["sucesso"] = True
                res_banco["pdf_nome"] = nome_pdf
                self.responder_json(200, res_banco)
            except Exception as e:
                self.responder_json(400, {"sucesso": False, "erro": str(e)})
            return

        # ETAPA 2: Empréstimo de Ferramenta
        if path == "/api/emprestimo_ferramenta" or path == "/api/cautela":
            try:
                res_banco = registrar_emprestimo_ferramenta(dados)
                caminho_pdf, nome_pdf = gerar_termo_cautela(res_banco)
                res_banco["sucesso"] = True
                res_banco["pdf_nome"] = nome_pdf
                self.responder_json(200, res_banco)
            except Exception as e:
                self.responder_json(400, {"sucesso": False, "erro": str(e)})
            return

        # Rotas POST - Termo de Cautela de Equipamento (.docx)
        if path == "/api/termo_cautela/parametros":
            try:
                salvar_cautela_parametros(dados)
                self.responder_json(200, {"sucesso": True})
            except Exception as e:
                self.responder_json(400, {"sucesso": False, "erro": str(e)})
            return

        if path == "/api/termo_cautela/gerar":
            try:
                # 1. Se solicitado, atualiza o cadastro do solicitante na base
                solic_id = dados.get("solicitante_id")
                atualizar_cad = dados.get("atualizar_cadastro_solicitante", True)
                if solic_id and atualizar_cad:
                    dados_solic = {
                        "nome_completo": dados.get("solicitante_nome") or (dados.get("solicitante") or {}).get("nome"),
                        "cpf": dados.get("solicitante_cpf") or (dados.get("solicitante") or {}).get("cpf"),
                        "tipo_vinculo": dados.get("solicitante_vinculo") or (dados.get("solicitante") or {}).get("vinculo"),
                        "cargo": dados.get("solicitante_cargo") or (dados.get("solicitante") or {}).get("cargo"),
                        "funcao_projeto": dados.get("solicitante_funcao") or (dados.get("solicitante") or {}).get("funcao"),
                        "siape": dados.get("solicitante_siape") or (dados.get("solicitante") or {}).get("siape"),
                        "unidade_origem": dados.get("solicitante_origem") or (dados.get("solicitante") or {}).get("origem"),
                        "projeto_padrao": dados.get("projeto") or (dados.get("solicitante") or {}).get("projeto")
                    }
                    try:
                        atualizar_dados_completos_solicitante(int(solic_id), dados_solic)
                    except Exception as e_sol:
                        print(f"Aviso ao atualizar solicitante: {e_sol}")

                # 2. Se solicitado, salva os parâmetros de Direção/Coordenação como padrão
                if dados.get("salvar_parametros_padrao"):
                    salvar_cautela_parametros({
                        "direcao_nome": (dados.get("direcao") or {}).get("nome", ""),
                        "direcao_cargo": (dados.get("direcao") or {}).get("cargo", ""),
                        "direcao_ato_tipo": (dados.get("direcao") or {}).get("ato_tipo", ""),
                        "direcao_ato_numero": (dados.get("direcao") or {}).get("ato_numero", ""),
                        "direcao_ato_origem": (dados.get("direcao") or {}).get("ato_origem", ""),
                        "direcao_ato_data": (dados.get("direcao") or {}).get("ato_data", ""),
                        "coord_nome": (dados.get("coordenacao") or {}).get("nome", ""),
                        "coord_locus": (dados.get("coordenacao") or {}).get("locus", ""),
                        "coord_siape": (dados.get("coordenacao") or {}).get("siape", ""),
                        "coord_ato": (dados.get("coordenacao") or {}).get("ato", "")
                    })

                # 3. Gera o arquivo .docx formatado
                resultado_docx = gerar_termo_cautela_docx(dados)

                # 4. Registra no banco de dados
                cautela_payload = {
                    "numero": resultado_docx["numero"],
                    "ano": resultado_docx["ano"],
                    "data_emissao": dados.get("data_emissao"),
                    "processo_sipac": dados.get("processo_sipac", ""),
                    "solicitante_id": solic_id,
                    "solicitante_nome": (dados.get("solicitante") or {}).get("nome") or dados.get("solicitante_nome", ""),
                    "solicitante_cpf": (dados.get("solicitante") or {}).get("cpf") or dados.get("solicitante_cpf", ""),
                    "solicitante_siape": (dados.get("solicitante") or {}).get("siape") or dados.get("solicitante_siape", ""),
                    "solicitante_cargo": (dados.get("solicitante") or {}).get("cargo") or dados.get("solicitante_cargo", ""),
                    "solicitante_vinculo": (dados.get("solicitante") or {}).get("vinculo") or dados.get("solicitante_vinculo", "Servidor do IFAM"),
                    "solicitante_origem": (dados.get("solicitante") or {}).get("origem") or dados.get("solicitante_origem", ""),
                    "solicitante_funcao": (dados.get("solicitante") or {}).get("funcao") or dados.get("solicitante_funcao", ""),
                    "projeto": dados.get("projeto", ""),
                    "vigencia_inicio": dados.get("vigencia_inicio", ""),
                    "vigencia_fim": dados.get("vigencia_fim", ""),
                    "direcao": dados.get("direcao", {}),
                    "coordenacao": dados.get("coordenacao", {}),
                    "itens": dados.get("itens", []),
                    "arquivo_gerado": resultado_docx["nome_arquivo"],
                    "operador_nome": (CONFIG.get("operador_ativo") or {}).get("nome", "")
                }
                cautela_id = salvar_registro_cautela(cautela_payload)

                self.responder_json(200, {
                    "sucesso": True,
                    "id": cautela_id,
                    "numero": resultado_docx["numero"],
                    "ano": resultado_docx["ano"],
                    "codigo_cautela": resultado_docx["codigo_cautela"],
                    "nome_arquivo": resultado_docx["nome_arquivo"],
                    "caminho_arquivo": resultado_docx["caminho_arquivo"],
                    "download_url": f"/api/termo_cautela/download?arquivo={resultado_docx['nome_arquivo']}"
                })
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.responder_json(400, {"sucesso": False, "erro": str(e)})
            return


        # ETAPA 2: Devolução de Ferramenta
        if path == "/api/devolver_ferramenta" or path == "/api/devolucao":
            id_emp = dados.get("id_emprestimo") or dados.get("id_cautela")
            sem_avarias = dados.get("sem_avarias", True)
            obs = dados.get("obs", "")
            ok = devolver_ferramenta(id_emp, sem_avarias, obs)
            self.responder_json(200, {"sucesso": ok})
            return

        # ETAPA 2: Retorno de Sobra Fracionada (Latas de Tinta / Cabos)
        if path == "/api/retorno_sobra":
            try:
                res = registrar_retorno_sobra(dados)
                self.responder_json(200, res)
            except Exception as e:
                self.responder_json(400, {"sucesso": False, "erro": str(e)})
            return

        # ETAPA 4: Cadastrar Novo Material (CRUD Create)
        if path == "/api/material":
            try:
                novo_id = criar_material(dados)
                self.responder_json(200, {"sucesso": True, "id": novo_id})
            except Exception as e:
                self.responder_json(400, {"sucesso": False, "erro": str(e)})
            return

        # ETAPA 4: Cadastrar Solicitante (Nome + CPF)
        if path == "/api/solicitante":
            try:
                nome = dados.get("nome") or dados.get("nome_completo")
                cpf = dados.get("cpf")
                novo_id = cadastrar_solicitante(nome, cpf)
                self.responder_json(200, {"sucesso": True, "id": novo_id})
            except Exception as e:
                self.responder_json(400, {"sucesso": False, "erro": str(e)})
            return

        # ETAPA 4: Cadastrar Parâmetro

        # API DIRETORES
        if path == "/api/diretores":
            try:
                acao = dados.get("acao")
                if acao == "CRIAR":
                    salvar_diretor(dados["cargo"], dados["nome"], dados["portaria"])
                elif acao == "EDITAR":
                    editar_diretor(dados["id"], dados["cargo"], dados["nome"], dados["portaria"])
                elif acao == "EXCLUIR":
                    excluir_diretor(dados["id"])
                self.responder_json(200, {"sucesso": True})
            except Exception as e:
                self.responder_json(400, {"sucesso": False, "erro": str(e)})
            return
            
        if path == "/api/parametro":
            try:
                novo_id = adicionar_parametro(dados['tipo'], dados['valor'])
                self.responder_json(200, {"sucesso": True, "id": novo_id})
            except Exception as e:
                self.responder_json(400, {"sucesso": False, "erro": str(e)})
            return

        # Fechamento do Expediente
        if path == "/api/fechar_expediente":
            try:
                caminho_drive = CONFIG.get("pasta_google_drive")
                res_exp = exportar_planilha_completa(caminho_custom_drive=caminho_drive)
                self.responder_json(200, {
                    "sucesso": True,
                    "arquivo_consolidado": os.path.basename(res_exp["arquivo_consolidado"]),
                    "arquivo_backup": os.path.basename(res_exp["arquivo_backup"]),
                    "caminho_drive": res_exp["arquivo_drive_custom"]
                })
            except Exception as e:
                self.responder_json(500, {"sucesso": False, "erro": str(e)})
        # Configuração da pasta do Drive
        if path == "/api/config":
            try:
                CONFIG["pasta_google_drive"] = dados.get("pasta_google_drive", "").strip()
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(CONFIG, f, ensure_ascii=False, indent=2)
                self.responder_json(200, {"sucesso": True})
            except Exception as e:
                self.responder_json(400, {"sucesso": False, "erro": str(e)})
            return

        self.send_error(404, "Rota POST nao encontrada")

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        dados = self.ler_payload()

        # ETAPA 4: Editar Material (CRUD Update)
        if path.startswith("/api/material/"):
            id_mat = path[len("/api/material/"):]
            try:
                editar_material(id_mat, dados)
                self.responder_json(200, {"sucesso": True})
            except Exception as e:
                self.responder_json(400, {"sucesso": False, "erro": str(e)})
            return

        # ETAPA 4: Editar Solicitante
        if path.startswith("/api/solicitante/"):
            try:
                id_solic = int(path[len("/api/solicitante/"):])
                nome = dados.get("nome") or dados.get("nome_completo")
                cpf = dados.get("cpf")
                editar_solicitante(id_solic, nome, cpf)
                self.responder_json(200, {"sucesso": True})
            except Exception as e:
                self.responder_json(400, {"sucesso": False, "erro": str(e)})
            return

        # ETAPA 4: Editar Parâmetro
        if path.startswith("/api/parametro/"):
            try:
                id_param = int(path[len("/api/parametro/"):])
                editar_parametro(id_param, dados['valor'])
                self.responder_json(200, {"sucesso": True})
            except Exception as e:
                self.responder_json(400, {"sucesso": False, "erro": str(e)})
            return

        self.send_error(404, "Rota PUT nao encontrada")

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # ETAPA 4: Excluir/Inativar Material (CRUD Delete)
        if path.startswith("/api/material/"):
            id_mat = path[len("/api/material/"):]
            try:
                acao = excluir_material(id_mat)
                self.responder_json(200, {"sucesso": True, "acao": acao})
            except Exception as e:
                self.responder_json(400, {"sucesso": False, "erro": str(e)})
            return

        # ETAPA 4: Excluir/Inativar Solicitante
        if path.startswith("/api/solicitante/"):
            try:
                id_solic = int(path[len("/api/solicitante/"):])
                excluir_solicitante(id_solic)
                self.responder_json(200, {"sucesso": True})
            except Exception as e:
                self.responder_json(400, {"sucesso": False, "erro": str(e)})
            return

        # ETAPA 4: Excluir Parâmetro
        if path.startswith("/api/parametro/"):
            try:
                id_param = int(path[len("/api/parametro/"):])
                excluir_parametro(id_param)
                self.responder_json(200, {"sucesso": True})
            except Exception as e:
                self.responder_json(400, {"sucesso": False, "erro": str(e)})
            return

        self.send_error(404, "Rota DELETE nao encontrada")

def iniciar_servidor(porta_inicial=None):
    global PORT
    init_db(DB_PATH)
    porta = porta_inicial or PORT
    httpd = None
    for p in range(porta, porta + 10):
        try:
            httpd = ReusableHTTPServer(("127.0.0.1", p), AlmoxarifadoHandler)
            PORT = p
            break
        except OSError:
            continue

    if not httpd:
        raise RuntimeError(f"Nao foi possivel iniciar o servidor em nenhuma porta entre {porta} e {porta+9}")

    print(f"ARGUS Almoxarifado Server rodando em http://127.0.0.1:{PORT}")
    try:
        httpd.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        httpd.server_close()

if __name__ == "__main__":
    iniciar_servidor()

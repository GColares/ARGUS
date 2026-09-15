# -*- coding: utf-8 -*-
"""
Inicializador Desktop Nativo do Terminal de Balcão do Almoxarifado (ARGUS).
Executa o servidor localmente em segundo plano e abre uma janela limpa e dedicada
em modo aplicativo (estilo Totem/PDV de loja), sem barra de navegação do browser.
"""
import os
import sys
import time
import tempfile
import threading
import subprocess
import urllib.request

# 1. Tratamento seguro de stdout/stderr para modo executável sem console (--windowed)
LOG_FILE = os.path.join(tempfile.gettempdir(), "argus_almoxarifado_app.log")

class SafeWriter:
    def __init__(self, filepath):
        self.filepath = filepath
    def write(self, s):
        if s and self.filepath:
            try:
                with open(self.filepath, "a", encoding="utf-8") as f:
                    f.write(s)
            except:
                pass
    def flush(self):
        pass

if sys.stdout is None:
    sys.stdout = SafeWriter(LOG_FILE)
if sys.stderr is None:
    sys.stderr = SafeWriter(LOG_FILE)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

import servidor
from servidor import iniciar_servidor

def aguardar_servidor(timeout=10):
    inicio = time.time()
    while time.time() - inicio < timeout:
        porta = getattr(servidor, "PORT", 5500)
        url = f"http://127.0.0.1:{porta}/api/status"
        try:
            with urllib.request.urlopen(url, timeout=1) as res:
                if res.status == 200:
                    return f"http://127.0.0.1:{porta}"
        except:
            time.sleep(0.3)
    return None

def abrir_janela_app(url):
    # 1. Caminhos do Microsoft Edge (Nativo no Windows 10/11)
    caminhos_edge = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
    ]
    
    # 2. Caminhos do Google Chrome
    caminhos_chrome = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]
    
    executavel = None
    for caminho in caminhos_edge + caminhos_chrome:
        if os.path.exists(caminho):
            executavel = caminho
            break

    profile_dir = os.path.join(
        os.environ.get("LOCALAPPDATA", tempfile.gettempdir()),
        "ARGUS_Almoxarifado_Profile"
    )
    os.makedirs(profile_dir, exist_ok=True)

    if executavel:
        cmd = [
            executavel,
            f"--app={url}",
            f"--user-data-dir={profile_dir}",
            "--start-maximized",
            "--no-first-run",
            "--no-default-browser-check"
        ]
        inicio = time.time()
        try:
            p = subprocess.Popen(cmd)
            p.wait()
            duracao = time.time() - inicio
            # Se fechou imediatamente em menos de 2s por qualquer restrição de ambiente, faz fallback
            if duracao < 2.0:
                fallback_navegador(url)
        except Exception as e:
            print(f"Erro ao abrir janela nativa: {e}")
            fallback_navegador(url)
    else:
        fallback_navegador(url)

def fallback_navegador(url):
    import webbrowser
    webbrowser.open(url)
    # Mantém o processo vivo para o servidor continuar respondendo
    while True:
        time.sleep(1)

def main():
    print("ARGUS Almoxarifado - Inicializando servidor desktop...")
    
    # Inicia o servidor HTTP em thread separada
    t = threading.Thread(target=iniciar_servidor, daemon=True)
    t.start()
    
    # Aguarda o servidor estar pronto
    url_ativa = aguardar_servidor(timeout=10)
    if url_ativa:
        print(f"Servidor online em {url_ativa}. Abrindo janela da aplicação...")
        abrir_janela_app(url_ativa)
    else:
        print("Erro: O servidor nao respondeu no tempo limite.")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n[{time.ctime()}] Timeout aguardando servidor subir.")

if __name__ == "__main__":
    main()

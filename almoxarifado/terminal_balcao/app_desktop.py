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

LOG_FILE = os.path.join(tempfile.gettempdir(), "argus_almoxarifado_app.log")
LOCK_FILE = os.path.join(tempfile.gettempdir(), "argus_almoxarifado.lock")
EDGE_PROFILE_DIR = os.path.join(tempfile.gettempdir(), "argus_edge_profile")

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

def esta_servidor_online(timeout=1):
    try:
        with urllib.request.urlopen("http://127.0.0.1:5500/api/status", timeout=timeout) as res:
            return res.status == 200
    except Exception:
        return False

def limpar_processos_residuais_edge():
    """Finaliza quaisquer processos órfãos do Edge vinculados exclusivamente ao perfil do Almoxarifado."""
    try:
        # Remove eventuais arquivos de lock do Chromium que sobraram
        for lf in ["lockfile", "SingletonLock", "SingletonCookie", "SingletonSocket"]:
            caminho = os.path.join(EDGE_PROFILE_DIR, lf)
            if os.path.exists(caminho):
                try:
                    os.remove(caminho)
                except Exception:
                    pass
        cmd = [
            "powershell", "-NoProfile", "-Command",
            "Get-CimInstance Win32_Process -Filter \"name = 'msedge.exe'\" | "
            "Where-Object { $_.CommandLine -like '*argus_edge_profile*' } | "
            "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
    except Exception:
        pass

def abrir_janela_app(url="http://127.0.0.1:5500"):
    """
    Abre a janela do aplicativo no Edge ou Chrome em modo app dedicado.
    Usa pasta de perfil exclusiva para evitar erro de concorrência/singleton (Error code 32)
    com instâncias do navegador já abertas pelo usuário.
    Retorna o objeto subprocess.Popen do processo da janela, ou None em caso de fallback.
    """
    caminhos = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
    ]

    for exe in caminhos:
        if os.path.exists(exe):
            try:
                cmd = [
                    exe,
                    f"--app={url}",
                    "--start-maximized",
                    f"--user-data-dir={EDGE_PROFILE_DIR}",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-background-mode",
                    "--disable-features=BackgroundMode",
                    "--disable-extensions"
                ]
                proc = subprocess.Popen(cmd)
                print(f"Janela dedicada aberta via: {exe} (PID {proc.pid})")
                return proc
            except Exception as e:
                print(f"Erro ao abrir com {exe}: {e}")

    try:
        os.startfile(url)
        return None
    except Exception:
        import webbrowser
        webbrowser.open(url)
        return None

def tentar_adquirir_lock():
    try:
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
        return True
    except Exception:
        return True

def liberar_lock():
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except Exception:
        pass

def monitor_heartbeat_loop():
    """
    Monitor de liveness e redundância: se a janela web esteve aberta e parar
    de enviar heartbeat por mais de 5 segundos (ex: queda súbita do navegador),
    o processo do servidor é finalizado automaticamente e o lock é liberado.
    """
    # Aguarda até 45s pelo primeiro sinal da janela carregando
    inicio = time.time()
    while time.time() - inicio < 45:
        if getattr(servidor, "HEARTBEAT_RECEBIDO", False):
            break
        time.sleep(0.5)

    if not getattr(servidor, "HEARTBEAT_RECEBIDO", False):
        print("Timeout aguardando primeiro heartbeat da janela. Encerrando servidor...")
        liberar_lock()
        limpar_processos_residuais_edge()
        os._exit(0)

    # Monitora encerramento da janela
    while True:
        time.sleep(1.5)
        if getattr(servidor, "HEARTBEAT_RECEBIDO", False):
            ultimo = getattr(servidor, "ULTIMO_HEARTBEAT", time.time())
            # Timeout grande de 30s para evitar encerramento prematuro se navegador for minimizado (Edge faz throttling do JS)
            if time.time() - ultimo > 30.0:
                print("Janela da aplicação fechada pelo usuário (sem heartbeat). Encerrando servidor...")
                liberar_lock()
                limpar_processos_residuais_edge()
                os._exit(0)

def aguardar_servidor(timeout=15):
    inicio = time.time()
    while time.time() - inicio < timeout:
        if esta_servidor_online(timeout=0.5):
            return "http://127.0.0.1:5500"
        time.sleep(0.3)
    return None

def main():
    # 1. Se o servidor JÁ está online, limpa resíduos e abre a janela do aplicativo!
    if esta_servidor_online(timeout=1):
        print("Servidor já está rodando. Abrindo janela do aplicativo...")
        limpar_processos_residuais_edge()
        abrir_janela_app("http://127.0.0.1:5500")
        sys.exit(0)

    # 2. Se não está online, garante que qualquer lock antigo e processos residuais sejam limpos
    liberar_lock()
    limpar_processos_residuais_edge()
    tentar_adquirir_lock()

    proc_janela = None
    try:
        print(f"[{time.ctime()}] ARGUS Almoxarifado - Iniciando servidor...")
        t_srv = threading.Thread(target=iniciar_servidor, daemon=True)
        t_srv.start()

        url_ativa = aguardar_servidor(timeout=15)
        if url_ativa:
            print(f"Servidor online em {url_ativa}. Abrindo janela dedicada do aplicativo...")
            proc_janela = abrir_janela_app(url_ativa)

            # Inicia monitor de heartbeat para detecção de fechamento da janela
            t_mon = threading.Thread(target=monitor_heartbeat_loop, daemon=True)
            t_mon.start()

            # Mantém processo pai ativo enquanto a sessão web estiver aberta
            while True:
                time.sleep(1)
        else:
            print("Erro: timeout aguardando servidor.")
    finally:
        liberar_lock()
        limpar_processos_residuais_edge()
        os._exit(0)

if __name__ == "__main__":
    main()
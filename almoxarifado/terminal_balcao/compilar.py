# -*- coding: utf-8 -*-
"""
Script de Compilação do Executável (.exe) do Terminal de Balcão do Almoxarifado.
Gera um aplicativo autônomo completo para Windows.
"""
import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXE = os.path.join(r"C:\ARGUS\.venv\Scripts\python.exe")
PYINSTALLER_EXE = os.path.join(r"C:\ARGUS\.venv\Scripts\pyinstaller.exe")

def compilar():
    print("=" * 60)
    print("INICIANDO COMPILACAO DO EXECUTAVEL DO ALMOXARIFADO ARGUS")
    print("=" * 60)
    
    cmd = [
        PYINSTALLER_EXE,
        "--noconfirm",
        "--onedir",                          # Modo diretório rápido (inicia instantaneamente)
        "--windowed",                        # Sem janela preta de console (janela limpa)
        "--name=ARGUS_Almoxarifado",
        f"--add-data={os.path.join(BASE_DIR, 'static')};static",
        f"--add-data={os.path.join(BASE_DIR, 'banco_almoxarifado.db')};.",
        f"--add-data={os.path.join(BASE_DIR, 'config.json')};.",
        "--hidden-import=reportlab",
        "--hidden-import=reportlab.lib",
        "--hidden-import=reportlab.platypus",
        "--hidden-import=openpyxl",
        "--hidden-import=sqlite3",
        os.path.join(BASE_DIR, "app_desktop.py")
    ]
    
    print("Executando PyInstaller...")
    resultado = subprocess.run(cmd, cwd=BASE_DIR)
    
    if resultado.returncode == 0:
        dist_dir = os.path.join(BASE_DIR, "dist", "ARGUS_Almoxarifado")
        exe_path = os.path.join(dist_dir, "ARGUS_Almoxarifado.exe")
        print("\n" + "=" * 60)
        print("COMPILACAO CONCLUIDA COM SUCESSO!")
        print(f"Executavel gerado em: {exe_path}")
        print("=" * 60)
    else:
        print("\nErro durante a compilação.")

if __name__ == "__main__":
    compilar()

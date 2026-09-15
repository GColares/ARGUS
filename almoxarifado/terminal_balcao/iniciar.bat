@echo off
chcp 65001 > nul
title ARGUS Almoxarifado

cd /d "C:\ARGUS\almoxarifado\terminal_balcao"

:: 1. Tenta usar o executável standalone compilado se existir
if exist "dist\ARGUS_Almoxarifado\ARGUS_Almoxarifado.exe" (
    start "" "dist\ARGUS_Almoxarifado\ARGUS_Almoxarifado.exe"
    exit
)

:: 2. Fallback: roda via Python
set PYTHON_EXE=C:\ARGUS\.venv\Scripts\python.exe
if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=python.exe
)

start "" "%PYTHON_EXE%" app_desktop.py
exit


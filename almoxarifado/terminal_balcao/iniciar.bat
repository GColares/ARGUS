@echo off
chcp 65001 > nul
title ARGUS Almoxarifado

cd /d "%~dp0"

set PYTHONW_EXE=C:\ARGUS\.venv\Scripts\pythonw.exe
if exist "%PYTHONW_EXE%" (
    start "" "%PYTHONW_EXE%" app_desktop.py
    exit
)

if exist "dist\ARGUS_Almoxarifado\ARGUS_Almoxarifado.exe" (
    start "" "dist\ARGUS_Almoxarifado\ARGUS_Almoxarifado.exe"
    exit
)

start "" pythonw.exe app_desktop.py
exit
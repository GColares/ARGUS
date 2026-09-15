@echo off
title Compilador do Executavel - Almoxarifado ARGUS
color 0A
echo ============================================================
echo   GERADOR DE EXECUTAVEL (.EXE) - ALMOXARIFADO ARGUS
echo ============================================================
echo.
echo Compilando o aplicativo standalone para Windows...
echo Aguarde alguns instantes...
echo.

"C:\ARGUS\.venv\Scripts\python.exe" compilar.py

echo.
echo Processo finalizado. Pressione qualquer tecla para sair.
pause >nul

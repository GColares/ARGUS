@echo off
chcp 65001 > nul
title Criar Atalho ARGUS

echo.
echo ===========================================
echo   Criando atalho do ARGUS na Area de Trabalho
echo ===========================================
echo.

set "SCRIPT_DIR=%~dp0"
set "DESKTOP_DIR=%USERPROFILE%\Desktop"
set "SHORTCUT_NAME=Almoxarifado ARGUS.lnk"
set "TARGET_PATH=%SCRIPT_DIR%iniciar_silencioso.vbs"
set "ICON_PATH=%SCRIPT_DIR%static\img\icone_almoxarifado.ico, 0"

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateShortcut.vbs"
echo sLinkFile = "%DESKTOP_DIR%\%SHORTCUT_NAME%" >> "%TEMP%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\CreateShortcut.vbs"
echo oLink.TargetPath = "%TARGET_PATH%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.IconLocation = "%ICON_PATH%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateShortcut.vbs"

cscript //nologo "%TEMP%\CreateShortcut.vbs"
del "%TEMP%\CreateShortcut.vbs"

echo Atalho criado com sucesso!
timeout /t 5 > nul
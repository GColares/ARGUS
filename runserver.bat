@echo off
REM Inicia o servidor de desenvolvimento do ARGUS na porta 8000 (Windows)
REM Execute este arquivo a partir da raiz do projeto: runserver.bat
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000

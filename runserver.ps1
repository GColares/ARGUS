# Inicia o servidor de desenvolvimento do ARGUS na porta 8000 (PowerShell)
# Execute a partir da raiz do projeto: .\runserver.ps1

Set-Location -Path $PSScriptRoot
& ".\.venv\Scripts\python.exe" ".\manage.py" runserver 127.0.0.1:8000

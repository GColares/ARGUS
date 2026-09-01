$ErrorActionPreference = 'Stop'
Write-Host "Iniciando rotina de Encerramento (Até Amanhã)..." -ForegroundColor Cyan

Write-Host "1. Atualize o diario_de_bordo.md com o que foi feito hoje se ainda não fez!" -ForegroundColor Magenta
$confirm = Read-Host "Você já atualizou o diário de bordo? (S/N)"
if ($confirm -notmatch "^[sS]") {
    Write-Host "Vá atualizar o diário primeiro e rode o script novamente!" -ForegroundColor Red
    exit
}

Write-Host "Gerando backups..." -ForegroundColor Yellow
if (!(Test-Path "backups/sql")) { New-Item -ItemType Directory -Path "backups/sql" | Out-Null }
if (!(Test-Path "backups/json")) { New-Item -ItemType Directory -Path "backups/json" | Out-Null }

$count = (Get-ChildItem backups/json/*.json -ErrorAction SilentlyContinue).Count + 1
$idStr = $count.ToString("000")
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm"

Write-Host "Salvando SQL Backup..."
$env:PGCLIENTENCODING='utf8'
$env:PGPASSWORD='argus'
& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -U postgres -d argus_db -f "backups/sql/${idStr}_db_backup_${timestamp}.sql"

Write-Host "Salvando JSON Backup..."
.\.venv\Scripts\python.exe -X utf8 manage.py dumpdata -e contenttypes -e auth.Permission --indent 2 > "backups/json/${idStr}_db_backup_${timestamp}.json"

Write-Host "Salvando Requirements..."
.\.venv\Scripts\python.exe -m pip freeze > requirements.txt

Write-Host "Commit e Push..."
git add .
$msg = Read-Host "Digite a mensagem final (ex: 'Fim do dia: Refatorado tela de projeto')"
if ([string]::IsNullOrWhiteSpace($msg)) { $msg = "Encerramento do dia" }
git commit -m $msg
git pull --rebase
git push

Write-Host "Tudo salvo! Bom descanso e até amanhã!" -ForegroundColor Green

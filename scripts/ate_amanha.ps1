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

$backupFiles = @(
    Get-ChildItem "backups/sql", "backups/json" -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^(\d{3})_db_backup_' }
)
$lastId = ($backupFiles |
    ForEach-Object { [int]([regex]::Match($_.Name, '^\d{3}').Value) } |
    Measure-Object -Maximum).Maximum
if ($null -eq $lastId) { $lastId = 0 }
$idStr = ($lastId + 1).ToString("000")
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm"

Write-Host "Salvando SQL Backup..."
if ([string]::IsNullOrWhiteSpace($env:ARGUS_DB_USER) -or
    [string]::IsNullOrWhiteSpace($env:ARGUS_DB_NAME) -or
    [string]::IsNullOrWhiteSpace($env:ARGUS_DB_PASSWORD)) {
    throw "Defina ARGUS_DB_USER, ARGUS_DB_NAME e ARGUS_DB_PASSWORD antes de gerar o backup."
}
$env:PGCLIENTENCODING = 'utf8'
$env:PGPASSWORD = $env:ARGUS_DB_PASSWORD
& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -U $env:ARGUS_DB_USER -d $env:ARGUS_DB_NAME -f "backups/sql/${idStr}_db_backup_${timestamp}.sql"
if ($LASTEXITCODE -ne 0) { throw "Falha ao gerar o backup SQL." }

Write-Host "Salvando JSON Backup..."
.\.venv\Scripts\python.exe -X utf8 manage.py dumpdata -e contenttypes -e auth.Permission --indent 2 > "backups/json/${idStr}_db_backup_${timestamp}.json"
if ($LASTEXITCODE -ne 0) { throw "Falha ao gerar o backup JSON." }

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

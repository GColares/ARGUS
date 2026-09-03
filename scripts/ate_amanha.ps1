$ErrorActionPreference = 'Stop'

function Invoke-CheckedCommand {
    param([string]$Description, [scriptblock]$Command)
    Write-Host $Description -ForegroundColor Yellow
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "Falha: $Description" }
}

Write-Host "Iniciando rotina de Encerramento (Até Amanhã)..." -ForegroundColor Cyan
if ((Read-Host "O diario_de_bordo.md foi atualizado? (S/N)") -notmatch '^[sS]$') {
    throw "Atualize o diário antes de executar a rotina."
}

New-Item -ItemType Directory -Force -Path 'backups/sql', 'backups/json' | Out-Null
$backupFiles = @(Get-ChildItem 'backups/sql', 'backups/json' -File |
    Where-Object { $_.Name -match '^\d{3}_db_backup_' })
$lastId = ($backupFiles |
    ForEach-Object { [int]([regex]::Match($_.Name, '^\d{3}').Value) } |
    Measure-Object -Maximum).Maximum
if ($null -eq $lastId) { $lastId = 0 }
$idStr = ($lastId + 1).ToString('000')
$timestamp = Get-Date -Format 'yyyy-MM-dd_HH-mm'

if ([string]::IsNullOrWhiteSpace($env:ARGUS_DB_USER) -or
    [string]::IsNullOrWhiteSpace($env:ARGUS_DB_NAME) -or
    [string]::IsNullOrWhiteSpace($env:ARGUS_DB_PASSWORD)) {
    throw "Defina ARGUS_DB_USER, ARGUS_DB_NAME e ARGUS_DB_PASSWORD antes do backup."
}

$env:PGCLIENTENCODING = 'utf8'
$env:PGPASSWORD = $env:ARGUS_DB_PASSWORD
Invoke-CheckedCommand "Gerando backup SQL ($idStr)..." {
    & "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -U $env:ARGUS_DB_USER -d $env:ARGUS_DB_NAME -f "backups/sql/${idStr}_db_backup_${timestamp}.sql"
}
Invoke-CheckedCommand "Gerando backup JSON ($idStr)..." {
    .\.venv\Scripts\python.exe -X utf8 manage.py dumpdata -e contenttypes -e auth.Permission --indent 2 > "backups/json/${idStr}_db_backup_${timestamp}.json"
}
Invoke-CheckedCommand "Exportando dependências..." {
    .\.venv\Scripts\python.exe -m pip freeze > requirements.txt
}

git status
git add .
if (-not (git diff --cached --quiet)) {
    $msg = Read-Host "Digite a mensagem final do commit"
    if ([string]::IsNullOrWhiteSpace($msg)) { $msg = 'Encerramento do dia' }
    Invoke-CheckedCommand "Criando commit..." { git commit -m $msg }
} else {
    Write-Host "Nenhuma alteração para commitar." -ForegroundColor DarkYellow
}
Invoke-CheckedCommand "Atualizando a branch antes do envio..." { git pull --rebase }
Invoke-CheckedCommand "Enviando para o GitHub..." { git push }
Write-Host "Tudo salvo e enviado! Bom descanso e até amanhã!" -ForegroundColor Green

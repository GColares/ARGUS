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

if ([string]::IsNullOrWhiteSpace($env:ARGUS_DB_USER)) { $env:ARGUS_DB_USER = 'postgres' }
if ([string]::IsNullOrWhiteSpace($env:ARGUS_DB_NAME)) { $env:ARGUS_DB_NAME = 'argus_db' }
if ([string]::IsNullOrWhiteSpace($env:ARGUS_DB_PASSWORD)) { $env:ARGUS_DB_PASSWORD = 'argus' }

# Localiza pg_dump de forma resiliente
$pgDump = "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe"
if (-not (Test-Path $pgDump)) {
    $found = (Get-Command pg_dump -ErrorAction SilentlyContinue)
    if ($found) {
        $pgDump = $found.Source
    } else {
        $alt = Get-ChildItem "C:\Program Files\PostgreSQL" -Filter "pg_dump.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
        if ($alt) { $pgDump = $alt }
    }
}

$env:PGCLIENTENCODING = 'utf8'
$env:PGPASSWORD = $env:ARGUS_DB_PASSWORD

if (Test-Path $pgDump) {
    Invoke-CheckedCommand "Gerando backup SQL ($idStr)..." {
        & $pgDump -U $env:ARGUS_DB_USER -d $env:ARGUS_DB_NAME -f "backups/sql/${idStr}_db_backup_${timestamp}.sql"
    }
} else {
    Write-Host "pg_dump.exe nao encontrado no disco. Pulando backup SQL (o backup JSON garantira a paridade)." -ForegroundColor DarkYellow
}

Invoke-CheckedCommand "Gerando backup JSON ($idStr)..." {
    .\.venv\Scripts\python.exe -X utf8 manage.py dumpdata -e contenttypes -e auth.Permission --indent 2 > "backups/json/${idStr}_db_backup_${timestamp}.json"
}

# Atualiza seed de media se houver arquivos
if (Test-Path 'media') {
    Compress-Archive -Path "media\*" -DestinationPath "backups\media_seed.zip" -CompressionLevel Fastest -Force
}

Invoke-CheckedCommand "Exportando dependências..." {
    .\.venv\Scripts\python.exe -m pip freeze > requirements.txt
}

# Exporta a memória viva do Antigravity para transplante transparente entre máquinas
if (Test-Path 'scripts/exportar_mente.ps1') {
    try {
        & .\scripts\exportar_mente.ps1
    } catch {
        Write-Host "Aviso ao exportar memória do Antigravity: $_" -ForegroundColor DarkYellow
    }
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

$currentBranch = (git branch --show-current).Trim()
$hasUpstream = (git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>$null)

if ($hasUpstream) {
    Invoke-CheckedCommand "Atualizando a branch antes do envio..." { git pull --rebase }
    Invoke-CheckedCommand "Enviando para o GitHub..." { git push }
} else {
    Invoke-CheckedCommand "Publicando e enviando a nova branch ($currentBranch) para o GitHub..." {
        git push -u origin $currentBranch
    }
}
Write-Host "Tudo salvo e enviado! Bom descanso e até amanhã!" -ForegroundColor Green

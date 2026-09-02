$ErrorActionPreference = 'Stop'
Write-Host "Iniciando rotina de Bom Dia (Sincronização Total)..." -ForegroundColor Cyan
Write-Host "Lembre-se de ler o diario_de_bordo.md para saber o status do projeto." -ForegroundColor Magenta

Write-Host "Sincronizando com a nuvem..." -ForegroundColor Yellow
git pull --rebase

Write-Host "Instalando/Sincronizando pacotes..." -ForegroundColor Yellow
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host "Sincronizando Banco de Dados..." -ForegroundColor Yellow
.\.venv\Scripts\python.exe manage.py migrate

$restaurar = Read-Host "Deseja restaurar algum backup do banco de dados? (J)son, (S)ql, ou (N)ao"
if ($restaurar -match "^[jJ]") {
    Write-Host "Listando os backups JSON mais recentes..."
    $backups = Get-ChildItem -Path "backups/json/" -Filter "*.json" |
        Where-Object { $_.Name -match '^\d{3}_db_backup_' } |
        Sort-Object LastWriteTime -Descending
    $backups | Select-Object Name -First 3
    $arquivo = Read-Host "Digite o nome exato do arquivo JSON (ex: 001_db_backup.json)"
    if (Test-Path "backups/json/$arquivo") {
        Write-Host "ATENCAO: o banco local sera limpo antes da restauracao."
        if ((Read-Host "Confirma a substituicao dos dados? (S/N)") -notmatch "^[sS]") { throw "Restauracao cancelada pelo usuario." }
        Write-Host "Limpando banco..."
        .\.venv\Scripts\python.exe manage.py flush --no-input
        if ($LASTEXITCODE -ne 0) { throw "Falha ao limpar o banco." }
        Write-Host "Restaurando..."
        .\.venv\Scripts\python.exe manage.py loaddata "backups/json/$arquivo"
        if ($LASTEXITCODE -ne 0) { throw "Falha ao restaurar o backup JSON." }
    } else {
        throw "Arquivo JSON nao encontrado."
    }
} elseif ($restaurar -match "^[sS]") {
    Write-Host "Listando os backups SQL mais recentes..."
    $backups = Get-ChildItem -Path "backups/sql/" -Filter "*.sql" |
        Where-Object { $_.Name -match '^\d{3}_db_backup_' } |
        Sort-Object LastWriteTime -Descending
    $backups | Select-Object Name -First 3
    $arquivo = Read-Host "Digite o nome exato do arquivo SQL"
    if (Test-Path "backups/sql/$arquivo") {
        if ([string]::IsNullOrWhiteSpace($env:ARGUS_DB_USER) -or
            [string]::IsNullOrWhiteSpace($env:ARGUS_DB_NAME) -or
            [string]::IsNullOrWhiteSpace($env:ARGUS_DB_PASSWORD)) {
            throw "Defina ARGUS_DB_USER, ARGUS_DB_NAME e ARGUS_DB_PASSWORD antes da restauracao."
        }
        Write-Host "ATENCAO: o schema public sera apagado antes da restauracao."
        if ((Read-Host "Confirma a substituicao dos dados? (S/N)") -notmatch "^[sS]") { throw "Restauracao cancelada pelo usuario." }
        Write-Host "Limpando schema public..."
        $env:PGCLIENTENCODING = 'utf8'
        $env:PGPASSWORD = $env:ARGUS_DB_PASSWORD
        & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U $env:ARGUS_DB_USER -d $env:ARGUS_DB_NAME -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO $env:ARGUS_DB_USER; GRANT ALL ON SCHEMA public TO public;"
        if ($LASTEXITCODE -ne 0) { throw "Falha ao limpar o schema public." }
        Write-Host "Restaurando bruto..."
        & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U $env:ARGUS_DB_USER -d $env:ARGUS_DB_NAME -f "backups/sql/$arquivo"
        if ($LASTEXITCODE -ne 0) { throw "Falha ao restaurar o backup SQL." }
    } else {
        throw "Arquivo SQL nao encontrado."
    }
}

Write-Host "Ambiente pronto para o trabalho! Bom dia!" -ForegroundColor Green

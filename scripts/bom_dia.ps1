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
    Get-ChildItem -Path "backups/json/" -Filter "*.json" | Sort-Object LastWriteTime -Descending | Select-Object Name -First 3
    $arquivo = Read-Host "Digite o nome exato do arquivo JSON (ex: 001_db_backup.json)"
    if (Test-Path "backups/json/$arquivo") {
        Write-Host "Limpando banco..."
        .\.venv\Scripts\python.exe manage.py flush --no-input
        Write-Host "Restaurando..."
        .\.venv\Scripts\python.exe manage.py loaddata "backups/json/$arquivo"
    } else {
        Write-Host "Arquivo não encontrado." -ForegroundColor Red
    }
} elseif ($restaurar -match "^[sS]") {
    Write-Host "Listando os backups SQL mais recentes..."
    Get-ChildItem -Path "backups/sql/" -Filter "*.sql" | Sort-Object LastWriteTime -Descending | Select-Object Name -First 3
    $arquivo = Read-Host "Digite o nome exato do arquivo SQL"
    if (Test-Path "backups/sql/$arquivo") {
        Write-Host "Limpando schema public..."
        $env:PGCLIENTENCODING='utf8'
        $env:PGPASSWORD='argus'
        & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d argus_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO postgres; GRANT ALL ON SCHEMA public TO public;"
        Write-Host "Restaurando bruto..."
        & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d argus_db -f "backups/sql/$arquivo"
    }
}

Write-Host "Ambiente pronto para o trabalho! Bom dia!" -ForegroundColor Green

$ErrorActionPreference = 'Stop'

function Invoke-CheckedCommand {
    param(
        [string]$Description,
        [scriptblock]$Command
    )

    Write-Host $Description -ForegroundColor Yellow
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Falha: $Description"
    }
}

function Get-BackupFiles {
    $files = @()
    foreach ($directory in @('backups/sql', 'backups/json')) {
        if (Test-Path $directory) {
            $files += Get-ChildItem $directory -File |
                Where-Object { $_.Name -match '^(?<id>\d{3})_db_backup_' }
        }
    }
    return $files
}

Write-Host "Iniciando rotina de Bom Dia (Sincronização Total)..." -ForegroundColor Cyan

Invoke-CheckedCommand "Sincronizando código com a nuvem..." { git pull --rebase }
Invoke-CheckedCommand "Instalando dependências..." { .\.venv\Scripts\python.exe -m pip install -r requirements.txt }
Invoke-CheckedCommand "Aplicando migrações..." { .\.venv\Scripts\python.exe manage.py migrate }

$backupFiles = @(Get-BackupFiles)
if ($backupFiles.Count -eq 0) {
    Write-Host "Nenhum backup versionado foi encontrado; restauração indisponível." -ForegroundColor DarkYellow
    $restaurar = 'N'
} else {
    $lastId = ($backupFiles |
        ForEach-Object { [int]([regex]::Match($_.Name, '^\d{3}').Value) } |
        Measure-Object -Maximum).Maximum
    $latestBackups = @($backupFiles | Where-Object {
        [int]([regex]::Match($_.Name, '^\d{3}').Value) -eq $lastId
    })

    Write-Host "Backup mais recente encontrado: ID $($lastId.ToString('000'))" -ForegroundColor Cyan
    $latestBackups | Select-Object Name, LastWriteTime | Format-Table -AutoSize
    $restaurar = Read-Host "Deseja restaurar esse backup? (J)son, (S)ql ou (N)ao"

    if ($restaurar -match '^[jJ]$') {
        $arquivo = $latestBackups | Where-Object Extension -eq '.json' | Select-Object -First 1
        if (-not $arquivo) { throw "Não há backup JSON para o ID mais recente." }
        Write-Host "ATENÇÃO: o banco local será limpo e substituído por $($arquivo.Name)." -ForegroundColor Red
        if ((Read-Host "Digite SUBSTITUIR para confirmar") -ne 'SUBSTITUIR') {
            throw "Restauração cancelada pelo usuário."
        }
        Invoke-CheckedCommand "Limpando banco para restauração JSON..." {
            .\.venv\Scripts\python.exe manage.py flush --no-input
        }
        Invoke-CheckedCommand "Restaurando backup JSON..." {
            .\.venv\Scripts\python.exe manage.py loaddata $arquivo.FullName
        }
        Invoke-CheckedCommand "Validando migrações após restauração..." {
            .\.venv\Scripts\python.exe manage.py showmigrations
        }
    } elseif ($restaurar -match '^[sS]$') {
        $arquivo = $latestBackups | Where-Object Extension -eq '.sql' | Select-Object -First 1
        if (-not $arquivo) { throw "Não há backup SQL para o ID mais recente." }
        if ([string]::IsNullOrWhiteSpace($env:ARGUS_DB_USER) -or
            [string]::IsNullOrWhiteSpace($env:ARGUS_DB_NAME) -or
            [string]::IsNullOrWhiteSpace($env:ARGUS_DB_PASSWORD)) {
            throw "Defina ARGUS_DB_USER, ARGUS_DB_NAME e ARGUS_DB_PASSWORD antes da restauração."
        }
        Write-Host "ATENÇÃO: o schema public será apagado e substituído por $($arquivo.Name)." -ForegroundColor Red
        if ((Read-Host "Digite SUBSTITUIR para confirmar") -ne 'SUBSTITUIR') {
            throw "Restauração cancelada pelo usuário."
        }
        $env:PGCLIENTENCODING = 'utf8'
        $env:PGPASSWORD = $env:ARGUS_DB_PASSWORD
        Invoke-CheckedCommand "Limpando schema public para restauração SQL..." {
            & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U $env:ARGUS_DB_USER -d $env:ARGUS_DB_NAME -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO $env:ARGUS_DB_USER; GRANT ALL ON SCHEMA public TO public;"
        }
        Invoke-CheckedCommand "Restaurando backup SQL..." {
            & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U $env:ARGUS_DB_USER -d $env:ARGUS_DB_NAME -f $arquivo.FullName
        }
        Invoke-CheckedCommand "Validando migrações após restauração..." {
            .\.venv\Scripts\python.exe manage.py showmigrations
        }
    } elseif ($restaurar -notmatch '^[nN]$') {
        throw "Opção inválida. Use J, S ou N."
    }
}

Write-Host "Ambiente pronto para o trabalho! Bom dia!" -ForegroundColor Green

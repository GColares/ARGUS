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

# Restauração automática de arquivos de mídia (uploads)
if (Test-Path 'backups/media_seed.zip') {
    if (-not (Test-Path 'media') -or (Get-ChildItem 'media' -Force | Measure-Object).Count -eq 0) {
        Write-Host "Restaurando arquivos de mídia (uploads/anexos)..." -ForegroundColor Cyan
        New-Item -ItemType Directory -Force -Path 'media' | Out-Null
        Expand-Archive -Path 'backups/media_seed.zip' -DestinationPath 'media' -Force
        Write-Host "Arquivos de mídia restaurados com sucesso!" -ForegroundColor Green
    }
}

# Verificação e oferta de restauração da mente viva do Antigravity
$menteZip = "$env:USERPROFILE\Downloads\mente_gemini_argus.zip"
if (Test-Path $menteZip) {
    $menteItem = Get-Item $menteZip
    Write-Host "`nPacote de mente viva do Antigravity detectado em Downloads!" -ForegroundColor Cyan
    Write-Host "Arquivo: mente_gemini_argus.zip ($([math]::Round($menteItem.Length / 1MB, 1)) MB - Modificado em: $($menteItem.LastWriteTime))" -ForegroundColor Gray
    $respMente = Read-Host "Deseja importar a memória viva do Antigravity agora? (S/N)"
    if ($respMente -match '^[sS]$') {
        if (Test-Path 'scripts/importar_mente.ps1') {
            & .\scripts\importar_mente.ps1
        }
    }
}

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
        if ([string]::IsNullOrWhiteSpace($env:ARGUS_DB_USER)) { $env:ARGUS_DB_USER = 'postgres' }
        if ([string]::IsNullOrWhiteSpace($env:ARGUS_DB_NAME)) { $env:ARGUS_DB_NAME = 'argus_db' }
        if ([string]::IsNullOrWhiteSpace($env:ARGUS_DB_PASSWORD)) { $env:ARGUS_DB_PASSWORD = 'argus' }

        # Localiza psql de forma resiliente
        $psqlTool = "C:\Program Files\PostgreSQL\18\bin\psql.exe"
        if (-not (Test-Path $psqlTool)) {
            $foundPsql = (Get-Command psql -ErrorAction SilentlyContinue)
            if ($foundPsql) {
                $psqlTool = $foundPsql.Source
            } else {
                $altPsql = Get-ChildItem "C:\Program Files\PostgreSQL" -Filter "psql.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
                if ($altPsql) { $psqlTool = $altPsql }
            }
        }
        if (-not (Test-Path $psqlTool)) {
            throw "psql.exe nao encontrado no disco para restauracao SQL."
        }

        Write-Host "ATENÇÃO: o schema public será apagado e substituído por $($arquivo.Name)." -ForegroundColor Red
        if ((Read-Host "Digite SUBSTITUIR para confirmar") -ne 'SUBSTITUIR') {
            throw "Restauração cancelada pelo usuário."
        }
        $env:PGCLIENTENCODING = 'utf8'
        $env:PGPASSWORD = $env:ARGUS_DB_PASSWORD
        Invoke-CheckedCommand "Limpando schema public para restauração SQL..." {
            & $psqlTool -U $env:ARGUS_DB_USER -d $env:ARGUS_DB_NAME -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO $env:ARGUS_DB_USER; GRANT ALL ON SCHEMA public TO public;"
        }
        Invoke-CheckedCommand "Restaurando backup SQL..." {
            & $psqlTool -U $env:ARGUS_DB_USER -d $env:ARGUS_DB_NAME -f $arquivo.FullName
        }
        Invoke-CheckedCommand "Validando migrações após restauração..." {
            .\.venv\Scripts\python.exe manage.py showmigrations
        }
    } elseif ($restaurar -notmatch '^[nN]$') {
        throw "Opção inválida. Use J, S ou N."
    }
}

Write-Host "Ambiente pronto para o trabalho! Bom dia!" -ForegroundColor Green

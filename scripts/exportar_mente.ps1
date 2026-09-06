# scripts/exportar_mente.ps1
$ErrorActionPreference = 'Stop'
$destino = "$env:USERPROFILE\Downloads\mente_gemini_argus.zip"

$tempStage = "$env:TEMP\antigravity_mente_stage"
if (Test-Path $tempStage) { Remove-Item $tempStage -Recurse -Force }
New-Item -ItemType Directory -Path "$tempStage\antigravity" -Force | Out-Null

Write-Host "Consolidando transações SQLite (WAL checkpoint)..." -ForegroundColor Gray
$pyCmd = @"
import sqlite3, glob, os
conv_dir = os.path.expanduser(r'~/.gemini/antigravity/conversations')
for db in glob.glob(os.path.join(conv_dir, '*.db')):
    try:
        con = sqlite3.connect(db)
        con.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        con.close()
    except Exception as e:
        print(f'Erro checkpoint em {db}: {e}')
"@
try {
    & python -c $pyCmd
} catch {
    Write-Host "Aviso ao rodar checkpoint Python, prosseguindo com cópia." -ForegroundColor DarkYellow
}

Write-Host "Copiando pasta brain (arquivos e logs de sessao)..." -ForegroundColor Gray
Copy-Item -Path "$env:USERPROFILE\.gemini\antigravity\brain" -Destination "$tempStage\antigravity\brain" -Recurse -Force

Write-Host "Copiando banco de dados conversations (chats consolidados)..." -ForegroundColor Gray
if (Test-Path "$env:USERPROFILE\.gemini\antigravity\conversations") {
    New-Item -ItemType Directory -Path "$tempStage\antigravity\conversations" -Force | Out-Null
    # Copia apenas os arquivos .db consolidados, evitando copiar arquivos de lock temporários (-shm e -wal corrompidos)
    Get-ChildItem -Path "$env:USERPROFILE\.gemini\antigravity\conversations\*.db" | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination "$tempStage\antigravity\conversations" -Force
    }
}

if (Test-Path "$env:USERPROFILE\.gemini\antigravity\agyhub_summaries_proto.pb") {
    Copy-Item -Path "$env:USERPROFILE\.gemini\antigravity\agyhub_summaries_proto.pb" -Destination "$tempStage\antigravity\" -Force
}

if (Test-Path $destino) {
    Remove-Item $destino -Force
}

Write-Host "Compactando pacote completo da mente do Antigravity..." -ForegroundColor Cyan
Compress-Archive -Path "$tempStage\antigravity\*" -DestinationPath $destino -CompressionLevel Fastest
Remove-Item $tempStage -Recurse -Force

Write-Host "Cerebro e historico completo exportados com sucesso para: $destino" -ForegroundColor Green
Write-Host "Copie esse arquivo para sua maquina de casa (via Drive, Pen Drive ou Nuvem)." -ForegroundColor Yellow

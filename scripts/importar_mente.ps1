# scripts/importar_mente.ps1
$ErrorActionPreference = 'Stop'
Write-Host "Importando memoria viva do Antigravity..." -ForegroundColor Cyan

$zipPath = "$env:USERPROFILE\Downloads\mente_gemini_argus.zip"
$destino = "$env:USERPROFILE\.gemini\antigravity\brain"

if (-not (Test-Path $zipPath)) {
    throw "Arquivo mente_gemini_argus.zip nao encontrado na pasta Downloads ($zipPath)."
}

# Verifica se o Antigravity está aberto e orienta a fechar para não corromper o SQLite
$procs = Get-Process | Where-Object { $_.ProcessName -eq 'Antigravity' }
if ($procs) {
    Write-Host "ATENÇÃO: O Antigravity está aberto em segundo plano ($($procs.Count) processos detectados)." -ForegroundColor Red
    Write-Host "Fechando processos do Antigravity para permitir a importação segura da memória..." -ForegroundColor Yellow
    $procs | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Limpa arquivos residuais de lock (-wal e -shm) para evitar que a UI fique em loop girando
$convDir = "$env:USERPROFILE\.gemini\antigravity\conversations"
if (Test-Path $convDir) {
    Remove-Item -Path "$convDir\*-wal" -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "$convDir\*-shm" -Force -ErrorAction SilentlyContinue
}

New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.gemini\antigravity" | Out-Null
Expand-Archive -Path $zipPath -DestinationPath "$env:USERPROFILE\.gemini\antigravity" -Force
Write-Host "Memoria do Antigravity restaurada com sucesso em: $env:USERPROFILE\.gemini\antigravity" -ForegroundColor Green
Write-Host "Abra o Antigravity agora: o historico completo estara destravado e acessivel!" -ForegroundColor Cyan


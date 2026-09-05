# scripts/importar_mente.ps1
$ErrorActionPreference = 'Stop'
Write-Host "Importando memoria viva do Antigravity..." -ForegroundColor Cyan

$zipPath = "$env:USERPROFILE\Downloads\mente_gemini_argus.zip"
$destino = "$env:USERPROFILE\.gemini\antigravity\brain"

if (-not (Test-Path $zipPath)) {
    throw "Arquivo mente_gemini_argus.zip nao encontrado na pasta Downloads ($zipPath)."
}

New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.gemini\antigravity" | Out-Null
Expand-Archive -Path $zipPath -DestinationPath "$env:USERPROFILE\.gemini\antigravity" -Force
Write-Host "Memoria do Antigravity restaurada com sucesso em: $destino" -ForegroundColor Green
Write-Host "Abra o Antigravity na maquina de casa para continuar da mesma sessao!" -ForegroundColor Cyan


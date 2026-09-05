# scripts/exportar_mente.ps1
$ErrorActionPreference = 'Stop'
Write-Host "Exportando memoria viva do Antigravity (cerebro)..." -ForegroundColor Cyan

$origem = "$env:USERPROFILE\.gemini\antigravity\brain"
$destino = "$env:USERPROFILE\Downloads\mente_gemini_argus.zip"

if (-not (Test-Path $origem)) {
    throw "Pasta brain do Antigravity nao encontrada em: $origem"
}

if (Test-Path $destino) {
    Remove-Item $destino -Force
}

Compress-Archive -Path $origem -DestinationPath $destino -CompressionLevel Fastest
Write-Host "Cerebro exportado com sucesso para: $destino" -ForegroundColor Green
Write-Host "Copie esse arquivo para sua maquina de casa (via Drive, Pen Drive ou Nuvem)." -ForegroundColor Yellow

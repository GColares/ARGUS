# scripts/exportar_mente.ps1
$ErrorActionPreference = 'Stop'
$destino = "$env:USERPROFILE\Downloads\mente_gemini_argus.zip"

$tempStage = "$env:TEMP\antigravity_mente_stage"
if (Test-Path $tempStage) { Remove-Item $tempStage -Recurse -Force }
New-Item -ItemType Directory -Path "$tempStage\antigravity" -Force | Out-Null

Write-Host "Copiando pasta brain (arquivos e logs de sessao)..." -ForegroundColor Gray
Copy-Item -Path "$env:USERPROFILE\.gemini\antigravity\brain" -Destination "$tempStage\antigravity\brain" -Recurse -Force

Write-Host "Copiando banco de dados conversations (chats e mensagens ativas)..." -ForegroundColor Gray
if (Test-Path "$env:USERPROFILE\.gemini\antigravity\conversations") {
    Copy-Item -Path "$env:USERPROFILE\.gemini\antigravity\conversations" -Destination "$tempStage\antigravity\conversations" -Recurse -Force
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

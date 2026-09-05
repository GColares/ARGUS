# scripts/instalar_plugins_antigravity.ps1
$ErrorActionPreference = 'Stop'
Write-Host "Instalando plugins do Antigravity..." -ForegroundColor Cyan

$origem = Join-Path $PSScriptRoot "plugins_antigravity"
$destino = "$env:USERPROFILE\.gemini\config\plugins"

if (-not (Test-Path $origem)) {
    throw "Pasta de origem nao encontrada: $origem"
}

New-Item -ItemType Directory -Force -Path $destino | Out-Null
Copy-Item -Path "$origem\*" -Destination $destino -Recurse -Force

Write-Host "Plugins instalados com sucesso em: $destino" -ForegroundColor Green
Write-Host "Reinicie o Antigravity para carregar os novos plugins." -ForegroundColor Cyan

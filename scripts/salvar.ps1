$ErrorActionPreference = 'Stop'
Write-Host "Iniciando salvamento parcial..." -ForegroundColor Cyan
git status
git add .
$msg = Read-Host "Digite a mensagem do commit (ou aperte Enter para usar 'Salvamento parcial')"
if ([string]::IsNullOrWhiteSpace($msg)) { $msg = "Salvamento parcial" }
git commit -m $msg
Write-Host "Sincronizando com a nuvem..." -ForegroundColor Yellow
git pull --rebase
Write-Host "Enviando para o GitHub..." -ForegroundColor Yellow
git push
Write-Host "Código salvo com sucesso na nuvem!" -ForegroundColor Green

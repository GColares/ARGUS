$desktopPath = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
$shortcutPath = Join-Path -Path $desktopPath -ChildPath "Almoxarifado ARGUS.lnk"
$targetPath = "C:\ARGUS\almoxarifado\terminal_balcao\dist\ARGUS_Almoxarifado\ARGUS_Almoxarifado.exe"
if (-not (Test-Path $targetPath)) {
    $targetPath = "C:\ARGUS\almoxarifado\terminal_balcao\iniciar_silencioso.vbs"
}
$iconPath = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

$wshShell = New-Object -ComObject WScript.Shell
$shortcut = $wshShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetPath
$shortcut.WorkingDirectory = "C:\ARGUS\almoxarifado\terminal_balcao"
$shortcut.Description = "Sistema de Balcão do Almoxarifado - Polo de Inovação IFAM"
$shortcut.IconLocation = "$iconPath, 0"
$shortcut.Save()

Write-Host "Atalho criado com sucesso na Area de Trabalho: $shortcutPath"


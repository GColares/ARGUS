$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$dir = "C:\Projetos\ARGUS\gestao_projetos\execucao_financeira"
$dispFile = Get-ChildItem -Path $dir -Filter "*BIO CAROCO 2026.xlsx" | Select-Object -First 1 -ExpandProperty FullName

Write-Host "Opening: $dispFile"
$wb = $excel.Workbooks.Open($dispFile)
$ws = $wb.Sheets.Item('Cronograma Desembolso')
Write-Host "Cronograma Desembolso UsedRange: " $ws.UsedRange.Address
for ($r = 1; $r -le 35; $r++) {
    $line = @()
    for ($c = 1; $c -le 8; $c++) {
        $t = $ws.Cells.Item($r, $c).Text
        if ($t) { $line += ("C" + $c + ": " + $t) }
    }
    if ($line.Count -gt 0) {
        Write-Host ("Row " + $r + ": " + ($line -join " | "))
    }
}
$wb.Close($false)
$excel.Quit()

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$f = "C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\execucao_orcamentaria.xlsx"
$wb = $excel.Workbooks.Open($f)
$ws = $wb.Sheets.Item('orcamento_biocaroco')
Write-Host "orcamento_biocaroco usedrange: " $ws.UsedRange.Address
for ($r = 1; $r -le 25; $r++) {
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

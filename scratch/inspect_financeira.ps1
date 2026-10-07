$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$wb = $excel.Workbooks.Open('C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\execucao_financeira.xlsx')
foreach ($s in $wb.Sheets) {
    Write-Host "Sheet: $($s.Name)"
    Write-Host "Tables in sheet: $($s.ListObjects.Count)"
    for ($t = 1; $t -le $s.ListObjects.Count; $t++) {
        $tbl = $s.ListObjects.Item($t)
        Write-Host "  Table: $($tbl.Name), Range: $($tbl.Range.Address)"
    }
}
$wsExt = $wb.Sheets.Item('extrato_bancario')
Write-Host "extrato_bancario header (Row 1):"
for ($c = 1; $c -le 15; $c++) {
    Write-Host ("  C" + $c + ": " + $wsExt.Cells.Item(1, $c).Text)
}
Write-Host "extrato_bancario rows count: $($wsExt.UsedRange.Rows.Count)"

$wsDin = $wb.Sheets.Item('dinamic')
Write-Host "dinamic usedrange: $($wsDin.UsedRange.Address)"
for ($r = 1; $r -le 25; $r++) {
    $line = @()
    for ($c = 1; $c -le 10; $c++) {
        $t = $wsDin.Cells.Item($r, $c).Text
        if ($t) { $line += ("C" + $c + ": " + $t) }
    }
    if ($line.Count -gt 0) {
        Write-Host ("Row " + $r + ": " + ($line -join ' | '))
    }
}

$wb.Close($false)
$excel.Quit()

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$wb = $excel.Workbooks.Open('C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\relatorio_mensal_recursos.xlsx')
$ws = $wb.Sheets.Item('det_execucao_orcamentaria')
Write-Host "Shape count in det_execucao_orcamentaria: " $ws.Shapes.Count
for ($i = 1; $i -le $ws.Shapes.Count; $i++) {
    Write-Host ("Shape " + $i + ": Name=" + $ws.Shapes.Item($i).Name + ", Type=" + $ws.Shapes.Item($i).Type)
}
Write-Host "Table / ListObject count: " $ws.ListObjects.Count
if ($ws.ListObjects.Count -gt 0) {
    $tbl = $ws.ListObjects.Item(1)
    Write-Host ("Table Name: " + $tbl.Name + ", Range: " + $tbl.Range.Address)
    for ($c = 1; $c -le $tbl.ListColumns.Count; $c++) {
        Write-Host ("Col " + $c + ": " + $tbl.ListColumns.Item($c).Name)
    }
}
Write-Host "`nRows 1 and 2 content:"
for ($r = 1; $r -le 2; $r++) {
    for ($c = 1; $c -le 8; $c++) {
        Write-Host ("R" + $r + "C" + $c + " = " + $ws.Cells.Item($r, $c).Text)
    }
}
$wb.Close($false)
$excel.Quit()

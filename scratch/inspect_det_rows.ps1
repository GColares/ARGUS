$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$wb = $excel.Workbooks.Open('C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\relatorio_mensal_recursos.xlsx')
$ws = $wb.Sheets.Item('det_execucao_orcamentaria')
Write-Host "det_execucao_orcamentaria rows:"
for ($r = 1; $r -le 16; $r++) {
    $rub = $ws.Cells.Item($r, 1).Text
    $prev = $ws.Cells.Item($r, 2).Text
    $exec = $ws.Cells.Item($r, 4).Text
    $disp = $ws.Cells.Item($r, 5).Text
    $pct = $ws.Cells.Item($r, 6).Text
    $fPrev = $ws.Cells.Item($r, 2).Formula
    $fExec = $ws.Cells.Item($r, 4).Formula
    Write-Host ("Row $r : Rubrica='$rub' | Prev=$prev ($fPrev) | Exec=$exec ($fExec) | Disp=$disp | Pct=$pct")
}
$wb.Close($false)
$excel.Quit()

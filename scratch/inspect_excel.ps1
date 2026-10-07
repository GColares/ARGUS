$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$wb = $excel.Workbooks.Open('C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\relatorio_mensal_recursos.xlsx')
Write-Host "Sheets in relatorio_mensal_recursos.xlsx:"
foreach ($s in $wb.Sheets) {
    Write-Host (" - " + $s.Name)
}
$wsDet = $wb.Sheets.Item("det_execucao_orcamentaria")
Write-Host ("UsedRange in det_execucao_orcamentaria: " + $wsDet.UsedRange.Address)
for ($r = 1; $r -le 20; $r++) {
    $rowVals = @()
    for ($c = 1; $c -le 10; $c++) {
        $form = $wsDet.Cells.Item($r, $c).Formula
        $val = $wsDet.Cells.Item($r, $c).Text
        if ($form -ne $null -and $form -ne "") {
            $rowVals += ("C" + $c + ": Form=" + $form + " [Val=" + $val + "]")
        }
    }
    if ($rowVals.Count -gt 0) {
        Write-Host ("Row $r : " + ($rowVals -join " | "))
    }
}
$wb.Close($false)
$excel.Quit()

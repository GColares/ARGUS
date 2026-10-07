$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$f = "C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\execucao_financeira.xlsx"
$wb = $excel.Workbooks.Open($f)
$ws = $wb.Sheets.Item("extrato_bancario")
for ($r = 2; $r -le 85; $r++) {
    $rub = $ws.Cells.Item($r, 5).Text
    $cta = $ws.Cells.Item($r, 4).Text
    if ($rub -like "*Terceiro*") {
        Write-Host ("Linha de Terceiros: " + $r + " | Val=" + $ws.Cells.Item($r, 10).Value2 + " | Desc=" + $ws.Cells.Item($r, 9).Text)
    }
    if ($rub -like "*Tribut*") {
        Write-Host ("Linha de Tributos: " + $r + " | Val=" + $ws.Cells.Item($r, 10).Value2 + " | Desc=" + $ws.Cells.Item($r, 9).Text)
    }
    if ($rub -like "*Tarifa*" -and $cta -like "*SEBRAE*") {
        Write-Host ("Tarifa SEBRAE: " + $r + " | Val=" + $ws.Cells.Item($r, 10).Value2)
    }
}
$wb.Close($false)
$excel.Quit()

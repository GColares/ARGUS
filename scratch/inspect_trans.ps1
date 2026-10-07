$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$f = "C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\execucao_financeira.xlsx"
$wb = $excel.Workbooks.Open($f)
$ws = $wb.Sheets.Item('extrato_bancario')

Write-Host "--- ITENS ESPECIFICOS NO EXTRATO BANCARIO ---"
for ($r = 2; $r -le $ws.UsedRange.Rows.Count; $r++) {
    $rub = $ws.Cells.Item($r, 5).Text
    $tipo = $ws.Cells.Item($r, 8).Text
    $desc = $ws.Cells.Item($r, 9).Text
    $val = $ws.Cells.Item($r, 10).Value2
    $cta = $ws.Cells.Item($r, 4).Text

    if ($rub -like "*ISS*" -or $rub -like "*Tribut*" -or $rub -like "*Terceiro*" -or $rub -like "*Tarifa*" -or $rub -like "*Investimento*") {
        Write-Host "Row $r : Cta=$cta | Rub=$rub | Tipo=$tipo | Val=$val | Desc=$desc"
    }
}

$wb.Close($false)
$excel.Quit()

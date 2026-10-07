$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$f = "C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\execucao_financeira.xlsx"
$wb = $excel.Workbooks.Open($f)
$ws = $wb.Sheets.Item('extrato_bancario')

Write-Host "Linhas de RECEITA no extrato_bancario:"
for ($r = 2; $r -le $ws.UsedRange.Rows.Count; $r++) {
    $rub = $ws.Cells.Item($r, 5).Text
    if ($rub -like "*Receita*") {
        $dt = $ws.Cells.Item($r, 2).Text
        $cta = $ws.Cells.Item($r, 4).Text
        $doc = $ws.Cells.Item($r, 6).Text
        $val = $ws.Cells.Item($r, 10).Value2
        Write-Host "Row $r : Data=$dt | Conta=$cta | Doc=$doc | Valor=$val"
    }
}

$wb.Close($false)
$excel.Quit()

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$f = "C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\execucao_financeira.xlsx"
$wb = $excel.Workbooks.Open($f)
$ws = $wb.Sheets.Item('extrato_bancario')
$rowCount = $ws.UsedRange.Rows.Count

$rubricas = @{}
$contas = @{}
$totalDebitos = 0
$totalCreditos = 0

for ($r = 2; $r -le $rowCount; $r++) {
    $conta = $ws.Cells.Item($r, 4).Text
    $rub = $ws.Cells.Item($r, 5).Text
    $tipo = $ws.Cells.Item($r, 8).Text
    $val = $ws.Cells.Item($r, 10).Value2

    if ($rub) {
        if (-not $rubricas.ContainsKey($rub)) { $rubricas[$rub] = 0 }
        $rubricas[$rub] += [double]$val
    }
    if ($conta) {
        if (-not $contas.ContainsKey($conta)) { $contas[$conta] = 0 }
        $contas[$conta] += [double]$val
    }
}

Write-Host "--- TOTAL POR RUBRICA NO EXTRATO BANCARIO ---"
foreach ($k in $rubricas.Keys) {
    Write-Host ("Rubrica: " + $k + " = " + $rubricas[$k])
}

Write-Host "`n--- TOTAL POR CONTA NO EXTRATO BANCARIO ---"
foreach ($k in $contas.Keys) {
    Write-Host ("Conta: " + $k + " = " + $contas[$k])
}

$wb.Close($false)
$excel.Quit()

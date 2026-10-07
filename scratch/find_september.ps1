$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$f = "C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\execucao_financeira.xlsx"
$wb = $excel.Workbooks.Open($f)
$ws = $wb.Sheets.Item("extrato_bancario")
$debSet = 0
$rendSetBruto = 0
$irrfSet = 0

for ($r = 2; $r -le 85; $r++) {
    $mes = $ws.Cells.Item($r, 3).Text
    $tipo = $ws.Cells.Item($r, 8).Text
    $val = [double]$ws.Cells.Item($r, 10).Value2

    if ($mes -eq "setembro") {
        Write-Host "Setembro Row $r : Val=$val | Tipo=$tipo | Desc=$($ws.Cells.Item($r, 9).Text)"
        if ($val -lt 0 -and $tipo -ne "IRRF Reteno Pessoa Jurdica" -and $tipo -ne "IRRF Pessoa Jurdica") {
            $debSet += $val
        }
        if ($tipo -eq "Aplicao Financeira") {
            $rendSetBruto += $val
        }
        if ($tipo -like "*IRRF*") {
            $irrfSet += $val
        }
    }
}

Write-Host "Debitos Setembro total: $debSet"
Write-Host "Rendimento Bruto Setembro: $rendSetBruto"
Write-Host "IRRF Setembro: $irrfSet"

$wb.Close($false)
$excel.Quit()

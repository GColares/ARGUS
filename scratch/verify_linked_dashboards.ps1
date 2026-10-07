$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$filePath = "C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\relatorio_mensal_recursos.xlsx"
$wb = $excel.Workbooks.Open($filePath)

Write-Host "=== VERIFICACAO DAS ABAS E FORMULAS VINCULADAS ===" -ForegroundColor Cyan

foreach ($sheetName in @("Slide 2 - Saude do Projeto", "Slide 3 - Desembolso e Contas", "Slide 4 - Analise e Atencao")) {
    $ws = $wb.Sheets.Item($sheetName)
    Write-Host "`n>>> SHEET: $sheetName <<<" -ForegroundColor Yellow
    
    # Check used range for any errors
    $errorsFound = 0
    for ($r = 1; $r -le 20; $r++) {
        for ($c = 1; $c -le 11; $c++) {
            $cell = $ws.Cells.Item($r, $c)
            $text = $cell.Text
            $form = $cell.Formula
            if ($text -like "#*") {
                Write-Host "  [ERRO DETECTADO] R${r}C${c}: Form='$form', Text='$text'" -ForegroundColor Red
                $errorsFound++
            }
        }
    }
    if ($errorsFound -eq 0) {
        Write-Host "  Status: ZERO ERROS de formula (#REF!, #NAME?, #VALUE!) encontrados!" -ForegroundColor Green
    }
}

# Detailed cell dump for Slide 2
$ws2 = $wb.Sheets.Item("Slide 2 - Saude do Projeto")
Write-Host "`n--- SLIDE 2: KPI CARDS ---" -ForegroundColor Cyan
Write-Host "  Saldo Disponivel (B6): $($ws2.Range('B6').Text) [Form: $($ws2.Range('B6').Formula)]"
Write-Host "  Receitas (D6): $($ws2.Range('D6').Text) [Form: $($ws2.Range('D6').Formula)]"
Write-Host "  Total Executado (F6): $($ws2.Range('F6').Text) [Form: $($ws2.Range('F6').Formula)]"
Write-Host "  Rendimento (H6): $($ws2.Range('H6').Text) [Form: $($ws2.Range('H6').Formula)]"

Write-Host "`n--- SLIDE 2: TABELA DE RUBRICAS ---" -ForegroundColor Cyan
for ($r = 11; $r -le 17; $r++) {
    $rub = $ws2.Cells.Item($r, 2).Text
    $orc = $ws2.Cells.Item($r, 4).Text
    $exe = $ws2.Cells.Item($r, 6).Text
    $dsp = $ws2.Cells.Item($r, 8).Text
    $pct = $ws2.Cells.Item($r, 10).Text
    $fExe = $ws2.Cells.Item($r, 6).Formula
    Write-Host "  Row $r : $rub | Orc=$orc | Exe=$exe | Dsp=$dsp | Pct=$pct | FormExe=$fExe"
}

# Detailed cell dump for Slide 3
$ws3 = $wb.Sheets.Item("Slide 3 - Desembolso e Contas")
Write-Host "`n--- SLIDE 3: PARCELAS RECEBIDAS ---" -ForegroundColor Cyan
for ($r = 7; $r -le 9; $r++) {
    Write-Host "  Row $r : $($ws3.Cells.Item($r, 2).Text) | Doc=$($ws3.Cells.Item($r, 3).Text) | Dt=$($ws3.Cells.Item($r, 4).Text) | Val=$($ws3.Cells.Item($r, 5).Text) [Form: $($ws3.Cells.Item($r, 5).Formula)]"
}
Write-Host "  Total Recebido (E14): $($ws3.Range('E14').Text) [Form: $($ws3.Range('E14').Formula)]"
Write-Host "  Resumo Saldo (J8): $($ws3.Range('J8').Text) [Form: $($ws3.Range('J8').Formula)]"
Write-Host "  Rend. Acumulado (J14): $($ws3.Range('J14').Text) [Form: $($ws3.Range('J14').Formula)]"

# Detailed cell dump for Slide 4
$ws4 = $wb.Sheets.Item("Slide 4 - Analise e Atencao")
Write-Host "`n--- SLIDE 4: EXECUCAO GERAL & SALDO ---" -ForegroundColor Cyan
Write-Host "  Execucao Geral (G6): $($ws4.Range('G6').Text) [Form: $($ws4.Range('G6').Formula)]"
Write-Host "  Subtexto Execucao (G7): $($ws4.Range('G7').Text)"
Write-Host "  Saldo Disponivel (G10): $($ws4.Range('G10').Text) [Form: $($ws4.Range('G10').Formula)]"

$wb.Close($false)
$excel.Quit()

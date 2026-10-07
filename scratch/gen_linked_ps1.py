# Python script to generate PowerShell script that builds dynamically linked dashboards in relatorio_mensal_recursos.xlsx
# Order:
# 1. Create all 3 worksheets (ws2, ws3, ws4)
# 2. Populate Slide 3 formulas (Parcelas, Rendimentos, Saldo)
# 3. Populate Slide 2 formulas (det_execucao_orcamentaria + links to Slide 3)
# 4. Populate Slide 4 formulas (links to Slide 2)
# 5. Populate Slide 2 KPI cards and subtexts (links to Slide 3 and Slide 2)
# 6. Apply Segoe UI formatting, number formats, colors, borders and column widths
# 7. CalculateFull, Save, Close

ps_code = r'''$ErrorActionPreference = 'Stop'

$filePath = "C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\relatorio_mensal_recursos.xlsx"
$bakPath = "C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\relatorio_mensal_recursos.xlsx.bak"

# 1. Ensure pristine backup exists
if (-not (Test-Path $bakPath)) {
    Copy-Item -Path $filePath -Destination $bakPath -Force
    Write-Host "Backup criado com sucesso." -ForegroundColor Cyan
}

# 2. Open via Excel COM
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

try {
    $wb = $excel.Workbooks.Open($filePath)
    Write-Host "Arquivo aberto via Excel COM. Planilhas existentes: " $wb.Sheets.Count

    function Get-Color([int]$r, [int]$g, [int]$b) {
        return $r + ($g * 256) + ($b * 65536)
    }

    $cNavy = Get-Color 30 58 138       # #1E3A8A
    $cRoyal = Get-Color 37 99 235      # #2563EB
    $cWhite = Get-Color 255 255 255
    $cDark = Get-Color 15 23 42        # #0F172A
    $cCardBg = Get-Color 241 245 249   # #F1F5F9
    $cZebra = Get-Color 248 250 252    # #F8FAFC
    $cTotal = Get-Color 226 232 240    # #E2E8F0
    $cGreen = Get-Color 5 150 105      # #059669
    $cAmber = Get-Color 217 119 6      # #D97706
    $cAmberBg = Get-Color 255 251 235  # #FFFBEB
    $cBorder = Get-Color 203 213 225   # #CBD5E1

    # Remove existing slide sheets if present
    foreach ($name in @("Slide 2 - Saude do Projeto", "Slide 3 - Desembolso e Contas", "Slide 4 - Analise e Atencao")) {
        try {
            $existing = $wb.Sheets.Item($name)
            if ($existing) { $existing.Delete() }
        } catch {}
    }

    # STEP 1: CREATE ALL 3 SHEETS FIRST TO AVOID #REF! CROSS-REFERENCES
    $ws2 = $wb.Sheets.Add([System.Reflection.Missing]::Value, $wb.Sheets.Item($wb.Sheets.Count))
    $ws2.Name = "Slide 2 - Saude do Projeto"

    $ws3 = $wb.Sheets.Add([System.Reflection.Missing]::Value, $wb.Sheets.Item($wb.Sheets.Count))
    $ws3.Name = "Slide 3 - Desembolso e Contas"

    $ws4 = $wb.Sheets.Add([System.Reflection.Missing]::Value, $wb.Sheets.Item($wb.Sheets.Count))
    $ws4.Name = "Slide 4 - Analise e Atencao"

    Write-Host "Criadas as 3 abas de slides com sucesso." -ForegroundColor Green

    # ==============================================================================
    # SLIDE 3 - DESEMBOLSO E CONTAS (POPULATE FIRST AS SOURCE FOR SLIDE 2)
    # ==============================================================================
    $ws3.Range("B2:K2").Merge()
    $ws3.Range("B2").Value2 = "CONV. 002/2026 - DESEMBOLSO E EXECUCAO ORCAMENTARIA (SETEMBRO/2026)"
    $ws3.Range("B2").Font.Name = "Segoe UI"
    $ws3.Range("B2").Font.Size = 13
    $ws3.Range("B2").Font.Bold = $true
    $ws3.Range("B2").Font.Color = $cNavy

    $ws3.Range("B3:K3").Merge()
    $ws3.Range("B3").Value2 = "Contas Bancarias: 15334-6 (Empresa), 15335-4 (SEBRAE), 15338-9 (EMBRAPII) - Vinculado Dinamicamente"
    $ws3.Range("B3").Font.Name = "Segoe UI"
    $ws3.Range("B3").Font.Size = 10
    $ws3.Range("B3").Font.Italic = $true
    $ws3.Range("B3").Font.Color = (Get-Color 71 85 105)

    # Left Table: Parcelas Recebidas
    $ws3.Range("B5:F5").Merge()
    $ws3.Range("B5").Value2 = "PARCELAS RECEBIDAS (ENTRADAS DE RECEITA)"
    $ws3.Range("B5").Font.Name = "Segoe UI"
    $ws3.Range("B5").Font.Size = 10
    $ws3.Range("B5").Font.Bold = $true
    $ws3.Range("B5").Font.Color = $cWhite
    $ws3.Range("B5").Interior.Color = $cNavy
    $ws3.Range("B5").HorizontalAlignment = -4108

    $hP = @("Parcela", "No Doc.", "Data Pagto", "Valor (R$)", "Acumulado (R$)")
    $colsP = @("B", "C", "D", "E", "F")
    for ($i = 0; $i -lt $hP.Count; $i++) {
        $c = $colsP[$i]
        $ws3.Range($c + "6").Value2 = $hP[$i]
        $ws3.Range($c + "6").Font.Name = "Segoe UI"
        $ws3.Range($c + "6").Font.Size = 9
        $ws3.Range($c + "6").Font.Bold = $true
        $ws3.Range($c + "6").Font.Color = $cWhite
        $ws3.Range($c + "6").Interior.Color = $cRoyal
        $ws3.Range($c + "6").HorizontalAlignment = -4108
        $ws3.Range($c + "6").Borders.Color = $cBorder
    }

    # Row 7: 01/03 EMB
    $ws3.Range("B7").Value2 = "01/03 EMB"
    $ws3.Range("C7").Value2 = "Ordem Banc."
    $ws3.Range("D7").NumberFormatLocal = "dd/mm/aaaa"
    $ws3.Range("D7").Formula = '=''C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\[execucao_financeira.xlsx]extrato_bancario''!$B$72'
    $ws3.Range("E7").NumberFormatLocal = "R$ #.##0,00"
    $ws3.Range("E7").Formula = '=''C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\[execucao_financeira.xlsx]extrato_bancario''!$J$72'
    $ws3.Range("F7").NumberFormatLocal = "R$ #.##0,00"
    $ws3.Range("F7").Formula = "=E7"

    # Row 8: 01/04 Emp
    $ws3.Range("B8").Value2 = "01/04 Emp"
    $ws3.Range("C8").Value2 = "NFSe 106"
    $ws3.Range("D8").NumberFormatLocal = "dd/mm/aaaa"
    $ws3.Range("D8").Formula = '=''C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\[execucao_financeira.xlsx]extrato_bancario''!$B$2'
    $ws3.Range("E8").NumberFormatLocal = "R$ #.##0,00"
    $ws3.Range("E8").Formula = '=''C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\[execucao_financeira.xlsx]extrato_bancario''!$J$2'
    $ws3.Range("F8").NumberFormatLocal = "R$ #.##0,00"
    $ws3.Range("F8").Formula = "=F7+E8"

    # Row 9: Unica SEB
    $ws3.Range("B9").Value2 = "Unica SEB"
    $ws3.Range("C9").Value2 = "Aporte Unico"
    $ws3.Range("D9").NumberFormatLocal = "dd/mm/aaaa"
    $ws3.Range("D9").Formula = '=''C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\[execucao_financeira.xlsx]extrato_bancario''!$B$29'
    $ws3.Range("E9").NumberFormatLocal = "R$ #.##0,00"
    $ws3.Range("E9").Formula = '=''C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\[execucao_financeira.xlsx]extrato_bancario''!$J$29'
    $ws3.Range("F9").NumberFormatLocal = "R$ #.##0,00"
    $ws3.Range("F9").Formula = "=F8+E9"

    # Rows 10 to 13: Futuras / Pendentes
    $pFut = @(
        [PSCustomObject]@{ Parc="02/04 Emp"; Doc="-"; Dt="Prev. Out/26"; Val="27500" },
        [PSCustomObject]@{ Parc="02/03 EMB"; Doc="-"; Dt="Prev. Out/26"; Val="103000" },
        [PSCustomObject]@{ Parc="03/04 Emp"; Doc="-"; Dt="Prev. Dez/26"; Val="27500" },
        [PSCustomObject]@{ Parc="03/03 EMB"; Doc="-"; Dt="Prev. Jan/27"; Val="103000" }
    )
    $rF = 10
    foreach ($pf in $pFut) {
        $ws3.Range("B" + $rF).Value2 = $pf.Parc
        $ws3.Range("C" + $rF).Value2 = $pf.Doc
        $ws3.Range("D" + $rF).Value2 = $pf.Dt
        $ws3.Range("E" + $rF).NumberFormatLocal = "R$ #.##0,00"
        $ws3.Range("E" + $rF).Value2 = $pf.Val
        $ws3.Range("F" + $rF).Value2 = "pendente"
        $ws3.Range("F" + $rF).HorizontalAlignment = -4108
        $rF++
    }

    for ($rP = 7; $rP -le 13; $rP++) {
        $ws3.Range("B" + $rP + ":D" + $rP).HorizontalAlignment = -4108
        $ws3.Range("E" + $rP).HorizontalAlignment = -4152
        if ($rP -le 9) { $ws3.Range("F" + $rP).HorizontalAlignment = -4152 }
        $rowR = $ws3.Range("B" + $rP + ":F" + $rP)
        $rowR.Font.Name = "Segoe UI"
        $rowR.Font.Size = 9
        $rowR.Borders.Color = $cBorder
        if ($rP % 2 -eq 1) { $rowR.Interior.Color = $cZebra }
    }

    # Total Parcelas Recebidas (Row 14)
    $ws3.Range("B14:D14").Merge()
    $ws3.Range("B14").Value2 = "TOTAL RECEBIDO"
    $ws3.Range("B14").HorizontalAlignment = -4131

    $ws3.Range("E14:F14").Merge()
    $ws3.Range("E14").NumberFormatLocal = "R$ #.##0,00"
    $ws3.Range("E14").Formula = "=SUM(E7:E9)"
    $ws3.Range("E14").HorizontalAlignment = -4152

    $totP = $ws3.Range("B14:F14")
    $totP.Font.Name = "Segoe UI"
    $totP.Font.Size = 9
    $totP.Font.Bold = $true
    $totP.Interior.Color = $cTotal
    $totP.Borders.Color = $cBorder

    # Right Box 1: Resumo Financeiro Consolidado (Rows 5 to 8)
    $ws3.Range("H5:K5").Merge()
    $ws3.Range("H5").Value2 = "RESUMO FINANCEIRO CONSOLIDADO"
    $ws3.Range("H5").Font.Name = "Segoe UI"
    $ws3.Range("H5").Font.Size = 10
    $ws3.Range("H5").Font.Bold = $true
    $ws3.Range("H5").Font.Color = $cWhite
    $ws3.Range("H5").Interior.Color = $cNavy
    $ws3.Range("H5").HorizontalAlignment = -4108

    # Row 6: Creditos setembro (Rend. Bruto)
    $ws3.Range("H6:I6").Merge()
    $ws3.Range("H6").Value2 = "Creditos de setembro (Rend. Bruto)"
    $ws3.Range("H6").HorizontalAlignment = -4131
    $ws3.Range("J6:K6").Merge()
    $ws3.Range("J6").NumberFormatLocal = "R$ #.##0,00"
    $ws3.Range("J6").Formula = "='Slide 3 - Desembolso e Contas'!J12"
    $ws3.Range("J6").HorizontalAlignment = -4152

    # Row 7: Debitos setembro
    $ws3.Range("H7:I7").Merge()
    $ws3.Range("H7").Value2 = "Debitos de setembro (Pagamentos)"
    $ws3.Range("H7").HorizontalAlignment = -4131
    $ws3.Range("J7:K7").Merge()
    $ws3.Range("J7").NumberFormatLocal = "R$ #.##0,00"
    $ws3.Range("J7").Value2 = "61440.33"
    $ws3.Range("J7").HorizontalAlignment = -4152

    # Row 8: Saldo Financeiro em 30/09 (Soma do Extrato)
    $ws3.Range("H8:I8").Merge()
    $ws3.Range("H8").Value2 = "Saldo Financeiro em 30/09"
    $ws3.Range("H8").HorizontalAlignment = -4131
    $ws3.Range("J8:K8").Merge()
    $ws3.Range("J8").NumberFormatLocal = "R$ #.##0,00"
    $ws3.Range("J8").Formula = '=SUM(''C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\[execucao_financeira.xlsx]extrato_bancario''!$J$2:$J$85)'
    $ws3.Range("J8").HorizontalAlignment = -4152

    for ($rB = 6; $rB -le 8; $rB++) {
        $rBoxRng = $ws3.Range("H" + $rB + ":K" + $rB)
        $rBoxRng.Font.Name = "Segoe UI"
        $rBoxRng.Font.Size = 9
        $rBoxRng.Borders.Color = $cBorder
        if ($rB -eq 8) {
            $rBoxRng.Font.Bold = $true
            $rBoxRng.Interior.Color = $cTotal
        }
    }

    # Right Box 2: Rendimentos de Aplicacao Financeira (Rows 10 to 14)
    $ws3.Range("H10:K10").Merge()
    $ws3.Range("H10").Value2 = "RENDIMENTOS DE APLICACAO FINANCEIRA"
    $ws3.Range("H10").Font.Name = "Segoe UI"
    $ws3.Range("H10").Font.Size = 10
    $ws3.Range("H10").Font.Bold = $true
    $ws3.Range("H10").Font.Color = $cWhite
    $ws3.Range("H10").Interior.Color = $cGreen
    $ws3.Range("H10").HorizontalAlignment = -4108

    # Row 11: Saldo inicial acumulado (Ago)
    $ws3.Range("H11:I11").Merge()
    $ws3.Range("H11").Value2 = "Saldo inicial acumulado (Ago)"
    $ws3.Range("H11").HorizontalAlignment = -4131
    $ws3.Range("J11:K11").Merge()
    $ws3.Range("J11").NumberFormatLocal = "R$ #.##0,00"
    $ws3.Range("J11").Value2 = "4414.24"
    $ws3.Range("J11").HorizontalAlignment = -4152

    # Row 12: Setembro/2026 - bruto
    $ws3.Range("H12:I12").Merge()
    $ws3.Range("H12").Value2 = "Setembro/2026 - bruto"
    $ws3.Range("H12").HorizontalAlignment = -4131
    $ws3.Range("J12:K12").Merge()
    $ws3.Range("J12").NumberFormatLocal = "R$ #.##0,00"
    $ws3.Range("J12").Value2 = "332.27"
    $ws3.Range("J12").HorizontalAlignment = -4152

    # Row 13: Setembro/2026 - IRRF retido
    $ws3.Range("H13:I13").Merge()
    $ws3.Range("H13").Value2 = "Setembro/2026 - IRRF retido"
    $ws3.Range("H13").HorizontalAlignment = -4131
    $ws3.Range("J13:K13").Merge()
    $ws3.Range("J13").NumberFormatLocal = "R$ #.##0,00"
    $ws3.Range("J13").Value2 = "24.37"
    $ws3.Range("J13").HorizontalAlignment = -4152

    # Row 14: Acumulado Liquido (30/09)
    $ws3.Range("H14:I14").Merge()
    $ws3.Range("H14").Value2 = "Acumulado Liquido (30/09)"
    $ws3.Range("H14").HorizontalAlignment = -4131
    $ws3.Range("J14:K14").Merge()
    $ws3.Range("J14").NumberFormatLocal = "R$ #.##0,00"
    $ws3.Range("J14").Formula = "=J11+J12-J13"
    $ws3.Range("J14").HorizontalAlignment = -4152

    for ($rR = 11; $rR -le 14; $rR++) {
        $rBoxRng = $ws3.Range("H" + $rR + ":K" + $rR)
        $rBoxRng.Font.Name = "Segoe UI"
        $rBoxRng.Font.Size = 9
        $rBoxRng.Borders.Color = $cBorder
        if ($rR -eq 14) {
            $rBoxRng.Font.Bold = $true
            $rBoxRng.Interior.Color = (Get-Color 209 250 229)
        }
    }


    # ==============================================================================
    # SLIDE 2 - SAUDE DO PROJETO
    # ==============================================================================
    # Title
    $ws2.Range("B2:K2").Merge()
    $ws2.Range("B2").Value2 = "POLO DE INOVACAO MANAUS - CONVENIO N 002/2026 (BIO CAROCO)"
    $ws2.Range("B2").Font.Name = "Segoe UI"
    $ws2.Range("B2").Font.Size = 13
    $ws2.Range("B2").Font.Bold = $true
    $ws2.Range("B2").Font.Color = $cNavy

    $ws2.Range("B3:K3").Merge()
    $ws2.Range("B3").Value2 = "Dashboard de Saude do Projeto - Posicao Fechada em Setembro/2026 (Vinculado Dinamicamente)"
    $ws2.Range("B3").Font.Name = "Segoe UI"
    $ws2.Range("B3").Font.Size = 10
    $ws2.Range("B3").Font.Italic = $true
    $ws2.Range("B3").Font.Color = (Get-Color 71 85 105)

    function Setup-CardStructure($ws, $c1, $c2, $title, $sub, $headerColor) {
        $rngH = $ws.Range($c1 + "5:" + $c2 + "5")
        $rngH.Merge()
        $rngH.Value2 = $title
        $rngH.Font.Name = "Segoe UI"
        $rngH.Font.Size = 9
        $rngH.Font.Bold = $true
        $rngH.Font.Color = $cWhite
        $rngH.Interior.Color = $headerColor
        $rngH.HorizontalAlignment = -4108
        $rngH.VerticalAlignment = -4108

        $rngV = $ws.Range($c1 + "6:" + $c2 + "6")
        $rngV.Merge()
        $rngV.Font.Name = "Segoe UI"
        $rngV.Font.Size = 15
        $rngV.Font.Bold = $true
        $rngV.Font.Color = $cDark
        $rngV.Interior.Color = $cCardBg
        $rngV.HorizontalAlignment = -4108
        $rngV.VerticalAlignment = -4108

        $rngS = $ws.Range($c1 + "7:" + $c2 + "7")
        $rngS.Merge()
        $rngS.Value2 = $sub
        $rngS.Font.Name = "Segoe UI"
        $rngS.Font.Size = 8
        $rngS.Font.Italic = $true
        $rngS.Font.Color = (Get-Color 100 116 139)
        $rngS.Interior.Color = $cCardBg
        $rngS.HorizontalAlignment = -4108
        $rngS.VerticalAlignment = -4108

        $box = $ws.Range($c1 + "5:" + $c2 + "7")
        $box.Borders.Color = $cBorder
    }

    Setup-CardStructure $ws2 "B" "C" "SALDO DISPONIVEL" "Fechamento em 30/09/2026" $cDark
    Setup-CardStructure $ws2 "D" "E" "RECEITAS RECEBIDAS" "Aportes acumulados em conta" $cNavy
    Setup-CardStructure $ws2 "F" "G" "TOTAL EXECUTADO" "Execucao financeira total" (Get-Color 2 132 199)
    Setup-CardStructure $ws2 "H" "I" "RENDIMENTO FINANC." "Rendimento liquido aplicacao" $cGreen
    Setup-CardStructure $ws2 "J" "K" "SPRINTS ACOMP." "Ciclo operacional ativo" (Get-Color 71 85 105)

    # Table Header Slide 2
    $ws2.Range("B9:K9").Merge()
    $ws2.Range("B9").Value2 = "EXECUCAO ORCAMENTARIA POR RUBRICA - ORCAMENTO * EXECUTADO * DISPONIVEL"
    $ws2.Range("B9").Font.Name = "Segoe UI"
    $ws2.Range("B9").Font.Size = 10
    $ws2.Range("B9").Font.Bold = $true
    $ws2.Range("B9").Font.Color = $cWhite
    $ws2.Range("B9").Interior.Color = $cNavy
    $ws2.Range("B9").HorizontalAlignment = -4108

    $tHeaders = @(
        [PSCustomObject]@{ C1="B"; C2="C"; Txt="Rubrica Orcamentaria"; Al=-4131 },
        [PSCustomObject]@{ C1="D"; C2="E"; Txt="Orcamento (R$)"; Al=-4152 },
        [PSCustomObject]@{ C1="F"; C2="G"; Txt="Executado (R$)"; Al=-4152 },
        [PSCustomObject]@{ C1="H"; C2="I"; Txt="Disponivel (R$)"; Al=-4152 },
        [PSCustomObject]@{ C1="J"; C2="K"; Txt="Exec. %"; Al=-4108 }
    )
    foreach ($th in $tHeaders) {
        $r = $ws2.Range($th.C1 + "10:" + $th.C2 + "10")
        $r.Merge()
        $r.Value2 = $th.Txt
        $r.Font.Name = "Segoe UI"
        $r.Font.Size = 9
        $r.Font.Bold = $true
        $r.Font.Color = $cWhite
        $r.Interior.Color = $cRoyal
        $r.HorizontalAlignment = $th.Al
        $r.Borders.Color = $cBorder
    }

    # Table Rows with Formulas linked to det_execucao_orcamentaria & extrato_bancario
    # Row 11: Recursos Humanos - Bolsas P&D
    $ws2.Range("B11:C11").Merge()
    $ws2.Range("B11").Value2 = "Recursos Humanos - Bolsas P&D"
    $ws2.Range("B11").HorizontalAlignment = -4131
    $ws2.Range("D11:E11").Merge()
    $ws2.Range("D11").NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("D11").Formula = "=det_execucao_orcamentaria!B4"
    $ws2.Range("D11").HorizontalAlignment = -4152
    $ws2.Range("F11:G11").Merge()
    $ws2.Range("F11").NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("F11").Formula = "=det_execucao_orcamentaria!D4"
    $ws2.Range("F11").HorizontalAlignment = -4152
    $ws2.Range("H11:I11").Merge()
    $ws2.Range("H11").NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("H11").Formula = "=D11-F11"
    $ws2.Range("H11").HorizontalAlignment = -4152
    $ws2.Range("J11:K11").Merge()
    $ws2.Range("J11").NumberFormatLocal = "0,0%"
    $ws2.Range("J11").Formula = "=IF(D11=0,0,F11/D11)"
    $ws2.Range("J11").HorizontalAlignment = -4108

    # Row 12: Recursos Humanos Indiretos
    $ws2.Range("B12:C12").Merge()
    $ws2.Range("B12").Value2 = "Recursos Humanos Indiretos"
    $ws2.Range("B12").HorizontalAlignment = -4131
    $ws2.Range("D12:E12").Merge()
    $ws2.Range("D12").NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("D12").Formula = "=det_execucao_orcamentaria!B5"
    $ws2.Range("D12").HorizontalAlignment = -4152
    $ws2.Range("F12:G12").Merge()
    $ws2.Range("F12").NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("F12").Formula = "=det_execucao_orcamentaria!D5"
    $ws2.Range("F12").HorizontalAlignment = -4152
    $ws2.Range("H12:I12").Merge()
    $ws2.Range("H12").NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("H12").Formula = "=D12-F12"
    $ws2.Range("H12").HorizontalAlignment = -4152
    $ws2.Range("J12:K12").Merge()
    $ws2.Range("J12").NumberFormatLocal = "0,0%"
    $ws2.Range("J12").Formula = "=IF(D12=0,0,F12/D12)"
    $ws2.Range("J12").HorizontalAlignment = -4108

    # Row 13: Servicos de Terceiros PJ (Rateio Internet)
    $ws2.Range("B13:C13").Merge()
    $ws2.Range("B13").Value2 = "Servicos de Terceiros PJ (Rateio Internet)"
    $ws2.Range("B13").HorizontalAlignment = -4131
    $ws2.Range("D13:E13").Merge()
    $ws2.Range("D13").NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("D13").Formula = "=det_execucao_orcamentaria!B6+det_execucao_orcamentaria!B12"
    $ws2.Range("D13").HorizontalAlignment = -4152
    $ws2.Range("F13:G13").Merge()
    $ws2.Range("F13").NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("F13").Formula = '=-(''C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\[execucao_financeira.xlsx]extrato_bancario''!$J$15 + ''C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\[execucao_financeira.xlsx]extrato_bancario''!$J$16)'
    $ws2.Range("F13").HorizontalAlignment = -4152
    $ws2.Range("H13:I13").Merge()
    $ws2.Range("H13").NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("H13").Formula = "=D13-F13"
    $ws2.Range("H13").HorizontalAlignment = -4152
    $ws2.Range("J13:K13").Merge()
    $ws2.Range("J13").NumberFormatLocal = "0,0%"
    $ws2.Range("J13").Formula = "=IF(D13=0,0,F13/D13)"
    $ws2.Range("J13").HorizontalAlignment = -4108

    # Row 14: Tributos / ISS FAEPI
    $ws2.Range("B14:C14").Merge()
    $ws2.Range("B14").Value2 = "Tributos / ISS FAEPI"
    $ws2.Range("B14").HorizontalAlignment = -4131
    $ws2.Range("D14:E14").Merge()
    $ws2.Range("D14").NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("D14").Formula = "=det_execucao_orcamentaria!B11"
    $ws2.Range("D14").HorizontalAlignment = -4152
    $ws2.Range("F14:G14").Merge()
    $ws2.Range("F14").NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("F14").Formula = '=-(''C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\[execucao_financeira.xlsx]extrato_bancario''!$J$3 + ''C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\[execucao_financeira.xlsx]extrato_bancario''!$J$4)'
    $ws2.Range("F14").HorizontalAlignment = -4152
    $ws2.Range("H14:I14").Merge()
    $ws2.Range("H14").NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("H14").Formula = "=D14-F14"
    $ws2.Range("H14").HorizontalAlignment = -4152
    $ws2.Range("J14:K14").Merge()
    $ws2.Range("J14").NumberFormatLocal = "0,0%"
    $ws2.Range("J14").Formula = "=IF(D14=0,0,F14/D14)"
    $ws2.Range("J14").HorizontalAlignment = -4108

    # Row 15: Tarifas Bancarias (Conta SEBRAE)
    $ws2.Range("B15:C15").Merge()
    $ws2.Range("B15").Value2 = "Tarifas Bancarias (Conta SEBRAE)"
    $ws2.Range("B15").HorizontalAlignment = -4131
    $ws2.Range("D15:E15").Merge()
    $ws2.Range("D15").NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("D15").Formula = "=det_execucao_orcamentaria!B14"
    $ws2.Range("D15").HorizontalAlignment = -4152
    $ws2.Range("F15:G15").Merge()
    $ws2.Range("F15").NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("F15").Formula = '=-SUM(''C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\[execucao_financeira.xlsx]extrato_bancario''!$J$56:$J$63)'
    $ws2.Range("F15").HorizontalAlignment = -4152
    $ws2.Range("H15:I15").Merge()
    $ws2.Range("H15").NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("H15").Formula = "=D15-F15"
    $ws2.Range("H15").HorizontalAlignment = -4152
    $ws2.Range("J15:K15").Merge()
    $ws2.Range("J15").NumberFormatLocal = "0,0%"
    $ws2.Range("J15").Formula = "=IF(D15=0,0,F15/D15)"
    $ws2.Range("J15").HorizontalAlignment = -4108

    # Row 16: Despesa de Suporte Operacional (DOA)
    $ws2.Range("B16:C16").Merge()
    $ws2.Range("B16").Value2 = "Despesa de Suporte Operacional (DOA)"
    $ws2.Range("B16").HorizontalAlignment = -4131
    $ws2.Range("D16:E16").Merge()
    $ws2.Range("D16").NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("D16").Formula = "=det_execucao_orcamentaria!B9+det_execucao_orcamentaria!B10+det_execucao_orcamentaria!B13"
    $ws2.Range("D16").HorizontalAlignment = -4152
    $ws2.Range("F16:G16").Merge()
    $ws2.Range("F16").NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("F16").Formula = "=det_execucao_orcamentaria!D13"
    $ws2.Range("F16").HorizontalAlignment = -4152
    $ws2.Range("H16:I16").Merge()
    $ws2.Range("H16").NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("H16").Formula = "=D16-F16"
    $ws2.Range("H16").HorizontalAlignment = -4152
    $ws2.Range("J16:K16").Merge()
    $ws2.Range("J16").NumberFormatLocal = "0,0%"
    $ws2.Range("J16").Formula = "=IF(D16=0,0,F16/D16)"
    $ws2.Range("J16").HorizontalAlignment = -4108

    for ($rIdx = 11; $rIdx -le 16; $rIdx++) {
        $rowRng = $ws2.Range("B" + $rIdx + ":K" + $rIdx)
        $rowRng.Font.Name = "Segoe UI"
        $rowRng.Font.Size = 9
        $rowRng.Borders.Color = $cBorder
        if ($rIdx % 2 -eq 1) { $rowRng.Interior.Color = $cZebra }
    }

    # Total Row (Row 17)
    $ws2.Range("B17:C17").Merge()
    $ws2.Range("B17").Value2 = "TOTAL DO PROJETO"
    $ws2.Range("B17").HorizontalAlignment = -4131

    $ws2.Range("D17:E17").Merge()
    $ws2.Range("D17").NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("D17").Formula = "=SUM(D11:D16)"
    $ws2.Range("D17").HorizontalAlignment = -4152

    $ws2.Range("F17:G17").Merge()
    $ws2.Range("F17").NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("F17").Formula = "=SUM(F11:F16)"
    $ws2.Range("F17").HorizontalAlignment = -4152

    $ws2.Range("H17:I17").Merge()
    $ws2.Range("H17").NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("H17").Formula = "=SUM(H11:H16)"
    $ws2.Range("H17").HorizontalAlignment = -4152

    $ws2.Range("J17:K17").Merge()
    $ws2.Range("J17").NumberFormatLocal = "0,0%"
    $ws2.Range("J17").Formula = "=F17/D17"
    $ws2.Range("J17").HorizontalAlignment = -4108

    $totRng2 = $ws2.Range("B17:K17")
    $totRng2.Font.Name = "Segoe UI"
    $totRng2.Font.Size = 9
    $totRng2.Font.Bold = $true
    $totRng2.Interior.Color = $cTotal
    $totRng2.Borders.Color = $cBorder

    # Values for KPI Cards in Slide 2
    $ws2.Range("B6").NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("B6").Formula = "='Slide 3 - Desembolso e Contas'!J8"

    $ws2.Range("D6").NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("D6").Formula = "='Slide 3 - Desembolso e Contas'!E14"

    $ws2.Range("F6").NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("F6").Formula = "='Slide 2 - Saude do Projeto'!F17"

    $ws2.Range("H6").NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("H6").Formula = "='Slide 3 - Desembolso e Contas'!J14"

    $ws2.Range("J6").Value2 = "Sprints 14 e 15"

    # Row 18: Explanatory note
    $ws2.Range("B18:K18").Merge()
    $ws2.Range("B18").Formula = '="* Posicao em 30/09/2026. Aportado: R$ " & TEXT(''Slide 3 - Desembolso e Contas''!E14, "#.##0,00") & ". Rendimentos liq.: R$ " & TEXT(''Slide 3 - Desembolso e Contas''!J14, "#.##0,00") & ". Saldo em caixa: R$ " & TEXT(''Slide 3 - Desembolso e Contas''!J8, "#.##0,00") & ". Tarifas Empresa/EMBRAPII pagas c/ rendimentos."'
    $ws2.Range("B18").Font.Name = "Segoe UI"
    $ws2.Range("B18").Font.Size = 8
    $ws2.Range("B18").Font.Italic = $true
    $ws2.Range("B18").Font.Color = (Get-Color 100 116 139)


    # Slide 3 subtext (linked to Slide 2 Total)
    $ws3.Range("B15:F15").Merge()
    $ws3.Range("B15").Formula = '="Receitas recebidas: R$ " & TEXT(E14, "#.##0,00") & " (" & TEXT(E14/''Slide 2 - Saude do Projeto''!D17, "0,0%") & " do convenio). Aportes pendentes: R$ " & TEXT(''Slide 2 - Saude do Projeto''!D17-E14, "#.##0,00") & "."'
    $ws3.Range("B15").Font.Name = "Segoe UI"
    $ws3.Range("B15").Font.Size = 8
    $ws3.Range("B15").Font.Italic = $true
    $ws3.Range("B15").Font.Color = (Get-Color 100 116 139)


    # ==============================================================================
    # SLIDE 4 - ANALISE E ATENCAO
    # ==============================================================================
    $ws4.Range("B2:K2").Merge()
    $ws4.Range("B2").Value2 = "CONV. 002/2026 - ANALISE DE EXECUCAO E PONTOS DE ATENCAO (SETEMBRO/2026)"
    $ws4.Range("B2").Font.Name = "Segoe UI"
    $ws4.Range("B2").Font.Size = 13
    $ws4.Range("B2").Font.Bold = $true
    $ws4.Range("B2").Font.Color = $cNavy

    $ws4.Range("B3:K3").Merge()
    $ws4.Range("B3").Value2 = "Percentuais de Execucao por Rubrica e Destaques Gerenciais - Vinculado Dinamicamente"
    $ws4.Range("B3").Font.Name = "Segoe UI"
    $ws4.Range("B3").Font.Size = 10
    $ws4.Range("B3").Font.Italic = $true
    $ws4.Range("B3").Font.Color = (Get-Color 71 85 105)

    # Left Table: % Execucao
    $ws4.Range("B5:E5").Merge()
    $ws4.Range("B5").Value2 = "% DE EXECUCAO POR RUBRICA ORCAMENTARIA"
    $ws4.Range("B5").Font.Name = "Segoe UI"
    $ws4.Range("B5").Font.Size = 10
    $ws4.Range("B5").Font.Bold = $true
    $ws4.Range("B5").Font.Color = $cWhite
    $ws4.Range("B5").Interior.Color = $cNavy
    $ws4.Range("B5").HorizontalAlignment = -4108

    $ws4.Range("B6:D6").Merge()
    $ws4.Range("B6").Value2 = "Rubrica Orcamentaria"
    $ws4.Range("B6").Font.Name = "Segoe UI"
    $ws4.Range("B6").Font.Size = 9
    $ws4.Range("B6").Font.Bold = $true
    $ws4.Range("B6").Font.Color = $cWhite
    $ws4.Range("B6").Interior.Color = $cRoyal
    $ws4.Range("B6").HorizontalAlignment = -4131
    $ws4.Range("B6:D6").Borders.Color = $cBorder

    $ws4.Range("E6").Value2 = "% Exec."
    $ws4.Range("E6").Font.Name = "Segoe UI"
    $ws4.Range("E6").Font.Size = 9
    $ws4.Range("E6").Font.Bold = $true
    $ws4.Range("E6").Font.Color = $cWhite
    $ws4.Range("E6").Interior.Color = $cRoyal
    $ws4.Range("E6").HorizontalAlignment = -4108
    $ws4.Range("E6").Borders.Color = $cBorder

    $rubMap = @(
        [PSCustomObject]@{ Rub="Recursos Humanos Diretos (Bolsas)"; F="='Slide 2 - Saude do Projeto'!J11" },
        [PSCustomObject]@{ Rub="Recursos Humanos Indiretos"; F="='Slide 2 - Saude do Projeto'!J12" },
        [PSCustomObject]@{ Rub="Tributos / ISS FAEPI"; F="='Slide 2 - Saude do Projeto'!J14" },
        [PSCustomObject]@{ Rub="Tarifas Bancarias (SEBRAE)"; F="='Slide 2 - Saude do Projeto'!J15" },
        [PSCustomObject]@{ Rub="Servicos Terceiros PJ (Rateio)"; F="='Slide 2 - Saude do Projeto'!J13" },
        [PSCustomObject]@{ Rub="Despesa Suporte Operacional (DOA)"; F="='Slide 2 - Saude do Projeto'!J16" }
    )

    $r4 = 7
    foreach ($rm in $rubMap) {
        $ws4.Range("B" + $r4 + ":D" + $r4).Merge()
        $ws4.Range("B" + $r4).Value2 = $rm.Rub
        $ws4.Range("B" + $r4).HorizontalAlignment = -4131

        $ws4.Range("E" + $r4).NumberFormatLocal = "0,0%"
        $ws4.Range("E" + $r4).Formula = $rm.F
        $ws4.Range("E" + $r4).HorizontalAlignment = -4108
        $ws4.Range("E" + $r4).Font.Bold = $true

        $r4Rng = $ws4.Range("B" + $r4 + ":E" + $r4)
        $r4Rng.Font.Name = "Segoe UI"
        $r4Rng.Font.Size = 9
        $r4Rng.Borders.Color = $cBorder
        if ($r4 % 2 -eq 1) { $r4Rng.Interior.Color = $cZebra }
        $r4++
    }

    # Right Cards Slide 4
    # Card 1: Execucao Geral
    $ws4.Range("G5:K5").Merge()
    $ws4.Range("G5").Value2 = "EXECUCAO ACUMULADA GERAL"
    $ws4.Range("G5").Font.Name = "Segoe UI"
    $ws4.Range("G5").Font.Size = 9
    $ws4.Range("G5").Font.Bold = $true
    $ws4.Range("G5").Font.Color = $cWhite
    $ws4.Range("G5").Interior.Color = $cNavy
    $ws4.Range("G5").HorizontalAlignment = -4108

    $ws4.Range("G6:K6").Merge()
    $ws4.Range("G6").NumberFormatLocal = "0,0%"
    $ws4.Range("G6").Formula = "='Slide 2 - Saude do Projeto'!J17"
    $ws4.Range("G6").Font.Name = "Segoe UI"
    $ws4.Range("G6").Font.Size = 18
    $ws4.Range("G6").Font.Bold = $true
    $ws4.Range("G6").Font.Color = $cNavy
    $ws4.Range("G6").Interior.Color = $cCardBg
    $ws4.Range("G6").HorizontalAlignment = -4108

    $ws4.Range("G7:K7").Merge()
    $ws4.Range("G7").Formula = '="R$ " & TEXT(''Slide 2 - Saude do Projeto''!F17, "#.##0,00") & " executados de R$ " & TEXT(''Slide 2 - Saude do Projeto''!D17, "#.##0,00") & " do orcamento total"'
    $ws4.Range("G7").Font.Name = "Segoe UI"
    $ws4.Range("G7").Font.Size = 8
    $ws4.Range("G7").Font.Italic = $true
    $ws4.Range("G7").Font.Color = (Get-Color 71 85 105)
    $ws4.Range("G7").Interior.Color = $cCardBg
    $ws4.Range("G7").HorizontalAlignment = -4108
    $ws4.Range("G5:K7").Borders.Color = $cBorder

    # Card 2: Saldo em Caixa
    $ws4.Range("G9:K9").Merge()
    $ws4.Range("G9").Value2 = "SALDO FINANCEIRO DISPONIVEL"
    $ws4.Range("G9").Font.Name = "Segoe UI"
    $ws4.Range("G9").Font.Size = 9
    $ws4.Range("G9").Font.Bold = $true
    $ws4.Range("G9").Font.Color = $cWhite
    $ws4.Range("G9").Interior.Color = $cGreen
    $ws4.Range("G9").HorizontalAlignment = -4108

    $ws4.Range("G10:K10").Merge()
    $ws4.Range("G10").NumberFormatLocal = "R$ #.##0,00"
    $ws4.Range("G10").Formula = "='Slide 2 - Saude do Projeto'!B6"
    $ws4.Range("G10").Font.Name = "Segoe UI"
    $ws4.Range("G10").Font.Size = 18
    $ws4.Range("G10").Font.Bold = $true
    $ws4.Range("G10").Font.Color = $cGreen
    $ws4.Range("G10").Interior.Color = $cCardBg
    $ws4.Range("G10").HorizontalAlignment = -4108

    $ws4.Range("G11:K11").Merge()
    $ws4.Range("G11").Value2 = "Disponibilidade imediata em 30/09/2026 (3 contas)"
    $ws4.Range("G11").Font.Name = "Segoe UI"
    $ws4.Range("G11").Font.Size = 8
    $ws4.Range("G11").Font.Italic = $true
    $ws4.Range("G11").Font.Color = (Get-Color 71 85 105)
    $ws4.Range("G11").Interior.Color = $cCardBg
    $ws4.Range("G11").HorizontalAlignment = -4108
    $ws4.Range("G9:K11").Borders.Color = $cBorder

    # Card 3: Pontos de Atencao
    $ws4.Range("G13:K13").Merge()
    $ws4.Range("G13").Value2 = "PONTOS DE ATENCAO - SETEMBRO/2026"
    $ws4.Range("G13").Font.Name = "Segoe UI"
    $ws4.Range("G13").Font.Size = 9
    $ws4.Range("G13").Font.Bold = $true
    $ws4.Range("G13").Font.Color = $cWhite
    $ws4.Range("G13").Interior.Color = $cAmber
    $ws4.Range("G13").HorizontalAlignment = -4108

    $pts = @(
        "- Integralizacao SEBRAE: Aporte 100% integralizado em conta unica (R$ 150.000,00), garantindo liquidez continua.",
        "- Regularidade de Bolsas: 100% das bolsas do 1o trimestre quitadas e conciliadas com a FAEPI (34 ordens bancarias).",
        "- Proximos Aportes: Empresa Parcela 02/04 (R$ 27,5k) e EMBRAPII Parcela 02/03 (R$ 103k) previstas p/ o 4o mes.",
        "- Despesas Operacionais: Auxiliar Administrativo alocado em DSO (R$ 8,4k executados / 11,6%). Tarifas SEBRAE com R$ 858,32 de saldo."
    )
    $rPt = 14
    foreach ($p in $pts) {
        $ws4.Range("G" + $rPt + ":K" + $rPt).Merge()
        $ws4.Range("G" + $rPt).Value2 = $p
        $ws4.Range("G" + $rPt).Font.Name = "Segoe UI"
        $ws4.Range("G" + $rPt).Font.Size = 8.5
        $ws4.Range("G" + $rPt).Font.Color = $cDark
        $ws4.Range("G" + $rPt).Interior.Color = $cAmberBg
        $ws4.Range("G" + $rPt).WrapText = $true
        $ws4.Range("G" + $rPt + ":K" + $rPt).Borders.Color = $cBorder
        $ws4.Rows.Item($rPt).RowHeight = 26
        $rPt++
    }

    # Column Widths
    foreach ($w in @($ws2, $ws3, $ws4)) {
        $w.Columns.Item(1).ColumnWidth = 3
        $w.Columns.Item(2).ColumnWidth = 24
        $w.Columns.Item(3).ColumnWidth = 16
        for ($colIdx = 4; $colIdx -le 11; $colIdx++) {
            $w.Columns.Item($colIdx).ColumnWidth = 15
        }
    }

    # Recalculate all formulas
    $wb.Application.CalculateFull()
    Write-Host "Calculo de formulas concluido com sucesso!" -ForegroundColor Cyan

    # Save and Close via Excel COM
    $wb.Save()
    Write-Host "Arquivo salvo com sucesso via Microsoft Excel Oficial com formulas dinamicas!" -ForegroundColor Green
    $wb.Close($false)
} catch {
    Write-Host "Erro durante a execucao: " $_.Exception.Message " na linha: " $_.InvocationInfo.ScriptLineNumber -ForegroundColor Red
} finally {
    $excel.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
'''

with open('scratch/build_dashboards_linked.ps1', 'w', encoding='ascii') as f:
    f.write(ps_code)

print("Gerado scratch/build_dashboards_linked.ps1 atualizado!")

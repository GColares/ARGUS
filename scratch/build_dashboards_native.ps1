$ErrorActionPreference = 'Stop'

$filePath = "C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\relatorio_mensal_recursos.xlsx"
$bakPath = "C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\relatorio_mensal_recursos.xlsx.bak"

# 1. Restore from pristine backup
Copy-Item -Path $bakPath -Destination $filePath -Force
Write-Host "Restaurado do backup original com sucesso." -ForegroundColor Cyan

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

    # Remove existing custom sheets if present
    foreach ($name in @("Slide 2 - Saude do Projeto", "Slide 3 - Desembolso e Contas", "Slide 4 - Analise e Atencao")) {
        try {
            $existing = $wb.Sheets.Item($name)
            if ($existing) { $existing.Delete() }
        } catch {}
    }

    # ==============================================================================
    # SLIDE 2 - SAUDE DO PROJETO
    # ==============================================================================
    $ws2 = $wb.Sheets.Add([System.Reflection.Missing]::Value, $wb.Sheets.Item($wb.Sheets.Count))
    $ws2.Name = "Slide 2 - Saude do Projeto"

    # Title
    $ws2.Range("B2:K2").Merge()
    $ws2.Range("B2").Value2 = "POLO DE INOVACAO MANAUS - CONVENIO N 002/2026 (BIO CAROCO)"
    $ws2.Range("B2").Font.Name = "Segoe UI"
    $ws2.Range("B2").Font.Size = 13
    $ws2.Range("B2").Font.Bold = $true
    $ws2.Range("B2").Font.Color = $cNavy

    $ws2.Range("B3:K3").Merge()
    $ws2.Range("B3").Value2 = "Dashboard de Saude do Projeto - Posicao Fechada em Setembro/2026 (Pronto para Copiar e Colar no Slide 2)"
    $ws2.Range("B3").Font.Name = "Segoe UI"
    $ws2.Range("B3").Font.Size = 10
    $ws2.Range("B3").Font.Italic = $true
    $ws2.Range("B3").Font.Color = (Get-Color 71 85 105)

    function Add-KpiCard($ws, $c1, $c2, $title, $val, $sub, $headerColor) {
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
        $rngV.Value2 = $val
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

    Add-KpiCard $ws2 "B" "C" "SALDO DISPONIVEL" "R$ 137.823,81" "Fechamento em 30/09/2026" $cDark
    Add-KpiCard $ws2 "D" "E" "RECEITAS RECEBIDAS" "R$ 280.500,00" "Aportes acumulados em conta" $cNavy
    Add-KpiCard $ws2 "F" "G" "TOTAL EXECUTADO" "R$ 147.398,33" "Execucao financeira total" (Get-Color 2 132 199)
    Add-KpiCard $ws2 "H" "I" "RENDIMENTO FINANC." "R$ 4.722,14" "Rendimento liquido aplicacao" $cGreen
    Add-KpiCard $ws2 "J" "K" "SPRINTS ACOMP." "Sprints 14 e 15" "Ciclo operacional ativo" (Get-Color 71 85 105)

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

    $tRows = @(
        [PSCustomObject]@{ Rub="Recursos Humanos - Bolsas P&D"; Orc="458000"; Exe="134250"; Dsp="323750"; Pct="0.293" },
        [PSCustomObject]@{ Rub="Recursos Humanos Indiretos"; Orc="22400"; Exe="0"; Dsp="22400"; Pct="0.000" },
        [PSCustomObject]@{ Rub="Servicos de Terceiros PJ (Rateio Internet)"; Orc="8937"; Exe="257.15"; Dsp="8679.85"; Pct="0.029" },
        [PSCustomObject]@{ Rub="Tributos / ISS FAEPI"; Orc="5500"; Exe="4125"; Dsp="1375"; Pct="0.750" },
        [PSCustomObject]@{ Rub="Tarifas Bancarias (Conta SEBRAE)"; Orc="1000"; Exe="141.68"; Dsp="858.32"; Pct="0.142" },
        [PSCustomObject]@{ Rub="Despesa de Suporte Operacional (DOA)"; Orc="72263"; Exe="8400"; Dsp="63863"; Pct="0.116" }
    )

    $rowIdx = 11
    foreach ($item in $tRows) {
        $ws2.Range("B" + $rowIdx + ":C" + $rowIdx).Merge()
        $ws2.Range("B" + $rowIdx).Value2 = $item.Rub
        $ws2.Range("B" + $rowIdx).HorizontalAlignment = -4131

        $ws2.Range("D" + $rowIdx + ":E" + $rowIdx).Merge()
        $ws2.Range("D" + $rowIdx).NumberFormatLocal = "R$ #.##0,00"
        $ws2.Range("D" + $rowIdx).Value2 = $item.Orc
        $ws2.Range("D" + $rowIdx).HorizontalAlignment = -4152

        $ws2.Range("F" + $rowIdx + ":G" + $rowIdx).Merge()
        $ws2.Range("F" + $rowIdx).NumberFormatLocal = "R$ #.##0,00"
        $ws2.Range("F" + $rowIdx).Value2 = $item.Exe
        $ws2.Range("F" + $rowIdx).HorizontalAlignment = -4152

        $ws2.Range("H" + $rowIdx + ":I" + $rowIdx).Merge()
        $ws2.Range("H" + $rowIdx).NumberFormatLocal = "R$ #.##0,00"
        $ws2.Range("H" + $rowIdx).Value2 = $item.Dsp
        $ws2.Range("H" + $rowIdx).HorizontalAlignment = -4152

        $ws2.Range("J" + $rowIdx + ":K" + $rowIdx).Merge()
        $ws2.Range("J" + $rowIdx).NumberFormatLocal = "0,0%"
        $ws2.Range("J" + $rowIdx).Value2 = $item.Pct
        $ws2.Range("J" + $rowIdx).HorizontalAlignment = -4108

        $rowRng = $ws2.Range("B" + $rowIdx + ":K" + $rowIdx)
        $rowRng.Font.Name = "Segoe UI"
        $rowRng.Font.Size = 9
        $rowRng.Borders.Color = $cBorder
        if ($rowIdx % 2 -eq 1) { $rowRng.Interior.Color = $cZebra }

        $rowIdx++
    }

    # Total Row
    $ws2.Range("B" + $rowIdx + ":C" + $rowIdx).Merge()
    $ws2.Range("B" + $rowIdx).Value2 = "TOTAL DO PROJETO"
    $ws2.Range("B" + $rowIdx).HorizontalAlignment = -4131

    $ws2.Range("D" + $rowIdx + ":E" + $rowIdx).Merge()
    $ws2.Range("D" + $rowIdx).NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("D" + $rowIdx).Value2 = "568100"
    $ws2.Range("D" + $rowIdx).HorizontalAlignment = -4152

    $ws2.Range("F" + $rowIdx + ":G" + $rowIdx).Merge()
    $ws2.Range("F" + $rowIdx).NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("F" + $rowIdx).Value2 = "147173.83"
    $ws2.Range("F" + $rowIdx).HorizontalAlignment = -4152

    $ws2.Range("H" + $rowIdx + ":I" + $rowIdx).Merge()
    $ws2.Range("H" + $rowIdx).NumberFormatLocal = "R$ #.##0,00"
    $ws2.Range("H" + $rowIdx).Value2 = "420926.17"
    $ws2.Range("H" + $rowIdx).HorizontalAlignment = -4152

    $ws2.Range("J" + $rowIdx + ":K" + $rowIdx).Merge()
    $ws2.Range("J" + $rowIdx).NumberFormatLocal = "0,0%"
    $ws2.Range("J" + $rowIdx).Value2 = "0.259"
    $ws2.Range("J" + $rowIdx).HorizontalAlignment = -4108

    $totRng = $ws2.Range("B" + $rowIdx + ":K" + $rowIdx)
    $totRng.Font.Name = "Segoe UI"
    $totRng.Font.Size = 9
    $totRng.Font.Bold = $true
    $totRng.Interior.Color = $cTotal
    $totRng.Borders.Color = $cBorder

    $rowIdx++
    $ws2.Range("B" + $rowIdx + ":K" + $rowIdx).Merge()
    $ws2.Range("B" + $rowIdx).Value2 = "* Posicao em 30/09/2026. Aportado: R$ 280.500,00. Rendimentos liq.: R$ 4.722,14. Saldo em caixa: R$ 137.823,81. Tarifas Empresa/EMBRAPII (R$ 224,50) pagas c/ rendimentos."
    $ws2.Range("B" + $rowIdx).Font.Name = "Segoe UI"
    $ws2.Range("B" + $rowIdx).Font.Size = 8
    $ws2.Range("B" + $rowIdx).Font.Italic = $true
    $ws2.Range("B" + $rowIdx).Font.Color = (Get-Color 100 116 139)


    # ==============================================================================
    # SLIDE 3 - DESEMBOLSO E CONTAS
    # ==============================================================================
    $ws3 = $wb.Sheets.Add([System.Reflection.Missing]::Value, $wb.Sheets.Item($wb.Sheets.Count))
    $ws3.Name = "Slide 3 - Desembolso e Contas"

    $ws3.Range("B2:K2").Merge()
    $ws3.Range("B2").Value2 = "CONV. 002/2026 - DESEMBOLSO E EXECUCAO ORCAMENTARIA (SETEMBRO/2026)"
    $ws3.Range("B2").Font.Name = "Segoe UI"
    $ws3.Range("B2").Font.Size = 13
    $ws3.Range("B2").Font.Bold = $true
    $ws3.Range("B2").Font.Color = $cNavy

    $ws3.Range("B3:K3").Merge()
    $ws3.Range("B3").Value2 = "Contas Bancarias: 15334-6 (Empresa), 15335-4 (SEBRAE), 15338-9 (EMBRAPII) - Pronto para Copiar e Colar no Slide 3"
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

    $parcRows = @(
        [PSCustomObject]@{ Parc="01/03 EMB"; Doc="Ordem Banc."; Dt="17/06/2026"; Val="103000"; Acum="103000"; IsNum=$true },
        [PSCustomObject]@{ Parc="01/04 Emp"; Doc="NFSe 106"; Dt="01/07/2026"; Val="27500"; Acum="130500"; IsNum=$true },
        [PSCustomObject]@{ Parc="Unica SEB"; Doc="Aporte Unico"; Dt="08/07/2026"; Val="150000"; Acum="280500"; IsNum=$true },
        [PSCustomObject]@{ Parc="02/04 Emp"; Doc="-"; Dt="Prev. Out/26"; Val="27500"; Acum="pendente"; IsNum=$false },
        [PSCustomObject]@{ Parc="02/03 EMB"; Doc="-"; Dt="Prev. Out/26"; Val="103000"; Acum="pendente"; IsNum=$false },
        [PSCustomObject]@{ Parc="03/04 Emp"; Doc="-"; Dt="Prev. Dez/26"; Val="27500"; Acum="pendente"; IsNum=$false },
        [PSCustomObject]@{ Parc="03/03 EMB"; Doc="-"; Dt="Prev. Jan/27"; Val="103000"; Acum="pendente"; IsNum=$false }
    )

    $rP = 7
    foreach ($p in $parcRows) {
        $ws3.Range("B" + $rP).Value2 = $p.Parc
        $ws3.Range("C" + $rP).Value2 = $p.Doc
        $ws3.Range("D" + $rP).Value2 = $p.Dt
        
        $ws3.Range("E" + $rP).NumberFormatLocal = "R$ #.##0,00"
        $ws3.Range("E" + $rP).Value2 = $p.Val

        $ws3.Range("B" + $rP + ":D" + $rP).HorizontalAlignment = -4108
        $ws3.Range("E" + $rP).HorizontalAlignment = -4152

        if ($p.IsNum) {
            $ws3.Range("F" + $rP).NumberFormatLocal = "R$ #.##0,00"
            $ws3.Range("F" + $rP).Value2 = $p.Acum
            $ws3.Range("F" + $rP).HorizontalAlignment = -4152
        } else {
            $ws3.Range("F" + $rP).Value2 = $p.Acum
            $ws3.Range("F" + $rP).HorizontalAlignment = -4108
        }

        $rowR = $ws3.Range("B" + $rP + ":F" + $rP)
        $rowR.Font.Name = "Segoe UI"
        $rowR.Font.Size = 9
        $rowR.Borders.Color = $cBorder
        if ($rP % 2 -eq 1) { $rowR.Interior.Color = $cZebra }
        $rP++
    }

    # Total Parcelas
    $ws3.Range("B" + $rP + ":D" + $rP).Merge()
    $ws3.Range("B" + $rP).Value2 = "TOTAL RECEBIDO"
    $ws3.Range("B" + $rP).HorizontalAlignment = -4131

    $ws3.Range("E" + $rP + ":F" + $rP).Merge()
    $ws3.Range("E" + $rP).NumberFormatLocal = "R$ #.##0,00"
    $ws3.Range("E" + $rP).Value2 = "280500"
    $ws3.Range("E" + $rP).HorizontalAlignment = -4152

    $totP = $ws3.Range("B" + $rP + ":F" + $rP)
    $totP.Font.Name = "Segoe UI"
    $totP.Font.Size = 9
    $totP.Font.Bold = $true
    $totP.Interior.Color = $cTotal
    $totP.Borders.Color = $cBorder

    $rP++
    $ws3.Range("B" + $rP + ":F" + $rP).Merge()
    $ws3.Range("B" + $rP).Value2 = "Receitas recebidas: R$ 280.500,00 (49,3% do convenio). Aportes pendentes: R$ 288.500,00."
    $ws3.Range("B" + $rP).Font.Name = "Segoe UI"
    $ws3.Range("B" + $rP).Font.Size = 8
    $ws3.Range("B" + $rP).Font.Italic = $true
    $ws3.Range("B" + $rP).Font.Color = (Get-Color 100 116 139)

    # Right Box 1: Resumo Financeiro Consolidado
    $ws3.Range("H5:K5").Merge()
    $ws3.Range("H5").Value2 = "RESUMO FINANCEIRO CONSOLIDADO"
    $ws3.Range("H5").Font.Name = "Segoe UI"
    $ws3.Range("H5").Font.Size = 10
    $ws3.Range("H5").Font.Bold = $true
    $ws3.Range("H5").Font.Color = $cWhite
    $ws3.Range("H5").Interior.Color = $cNavy
    $ws3.Range("H5").HorizontalAlignment = -4108

    $resItems = @(
        [PSCustomObject]@{ Lbl="Creditos de setembro (Rend. Bruto)"; Val="332.27" },
        [PSCustomObject]@{ Lbl="Debitos de setembro (Pagamentos)"; Val="61440.33" },
        [PSCustomObject]@{ Lbl="Saldo Financeiro em 30/09"; Val="137823.81" }
    )
    $rBox1 = 6
    foreach ($ri in $resItems) {
        $ws3.Range("H" + $rBox1 + ":I" + $rBox1).Merge()
        $ws3.Range("H" + $rBox1).Value2 = $ri.Lbl
        $ws3.Range("H" + $rBox1).HorizontalAlignment = -4131

        $ws3.Range("J" + $rBox1 + ":K" + $rBox1).Merge()
        $ws3.Range("J" + $rBox1).NumberFormatLocal = "R$ #.##0,00"
        $ws3.Range("J" + $rBox1).Value2 = $ri.Val
        $ws3.Range("J" + $rBox1).HorizontalAlignment = -4152

        $rBoxRng = $ws3.Range("H" + $rBox1 + ":K" + $rBox1)
        $rBoxRng.Font.Name = "Segoe UI"
        $rBoxRng.Font.Size = 9
        $rBoxRng.Borders.Color = $cBorder
        if ($ri.Lbl -like "*Saldo*") {
            $rBoxRng.Font.Bold = $true
            $rBoxRng.Interior.Color = $cTotal
        }
        $rBox1++
    }

    # Right Box 2: Rendimentos de Aplicacao Financeira
    $rBox2 = 10
    $ws3.Range("H" + $rBox2 + ":K" + $rBox2).Merge()
    $ws3.Range("H" + $rBox2).Value2 = "RENDIMENTOS DE APLICACAO FINANCEIRA"
    $ws3.Range("H" + $rBox2).Font.Name = "Segoe UI"
    $ws3.Range("H" + $rBox2).Font.Size = 10
    $ws3.Range("H" + $rBox2).Font.Bold = $true
    $ws3.Range("H" + $rBox2).Font.Color = $cWhite
    $ws3.Range("H" + $rBox2).Interior.Color = $cGreen
    $ws3.Range("H" + $rBox2).HorizontalAlignment = -4108

    $rendItems = @(
        [PSCustomObject]@{ Lbl="Saldo inicial acumulado (Ago)"; Val="4414.24" },
        [PSCustomObject]@{ Lbl="Setembro/2026 - bruto"; Val="332.27" },
        [PSCustomObject]@{ Lbl="Setembro/2026 - IRRF retido"; Val="24.37" },
        [PSCustomObject]@{ Lbl="Acumulado Liquido (30/09)"; Val="4722.14" }
    )
    $rBox2++
    foreach ($ri in $rendItems) {
        $ws3.Range("H" + $rBox2 + ":I" + $rBox2).Merge()
        $ws3.Range("H" + $rBox2).Value2 = $ri.Lbl
        $ws3.Range("H" + $rBox2).HorizontalAlignment = -4131

        $ws3.Range("J" + $rBox2 + ":K" + $rBox2).Merge()
        $ws3.Range("J" + $rBox2).NumberFormatLocal = "R$ #.##0,00"
        $ws3.Range("J" + $rBox2).Value2 = $ri.Val
        $ws3.Range("J" + $rBox2).HorizontalAlignment = -4152

        $rBoxRng = $ws3.Range("H" + $rBox2 + ":K" + $rBox2)
        $rBoxRng.Font.Name = "Segoe UI"
        $rBoxRng.Font.Size = 9
        $rBoxRng.Borders.Color = $cBorder
        if ($ri.Lbl -like "*Acumulado*") {
            $rBoxRng.Font.Bold = $true
            $rBoxRng.Interior.Color = (Get-Color 209 250 229)
        }
        $rBox2++
    }


    # ==============================================================================
    # SLIDE 4 - ANALISE E ATENCAO
    # ==============================================================================
    $ws4 = $wb.Sheets.Add([System.Reflection.Missing]::Value, $wb.Sheets.Item($wb.Sheets.Count))
    $ws4.Name = "Slide 4 - Analise e Atencao"

    $ws4.Range("B2:K2").Merge()
    $ws4.Range("B2").Value2 = "CONV. 002/2026 - ANALISE DE EXECUCAO E PONTOS DE ATENCAO (SETEMBRO/2026)"
    $ws4.Range("B2").Font.Name = "Segoe UI"
    $ws4.Range("B2").Font.Size = 13
    $ws4.Range("B2").Font.Bold = $true
    $ws4.Range("B2").Font.Color = $cNavy

    $ws4.Range("B3:K3").Merge()
    $ws4.Range("B3").Value2 = "Percentuais de Execucao por Rubrica e Destaques Gerenciais - Pronto para Copiar e Colar no Slide 4"
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

    $rubPct = @(
        [PSCustomObject]@{ Rub="Recursos Humanos Diretos (Bolsas)"; Pct="0.293" },
        [PSCustomObject]@{ Rub="Recursos Humanos Indiretos"; Pct="0.000" },
        [PSCustomObject]@{ Rub="Tributos / ISS FAEPI"; Pct="0.750" },
        [PSCustomObject]@{ Rub="Tarifas Bancarias (SEBRAE)"; Pct="0.142" },
        [PSCustomObject]@{ Rub="Servicos Terceiros PJ (Rateio)"; Pct="0.029" },
        [PSCustomObject]@{ Rub="Despesa Suporte Operacional (DOA)"; Pct="0.116" }
    )

    $r4 = 7
    foreach ($rp in $rubPct) {
        $ws4.Range("B" + $r4 + ":D" + $r4).Merge()
        $ws4.Range("B" + $r4).Value2 = $rp.Rub
        $ws4.Range("B" + $r4).HorizontalAlignment = -4131

        $ws4.Range("E" + $r4).NumberFormatLocal = "0,0%"
        $ws4.Range("E" + $r4).Value2 = $rp.Pct
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
    $ws4.Range("G6").Value2 = "25,9%"
    $ws4.Range("G6").Font.Name = "Segoe UI"
    $ws4.Range("G6").Font.Size = 18
    $ws4.Range("G6").Font.Bold = $true
    $ws4.Range("G6").Font.Color = $cNavy
    $ws4.Range("G6").Interior.Color = $cCardBg
    $ws4.Range("G6").HorizontalAlignment = -4108

    $ws4.Range("G7:K7").Merge()
    $ws4.Range("G7").Value2 = "R$ 147.398,33 executados de R$ 568.100,00 do orcamento total"
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
    $ws4.Range("G10").Value2 = "R$ 137.823,81"
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

    # Save and Close via Excel
    $wb.Save()
    Write-Host "Arquivo salvo com sucesso via Microsoft Excel Oficial!" -ForegroundColor Green
    $wb.Close($false)
} catch {
    Write-Host "Erro durante a execucao: " $_.Exception.Message " na linha: " $_.InvocationInfo.ScriptLineNumber -ForegroundColor Red
} finally {
    $excel.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}

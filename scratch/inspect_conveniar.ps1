$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

try {
    # 1. Inspecionar execucao_financeira.xlsx
    $finFile = "C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\execucao_financeira.xlsx"
    $wb = $excel.Workbooks.Open($finFile)
    Write-Host "=== EXECUCAO_FINANCEIRA.XLSX ==="
    Write-Host ("Sheets count: " + $wb.Sheets.Count)
    foreach ($s in $wb.Sheets) {
        Write-Host (" - Sheet: " + $s.Name + ", UsedRange: " + $s.UsedRange.Address)
    }
    $wsExt = $wb.Sheets.Item("extrato_bancario")
    Write-Host "`nHeaders in extrato_bancario (Row 1):"
    $headerList = @()
    for ($c = 1; $c -le 15; $c++) {
        $val = $wsExt.Cells.Item(1, $c).Text
        if ($val) {
            $headerList += ("Col " + $c + ": '" + $val + "'")
        }
    }
    Write-Host ($headerList -join " | ")
    Write-Host ("Total rows in extrato_bancario: " + $wsExt.UsedRange.Rows.Count)

    Write-Host "`nFirst 3 data rows in extrato_bancario:"
    for ($r = 2; $r -le 4; $r++) {
        $rowVals = @()
        for ($c = 1; $c -le 10; $c++) {
            $rowVals += ("Col " + $c + ": '" + $wsExt.Cells.Item($r, $c).Text + "'")
        }
        Write-Host ("Row " + $r + " -> " + ($rowVals -join " | "))
    }

    Write-Host "`nLast 3 data rows in extrato_bancario:"
    $lastR = $wsExt.UsedRange.Rows.Count
    for ($r = ($lastR - 2); $r -le $lastR; $r++) {
        $rowVals = @()
        for ($c = 1; $c -le 10; $c++) {
            $rowVals += ("Col " + $c + ": '" + $wsExt.Cells.Item($r, $c).Text + "'")
        }
        Write-Host ("Row " + $r + " -> " + ($rowVals -join " | "))
    }
    $wb.Close($false)

    # 2. Inspecionar os 3 arquivos do Conveniar
    $convFiles = Get-ChildItem -Path "C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\dados-conveniar" -Filter "*.xlsx"
    foreach ($cf in $convFiles) {
        Write-Host "`n=== CONVENIAR FILE: $($cf.Name) ==="
        $wbConv = $excel.Workbooks.Open($cf.FullName)
        Write-Host ("Sheets count: " + $wbConv.Sheets.Count)
        $wsConv = $wbConv.Sheets.Item(1)
        Write-Host ("Sheet 1 Name: " + $wsConv.Name + ", UsedRange: " + $wsConv.UsedRange.Address)
        Write-Host ("Rows count: " + $wsConv.UsedRange.Rows.Count)

        Write-Host "Top 10 rows preview:"
        for ($r = 1; $r -le [Math]::Min(12, $wsConv.UsedRange.Rows.Count); $r++) {
            $rowVals = @()
            for ($c = 1; $c -le 12; $c++) {
                $t = $wsConv.Cells.Item($r, $c).Text
                if ($t) { $rowVals += ("Col " + $c + ": '" + $t + "'") }
            }
            if ($rowVals.Count -gt 0) {
                Write-Host ("Row " + $r + " -> " + ($rowVals -join " | "))
            }
        }
        $wbConv.Close($false)
    }

} finally {
    $excel.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}

$files = @(
    "C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\execucao_orcamentaria.xlsx",
    "C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\DISPÊNDIOS - CV_002-2026 - BIO CAROCO 2026.xlsx",
    "C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\execucao_financeira.xlsx"
)

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false

foreach ($f in $files) {
    if (Test-Path $f) {
        Write-Host "=== FILE: $(Split-Path $f -Leaf) ==="
        $wb = $excel.Workbooks.Open($f)
        foreach ($s in $wb.Sheets) {
            Write-Host ("  Sheet: " + $s.Name + " [UsedRange: " + $s.UsedRange.Address + "]")
        }
        $wb.Close($false)
    } else {
        Write-Host "File NOT FOUND: $f"
    }
}
$excel.Quit()

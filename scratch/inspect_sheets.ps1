$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$wb = $excel.Workbooks.Open('C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\relatorio_mensal_recursos.xlsx')
Write-Host "--- SHEETS ---"
foreach ($s in $wb.Sheets) { Write-Host $s.Name }
$wb.Close($false)
$excel.Quit()

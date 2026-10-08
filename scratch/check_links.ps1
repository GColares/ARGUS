$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$wb = $excel.Workbooks.Open('C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\relatorio_mensal_recursos.xlsx')
$links = $wb.LinkSources(1)
if ($links -ne $null) {
    Write-Host "External Links in Workbook:"
    foreach ($l in $links) {
        Write-Host (" - " + $l)
    }
} else {
    Write-Host "No external links detected."
}
$wb.Close($false)
$excel.Quit()

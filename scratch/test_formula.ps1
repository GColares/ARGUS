$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$wb = $excel.Workbooks.Open('C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\relatorio_mensal_recursos.xlsx')
$ws2 = $wb.Sheets.Item('Slide 2 - Saude do Projeto')

# Test assigning formula to D11
$ws2.Range("D11").Formula = "=det_execucao_orcamentaria!B4"
Write-Host "D11 Formula: " $ws2.Range("D11").Formula
Write-Host "D11 Value: " $ws2.Range("D11").Value2
Write-Host "D11 Text: " $ws2.Range("D11").Text

$wb.Close($false)
$excel.Quit()

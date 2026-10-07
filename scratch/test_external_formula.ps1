$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$wb = $excel.Workbooks.Open('C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\relatorio_mensal_recursos.xlsx')
$ws2 = $wb.Sheets.Item('Slide 2 - Saude do Projeto')

$ws2.Range("D12").Formula = "='C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\[execucao_financeira.xlsx]extrato_bancario'!J2"
Write-Host "D12 Formula: " $ws2.Range("D12").Formula
Write-Host "D12 Value: " $ws2.Range("D12").Value2
Write-Host "D12 Text: " $ws2.Range("D12").Text

$ws2.Range("D13").Formula = "=SUM('C:\Projetos\ARGUS\gestao_projetos\execucao_financeira\[execucao_financeira.xlsx]extrato_bancario'!J2:J85)"
Write-Host "D13 Formula: " $ws2.Range("D13").Formula
Write-Host "D13 Value: " $ws2.Range("D13").Value2
Write-Host "D13 Text: " $ws2.Range("D13").Text

$wb.Close($false)
$excel.Quit()

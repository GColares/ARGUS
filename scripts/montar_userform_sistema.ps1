# c:\ARGUS\scripts\montar_userform_sistema.ps1
$ErrorActionPreference = "Stop"

$xlsxPath = "C:\ARGUS\almoxarifado\inventario_legado\Almoxarifado_ARGUS_Operacional.xlsx"
$xlsmPath = "C:\ARGUS\almoxarifado\inventario_legado\Almoxarifado_ARGUS_Operacional.xlsm"
$pdfFolder = "C:\ARGUS\almoxarifado\inventario_legado\comprovantes_pdf"

if (-not (Test-Path $pdfFolder)) {
    New-Item -ItemType Directory -Path $pdfFolder -Force | Out-Null
}

$userFormCode = Get-Content -Path "C:\ARGUS\scripts\vba_userform.txt" -Raw -Encoding UTF8
$modCode = Get-Content -Path "C:\ARGUS\scripts\vba_modulo.txt" -Raw -Encoding UTF8
$wbOpenCode = Get-Content -Path "C:\ARGUS\scripts\vba_thisworkbook.txt" -Raw -Encoding UTF8

Write-Host "Iniciando Microsoft Excel COM..."
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

try {
    Write-Host "Abrindo: $xlsxPath"
    $wb = $excel.Workbooks.Open($xlsxPath)

    # 1. Configurar visual de Terminal na planilha
    $wsB = $wb.Sheets.Item("PAINEL_BALCAO")
    $excel.ActiveWindow.DisplayGridlines = $false
    $excel.ActiveWindow.DisplayHeadings = $false
    $excel.DisplayFormulaBar = $false

    # Remover componentes antigos se existirem
    foreach ($comp in $wb.VBProject.VBComponents) {
        if ($comp.Name -eq "FrmArgusBalcao" -or $comp.Name -eq "ModOperacionalAlmoxarifado") {
            $wb.VBProject.VBComponents.Remove($comp)
        }
    }

    # 2. Criar o UserForm FrmArgusBalcao
    Write-Host "Criando FrmArgusBalcao..."
    $uf = $wb.VBProject.VBComponents.Add(3) # 3 = vbext_ct_MSForm
    $uf.Name = "FrmArgusBalcao"
    $uf.Properties.Item("Caption").Value = "ARGUS - Sistema Operacional do Almoxarifado (Polo de Inovacao IFAM)"
    $uf.Properties.Item("Width").Value = 660
    $uf.Properties.Item("Height").Value = 510

    # Banner de Cabecalho
    $banner = $uf.Designer.Controls.Add("Forms.Label.1", "lblBanner")
    $banner.Top = 0
    $banner.Left = 0
    $banner.Width = 660
    $banner.Height = 44
    $banner.BackColor = 0x32510F # Verde Institucional BGR
    $banner.Caption = ""

    $lblTit = $uf.Designer.Controls.Add("Forms.Label.1", "lblTitulo")
    $lblTit.Top = 6
    $lblTit.Left = 16
    $lblTit.Width = 600
    $lblTit.Height = 18
    $lblTit.Caption = "ARGUS  |  SISTEMA DO ALMOXARIFADO & PATRIMONIO"
    $lblTit.ForeColor = 0xFFFFFF
    $lblTit.BackStyle = 0

    $lblSub = $uf.Designer.Controls.Add("Forms.Label.1", "lblSub")
    $lblSub.Top = 24
    $lblSub.Left = 16
    $lblSub.Width = 600
    $lblSub.Height = 14
    $lblSub.Caption = "Polo de Inovacao IFAM - Terminal de Atendimento Rapido de Balcao"
    $lblSub.ForeColor = 0xD1E7DD
    $lblSub.BackStyle = 0

    # MultiPage de Abas
    $mp = $uf.Designer.Controls.Add("Forms.MultiPage.1", "mpAbas")
    $mp.Top = 50
    $mp.Left = 12
    $mp.Width = 622
    $mp.Height = 390
    
    $page0 = $mp.Pages.Item(0)
    $page0.Caption = "  SAIDA DE CONSUMO  "
    
    $page1 = $mp.Pages.Item(1)
    $page1.Caption = "  NOVA CAUTELA (FERRAMENTAS/TI)  "
    
    $page2 = $mp.Pages.Add("Page3", "  DEVOLUCAO DE CAUTELA  ")
    $page3 = $mp.Pages.Add("Page4", "  CONSULTAR ESTOQUE  ")

    # Aba 0: SAIDA DE CONSUMO
    $lbl = $page0.Controls.Add("Forms.Label.1", "lblS1")
    $lbl.Top = 15; $lbl.Left = 15; $lbl.Width = 160; $lbl.Caption = "Solicitante / Responsavel:"

    $cbo = $page0.Controls.Add("Forms.ComboBox.1", "cboSolicitanteS")
    $cbo.Top = 12; $cbo.Left = 180; $cbo.Width = 400; $cbo.Height = 20

    $lbl = $page0.Controls.Add("Forms.Label.1", "lblS2")
    $lbl.Top = 45; $lbl.Left = 15; $lbl.Width = 160; $lbl.Caption = "Matricula SIAPE ou CPF:"

    $txt = $page0.Controls.Add("Forms.TextBox.1", "txtSiapeS")
    $txt.Top = 42; $txt.Left = 180; $txt.Width = 180; $txt.Height = 20

    $lbl = $page0.Controls.Add("Forms.Label.1", "lblS3")
    $lbl.Top = 75; $lbl.Left = 15; $lbl.Width = 160; $lbl.Caption = "Projeto Financiador:"

    $cbo = $page0.Controls.Add("Forms.ComboBox.1", "cboProjetoS")
    $cbo.Top = 72; $cbo.Left = 180; $cbo.Width = 400; $cbo.Height = 20

    $lbl = $page0.Controls.Add("Forms.Label.1", "lblS4")
    $lbl.Top = 105; $lbl.Left = 15; $lbl.Width = 160; $lbl.Caption = "Ambiente / Sala Destino:"

    $cbo = $page0.Controls.Add("Forms.ComboBox.1", "cboAmbienteS")
    $cbo.Top = 102; $cbo.Left = 180; $cbo.Width = 400; $cbo.Height = 20

    $lbl = $page0.Controls.Add("Forms.Label.1", "lblS5")
    $lbl.Top = 135; $lbl.Left = 15; $lbl.Width = 160; $lbl.Caption = "Item / Material a Retirar:"

    $cbo = $page0.Controls.Add("Forms.ComboBox.1", "cboItemS")
    $cbo.Top = 132; $cbo.Left = 180; $cbo.Width = 400; $cbo.Height = 20

    $lbl = $page0.Controls.Add("Forms.Label.1", "lblS6")
    $lbl.Top = 165; $lbl.Left = 15; $lbl.Width = 160; $lbl.Caption = "Quantidade:"

    $txt = $page0.Controls.Add("Forms.TextBox.1", "txtQtdS")
    $txt.Top = 162; $txt.Left = 180; $txt.Width = 80; $txt.Height = 20
    $txt.Text = "1"

    $lbl = $page0.Controls.Add("Forms.Label.1", "lblS7")
    $lbl.Top = 195; $lbl.Left = 15; $lbl.Width = 160; $lbl.Caption = "Finalidade do Uso:"

    $txt = $page0.Controls.Add("Forms.TextBox.1", "txtFinalidadeS")
    $txt.Top = 192; $txt.Left = 180; $txt.Width = 400; $txt.Height = 20
    $txt.Text = "Manutencao predial / Uso nas instalacoes"

    $btn = $page0.Controls.Add("Forms.CommandButton.1", "btnRegistrarSaida")
    $btn.Top = 240; $btn.Left = 160; $btn.Width = 300; $btn.Height = 38
    $btn.Caption = "REGISTRAR SAIDA E GERAR RECIBO"
    $btn.BackColor = 0x548719
    $btn.ForeColor = 0xFFFFFF

    # Aba 1: NOVA CAUTELA
    $lbl = $page1.Controls.Add("Forms.Label.1", "lblC1")
    $lbl.Top = 15; $lbl.Left = 15; $lbl.Width = 160; $lbl.Caption = "Solicitante / Responsavel:"

    $cbo = $page1.Controls.Add("Forms.ComboBox.1", "cboSolicitanteC")
    $cbo.Top = 12; $cbo.Left = 180; $cbo.Width = 400; $cbo.Height = 20

    $lbl = $page1.Controls.Add("Forms.Label.1", "lblC2")
    $lbl.Top = 45; $lbl.Left = 15; $lbl.Width = 160; $lbl.Caption = "Matricula SIAPE ou CPF:"

    $txt = $page1.Controls.Add("Forms.TextBox.1", "txtSiapeC")
    $txt.Top = 42; $txt.Left = 180; $txt.Width = 180; $txt.Height = 20

    $lbl = $page1.Controls.Add("Forms.Label.1", "lblC3")
    $lbl.Top = 75; $lbl.Left = 15; $lbl.Width = 160; $lbl.Caption = "Projeto Vinculado:"

    $cbo = $page1.Controls.Add("Forms.ComboBox.1", "cboProjetoC")
    $cbo.Top = 72; $cbo.Left = 180; $cbo.Width = 400; $cbo.Height = 20

    $lbl = $page1.Controls.Add("Forms.Label.1", "lblC4")
    $lbl.Top = 105; $lbl.Left = 15; $lbl.Width = 160; $lbl.Caption = "Ferramenta / Equip. TI:"

    $cbo = $page1.Controls.Add("Forms.ComboBox.1", "cboItemC")
    $cbo.Top = 102; $cbo.Left = 180; $cbo.Width = 400; $cbo.Height = 20

    $lbl = $page1.Controls.Add("Forms.Label.1", "lblC5")
    $lbl.Top = 135; $lbl.Left = 15; $lbl.Width = 160; $lbl.Caption = "N Serie / Patrimonio:"

    $txt = $page1.Controls.Add("Forms.TextBox.1", "txtSerieC")
    $txt.Top = 132; $txt.Left = 180; $txt.Width = 200; $txt.Height = 20

    $lbl = $page1.Controls.Add("Forms.Label.1", "lblC6")
    $lbl.Top = 165; $lbl.Left = 15; $lbl.Width = 160; $lbl.Caption = "Previsao de Devolucao:"

    $txt = $page1.Controls.Add("Forms.TextBox.1", "txtDataDevC")
    $txt.Top = 162; $txt.Left = 180; $txt.Width = 120; $txt.Height = 20
    $txt.Text = (Get-Date).AddDays(15).ToString("dd/MM/yyyy")

    $lbl = $page1.Controls.Add("Forms.Label.1", "lblC7")
    $lbl.Top = 195; $lbl.Left = 15; $lbl.Width = 160; $lbl.Caption = "Finalidade / Atividade:"

    $txt = $page1.Controls.Add("Forms.TextBox.1", "txtFinalidadeC")
    $txt.Top = 192; $txt.Left = 180; $txt.Width = 400; $txt.Height = 20
    $txt.Text = "Atividades de pesquisa e desenvolvimento"

    $btn = $page1.Controls.Add("Forms.CommandButton.1", "btnRegistrarCautela")
    $btn.Top = 240; $btn.Left = 160; $btn.Width = 300; $btn.Height = 38
    $btn.Caption = "REGISTRAR CAUTELA E GERAR TERMO"
    $btn.BackColor = 0xFD6E0D
    $btn.ForeColor = 0xFFFFFF

    # Aba 2: DEVOLUCAO
    $lbl = $page2.Controls.Add("Forms.Label.1", "lblD1")
    $lbl.Top = 15; $lbl.Left = 15; $lbl.Width = 350; $lbl.Caption = "Selecione a Cautela em Aberto (EM USO):"

    $cbo = $page2.Controls.Add("Forms.ComboBox.1", "cboCautelasAbertas")
    $cbo.Top = 38; $cbo.Left = 15; $cbo.Width = 570; $cbo.Height = 22

    $lbl = $page2.Controls.Add("Forms.Label.1", "lblD2")
    $lbl.Top = 75; $lbl.Left = 15; $lbl.Width = 350; $lbl.Caption = "Condicao Fisica do Material no Retorno:"

    $opt1 = $page2.Controls.Add("Forms.OptionButton.1", "optSemAvaria")
    $opt1.Top = 98; $opt1.Left = 25; $opt1.Width = 240; $opt1.Caption = "Perfeito Estado (Sem Avarias)"
    $opt1.Value = $true

    $opt2 = $page2.Controls.Add("Forms.OptionButton.1", "optComAvaria")
    $opt2.Top = 98; $opt2.Left = 290; $opt2.Width = 240; $opt2.Caption = "Com Avaria / Falhas"

    $lbl = $page2.Controls.Add("Forms.Label.1", "lblD3")
    $lbl.Top = 135; $lbl.Left = 15; $lbl.Width = 350; $lbl.Caption = "Observacoes da Vistoria:"

    $txt = $page2.Controls.Add("Forms.TextBox.1", "txtObsDevolucao")
    $txt.Top = 155; $txt.Left = 15; $txt.Width = 570; $txt.Height = 55
    $txt.MultiLine = $true

    $btn = $page2.Controls.Add("Forms.CommandButton.1", "btnConfirmarDevolucao")
    $btn.Top = 230; $btn.Left = 160; $btn.Width = 300; $btn.Height = 38
    $btn.Caption = "CONFIRMAR RETORNO / BAIXA"
    $btn.BackColor = 0x548719
    $btn.ForeColor = 0xFFFFFF

    # Aba 3: CONSULTAR ESTOQUE
    $lbl = $page3.Controls.Add("Forms.Label.1", "lblE1")
    $lbl.Top = 15; $lbl.Left = 15; $lbl.Width = 140; $lbl.Caption = "Buscar Material:"

    $txt = $page3.Controls.Add("Forms.TextBox.1", "txtBuscaEstoque")
    $txt.Top = 12; $txt.Left = 160; $txt.Width = 280; $txt.Height = 20

    $lbl = $page3.Controls.Add("Forms.Label.1", "lblEInfo")
    $lbl.Top = 38; $lbl.Left = 15; $lbl.Width = 570; $lbl.Caption = "Codigo | Descricao do Material | Categoria | Saldo Atual | Status"
    $lbl.ForeColor = 0x6C757D

    $lst = $page3.Controls.Add("Forms.ListBox.1", "lstEstoque")
    $lst.Top = 55; $lst.Left = 15; $lst.Width = 585; $lst.Height = 240
    $lst.ColumnCount = 5

    # Rodape do Formulario
    $btn = $uf.Designer.Controls.Add("Forms.CommandButton.1", "btnAbrirPasta")
    $btn.Top = 448; $btn.Left = 14; $btn.Width = 230; $btn.Height = 28
    $btn.Caption = "ABRIR COMPROVANTES (PDF)"
    $btn.BackColor = 0x4B5563
    $btn.ForeColor = 0xFFFFFF

    $btn = $uf.Designer.Controls.Add("Forms.CommandButton.1", "btnFechar")
    $btn.Top = 448; $btn.Left = 524; $btn.Width = 110; $btn.Height = 28
    $btn.Caption = "FECHAR"
    $btn.BackColor = 0x212529
    $btn.ForeColor = 0xFFFFFF

    # 3. Injetar Codigo no UserForm
    Write-Host "Injetando codigo do UserForm..."
    $uf.CodeModule.AddFromString($userFormCode)

    # 4. Injetar Modulo Padrao
    Write-Host "Injetando ModOperacionalAlmoxarifado..."
    $mod = $wb.VBProject.VBComponents.Add(1)
    $mod.Name = "ModOperacionalAlmoxarifado"
    $mod.CodeModule.AddFromString($modCode)

    # 5. Configurar ThisWorkbook
    Write-Host "Injetando Workbook_Open..."
    $thisWb = $wb.VBProject.VBComponents.Item("EstaPastaDeTrabalho")
    if ($null -eq $thisWb) {
        $thisWb = $wb.VBProject.VBComponents.Item("ThisWorkbook")
    }
    $thisWb.CodeModule.AddFromString($wbOpenCode)

    # 6. Botao Mestre de Terminal no PAINEL_BALCAO
    Write-Host "Configurando botao mestre do sistema na planilha..."
    $wsB.Shapes | ForEach-Object { $_.Delete() }
    
    $btnMestre = $wsB.Shapes.AddShape(1, 160, 310, 360, 56)
    $btnMestre.TextFrame.Characters().Text = "CLIQUE AQUI PARA ABRIR O SISTEMA DE BALCAO"
    $btnMestre.TextFrame.Characters().Font.Bold = $true
    $btnMestre.TextFrame.Characters().Font.Size = 11
    $btnMestre.TextFrame.Characters().Font.Color = 0xFFFFFF
    $btnMestre.Fill.ForeColor.RGB = 0x548719
    $btnMestre.Line.Visible = $false
    $btnMestre.OnAction = "AbrirSistemaAlmoxarifado"

    Write-Host "Salvando pasta de trabalho macro-enabled (.xlsm): $xlsmPath"
    $wb.SaveAs($xlsmPath, 52)
    $wb.Close($false)
    Write-Host "SISTEMA DESKTOP GERADO COM SUCESSO ABSOLUTO!"
}
finally {
    $excel.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}

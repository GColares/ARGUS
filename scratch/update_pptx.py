import shutil
import zipfile
import os
import xml.etree.ElementTree as ET

# Paths
base_dir = r"c:\Projetos\ARGUS\gestao_projetos\execucao_financeira"
target_pptx = os.path.join(base_dir, "2026-09_Acompanhamento_Conv002_2026_BioCaroco_Setembro_2026-teste.pptx")
pristine_pptx = os.path.join(base_dir, "2026-09_Acompanhamento_Conv002_2026_BioCaroco_Setembro_2026.pptx")

NS = {
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
}
ET.register_namespace('p', NS['p'])
ET.register_namespace('a', NS['a'])

def set_shape_text(sp, new_text):
    txBody = sp.find('p:txBody', NS)
    if txBody is None:
        return
    paragraphs = txBody.findall('a:p', NS)
    if not paragraphs:
        return
    first_p = paragraphs[0]
    
    runs = first_p.findall('a:r', NS)
    if runs:
        first_r = runs[0]
        t = first_r.find('a:t', NS)
        if t is None:
            t = ET.SubElement(first_r, f"{{{NS['a']}}}t")
        t.text = new_text
        for r in runs[1:]:
            first_p.remove(r)
    else:
        r = ET.SubElement(first_p, f"{{{NS['a']}}}r")
        t = ET.SubElement(r, f"{{{NS['a']}}}t")
        t.text = new_text
        
    for p in paragraphs[1:]:
        txBody.remove(p)

def set_shape_width(sp, new_cx):
    xfrm = sp.find('.//p:spPr/a:xfrm', NS)
    if xfrm is not None:
        ext = xfrm.find('a:ext', NS)
        if ext is not None:
            ext.set('cx', str(new_cx))

def update_slide1(xml_content):
    root = ET.fromstring(xml_content)
    shapes_by_id = {sp.find('.//p:nvSpPr/p:cNvPr', NS).get('id'): sp for sp in root.findall('.//p:sp', NS) if sp.find('.//p:nvSpPr/p:cNvPr', NS) is not None}

    if '188' in shapes_by_id: set_shape_text(shapes_by_id['188'], "Polo de Inovação Manaus")
    if '189' in shapes_by_id: set_shape_text(shapes_by_id['189'], "Conv. 002/2026 – Bio Caroço")
    if '190' in shapes_by_id: set_shape_text(shapes_by_id['190'], "Prazo de Execução: Jun/2026 a Fev/2027 (9 meses)")
    if '191' in shapes_by_id: set_shape_text(shapes_by_id['191'], "SETEMBRO / 2026")
        
    return ET.tostring(root, encoding='utf-8')

def update_slide2(xml_content):
    root = ET.fromstring(xml_content)
    shapes_by_id = {sp.find('.//p:nvSpPr/p:cNvPr', NS).get('id'): sp for sp in root.findall('.//p:sp', NS) if sp.find('.//p:nvSpPr/p:cNvPr', NS) is not None}

    # Headers
    if '197' in shapes_by_id: set_shape_text(shapes_by_id['197'], "GESTÃO FINANCEIRA")
    if '198' in shapes_by_id: set_shape_text(shapes_by_id['198'], "Dashboard de Saúde do Projeto")
    if '200' in shapes_by_id: set_shape_text(shapes_by_id['200'], "Período: Setembro / 2026")

    # Cards
    if '202' in shapes_by_id: set_shape_text(shapes_by_id['202'], "SALDO DISPONÍVEL")
    if '203' in shapes_by_id: set_shape_text(shapes_by_id['203'], "R$ 137.823,81")
    if '204' in shapes_by_id: set_shape_text(shapes_by_id['204'], "Fechamento em 30/09")

    if '206' in shapes_by_id: set_shape_text(shapes_by_id['206'], "RECEITAS RECEBIDAS")
    if '207' in shapes_by_id: set_shape_text(shapes_by_id['207'], "R$ 280.500,00")
    if '208' in shapes_by_id: set_shape_text(shapes_by_id['208'], "Receitas acumuladas")

    if '210' in shapes_by_id: set_shape_text(shapes_by_id['210'], "TOTAL EXECUTADO")
    if '211' in shapes_by_id: set_shape_text(shapes_by_id['211'], "R$ 147.398,33")
    if '212' in shapes_by_id: set_shape_text(shapes_by_id['212'], "Execução acumulada")

    if '214' in shapes_by_id: set_shape_text(shapes_by_id['214'], "RENDIMENTO FINANC.")
    if '215' in shapes_by_id: set_shape_text(shapes_by_id['215'], "R$ 4.722,14")
    if '216' in shapes_by_id: set_shape_text(shapes_by_id['216'], "Rendimento acumulado")

    if '218' in shapes_by_id: set_shape_text(shapes_by_id['218'], "SPRINTS ACOMP.")
    if '219' in shapes_by_id: set_shape_text(shapes_by_id['219'], "2")
    if '220' in shapes_by_id: set_shape_text(shapes_by_id['220'], "Sprints 14 e 15")

    # Table Header
    if '221' in shapes_by_id:
        set_shape_text(shapes_by_id['221'], "Execução Orçamentária por Rubrica – Orçamento • Executado • Disponível")

    # Row 1: RH Direto
    if '229' in shapes_by_id: set_shape_text(shapes_by_id['229'], "Recursos Humanos – Bolsas P&D")
    if '230' in shapes_by_id: set_shape_text(shapes_by_id['230'], "458.000,00")
    if '231' in shapes_by_id: set_shape_text(shapes_by_id['231'], "134.250,00")
    if '232' in shapes_by_id: set_shape_text(shapes_by_id['232'], "323.750,00")
    if '233' in shapes_by_id: set_shape_text(shapes_by_id['233'], "29,3%")

    # Row 2: RH Indireto (Sem o auxiliar administrativo -> 0,00)
    if '236' in shapes_by_id: set_shape_text(shapes_by_id['236'], "Recursos Humanos Indiretos")
    if '237' in shapes_by_id: set_shape_text(shapes_by_id['237'], "22.400,00")
    if '238' in shapes_by_id: set_shape_text(shapes_by_id['238'], "0,00")
    if '239' in shapes_by_id: set_shape_text(shapes_by_id['239'], "22.400,00")
    if '240' in shapes_by_id: set_shape_text(shapes_by_id['240'], "0,0%")

    # Row 3: Serviços Terceiros PJ
    if '242' in shapes_by_id: set_shape_text(shapes_by_id['242'], "Serviços de Terceiros PJ (Rateio Internet)")
    if '243' in shapes_by_id: set_shape_text(shapes_by_id['243'], "8.937,00")
    if '244' in shapes_by_id: set_shape_text(shapes_by_id['244'], "257,15")
    if '245' in shapes_by_id: set_shape_text(shapes_by_id['245'], "8.679,85")
    if '246' in shapes_by_id: set_shape_text(shapes_by_id['246'], "2,9%")

    # Row 4: Tributos / ISS
    if '249' in shapes_by_id: set_shape_text(shapes_by_id['249'], "Tributos / ISS FAEPI")
    if '250' in shapes_by_id: set_shape_text(shapes_by_id['250'], "5.500,00")
    if '251' in shapes_by_id: set_shape_text(shapes_by_id['251'], "4.125,00")
    if '252' in shapes_by_id: set_shape_text(shapes_by_id['252'], "1.375,00")
    if '253' in shapes_by_id: set_shape_text(shapes_by_id['253'], "75,0%")

    # Row 5: Tarifas Bancárias (Dotação exclusiva da Conta SEBRAE no PT)
    if '255' in shapes_by_id: set_shape_text(shapes_by_id['255'], "Tarifas Bancárias (Conta SEBRAE)")
    if '256' in shapes_by_id: set_shape_text(shapes_by_id['256'], "1.000,00")
    if '257' in shapes_by_id: set_shape_text(shapes_by_id['257'], "141,68")
    if '258' in shapes_by_id: set_shape_text(shapes_by_id['258'], "858,32")
    if '259' in shapes_by_id: set_shape_text(shapes_by_id['259'], "14,2%")

    # Row 6: Despesa de Suporte Operacional (DOA) - Absorve os R$ 8.400,00 do Aux. Administrativo
    if '262' in shapes_by_id: set_shape_text(shapes_by_id['262'], "Despesa de Suporte Operacional (DOA)")
    if '263' in shapes_by_id: set_shape_text(shapes_by_id['263'], "72.263,00")
    if '264' in shapes_by_id: set_shape_text(shapes_by_id['264'], "8.400,00")
    if '265' in shapes_by_id: set_shape_text(shapes_by_id['265'], "63.863,00")
    if '266' in shapes_by_id: set_shape_text(shapes_by_id['266'], "11,6%")

    # Row 7: Linha vazia
    if '268' in shapes_by_id: set_shape_text(shapes_by_id['268'], "—")
    if '269' in shapes_by_id: set_shape_text(shapes_by_id['269'], "—")
    if '270' in shapes_by_id: set_shape_text(shapes_by_id['270'], "—")
    if '271' in shapes_by_id: set_shape_text(shapes_by_id['271'], "—")
    if '272' in shapes_by_id: set_shape_text(shapes_by_id['272'], "—")

    # Total Row
    if '275' in shapes_by_id: set_shape_text(shapes_by_id['275'], "TOTAL DO PROJETO")
    if '276' in shapes_by_id: set_shape_text(shapes_by_id['276'], "568.100,00")
    if '277' in shapes_by_id: set_shape_text(shapes_by_id['277'], "147.173,83")
    if '278' in shapes_by_id: set_shape_text(shapes_by_id['278'], "420.926,17")
    if '279' in shapes_by_id: set_shape_text(shapes_by_id['279'], "25,9%")

    # Footnote
    if '280' in shapes_by_id:
        set_shape_text(shapes_by_id['280'], "* Posição em 30/09/2026. Aporte: R$ 280.500,00. Rendimentos líq.: R$ 4.722,14. Saldo em caixa: R$ 137.823,81. Tarifas Empresa/EMBRAPII (R$ 224,50) pagas c/ rendimentos.")

    return ET.tostring(root, encoding='utf-8')

def update_slide3(xml_content):
    root = ET.fromstring(xml_content)
    shapes_by_id = {sp.find('.//p:nvSpPr/p:cNvPr', NS).get('id'): sp for sp in root.findall('.//p:sp', NS) if sp.find('.//p:nvSpPr/p:cNvPr', NS) is not None}

    # Headers
    if '286' in shapes_by_id: set_shape_text(shapes_by_id['286'], "5. GESTÃO FINANCEIRA")
    if '287' in shapes_by_id: set_shape_text(shapes_by_id['287'], "Desembolso e Execução Orçamentária – Setembro")
    if '288' in shapes_by_id: set_shape_text(shapes_by_id['288'], "Conv. 002/2026 – Contas: 15334-6 (Empresa), 15335-4 (SEBRAE), 15338-9 (EMBRAPII)")
    if '289' in shapes_by_id: set_shape_text(shapes_by_id['289'], "Parcelas Recebidas (Entradas de Receita)")

    # Table Left (Parcelas)
    if '291' in shapes_by_id: set_shape_text(shapes_by_id['291'], "Parcela")
    if '292' in shapes_by_id: set_shape_text(shapes_by_id['292'], "Nº Doc.")
    if '293' in shapes_by_id: set_shape_text(shapes_by_id['293'], "Data Pagto")
    if '294' in shapes_by_id: set_shape_text(shapes_by_id['294'], "Valor (R$)")
    if '295' in shapes_by_id: set_shape_text(shapes_by_id['295'], "Acumulado (R$)")

    # Row 1: EMBRAPII 01/03
    if '297' in shapes_by_id: set_shape_text(shapes_by_id['297'], "01/03 EMB")
    if '298' in shapes_by_id: set_shape_text(shapes_by_id['298'], "Ordem Banc.")
    if '299' in shapes_by_id: set_shape_text(shapes_by_id['299'], "17/06/2026")
    if '300' in shapes_by_id: set_shape_text(shapes_by_id['300'], "103.000,00")
    if '301' in shapes_by_id: set_shape_text(shapes_by_id['301'], "103.000,00")

    # Row 2: LC Frutas 01/04
    if '304' in shapes_by_id: set_shape_text(shapes_by_id['304'], "01/04 Emp")
    if '305' in shapes_by_id: set_shape_text(shapes_by_id['305'], "NFSe 106")
    if '306' in shapes_by_id: set_shape_text(shapes_by_id['306'], "01/07/2026")
    if '307' in shapes_by_id: set_shape_text(shapes_by_id['307'], "27.500,00")
    if '308' in shapes_by_id: set_shape_text(shapes_by_id['308'], "130.500,00")

    # Row 3: SEBRAE Única
    if '310' in shapes_by_id: set_shape_text(shapes_by_id['310'], "Única SEB")
    if '311' in shapes_by_id: set_shape_text(shapes_by_id['311'], "Aporte Único")
    if '312' in shapes_by_id: set_shape_text(shapes_by_id['312'], "08/07/2026")
    if '313' in shapes_by_id: set_shape_text(shapes_by_id['313'], "150.000,00")
    if '314' in shapes_by_id: set_shape_text(shapes_by_id['314'], "280.500,00")

    # Row 4: LC Frutas 02/04
    if '317' in shapes_by_id: set_shape_text(shapes_by_id['317'], "02/04 Emp")
    if '318' in shapes_by_id: set_shape_text(shapes_by_id['318'], "—")
    if '319' in shapes_by_id: set_shape_text(shapes_by_id['319'], "Prev. Out/26")
    if '320' in shapes_by_id: set_shape_text(shapes_by_id['320'], "27.500,00")
    if '321' in shapes_by_id: set_shape_text(shapes_by_id['321'], "pendente")

    # Row 5: EMBRAPII 02/03
    if '323' in shapes_by_id: set_shape_text(shapes_by_id['323'], "02/03 EMB")
    if '324' in shapes_by_id: set_shape_text(shapes_by_id['324'], "—")
    if '325' in shapes_by_id: set_shape_text(shapes_by_id['325'], "Prev. Out/26")
    if '326' in shapes_by_id: set_shape_text(shapes_by_id['326'], "103.000,00")
    if '327' in shapes_by_id: set_shape_text(shapes_by_id['327'], "pendente")

    # Row 6: LC Frutas 03/04
    if '330' in shapes_by_id: set_shape_text(shapes_by_id['330'], "03/04 Emp")
    if '331' in shapes_by_id: set_shape_text(shapes_by_id['331'], "—")
    if '332' in shapes_by_id: set_shape_text(shapes_by_id['332'], "Prev. Dez/26")
    if '333' in shapes_by_id: set_shape_text(shapes_by_id['333'], "27.500,00")
    if '334' in shapes_by_id: set_shape_text(shapes_by_id['334'], "pendente")

    # Row 7: EMBRAPII 03/03
    if '336' in shapes_by_id: set_shape_text(shapes_by_id['336'], "03/03 EMB")
    if '337' in shapes_by_id: set_shape_text(shapes_by_id['337'], "—")
    if '338' in shapes_by_id: set_shape_text(shapes_by_id['338'], "Prev. Jan/27")
    if '339' in shapes_by_id: set_shape_text(shapes_by_id['339'], "103.000,00")
    if '340' in shapes_by_id: set_shape_text(shapes_by_id['340'], "pendente")

    # Total Row
    if '343' in shapes_by_id: set_shape_text(shapes_by_id['343'], "TOTAL RECEBIDO")
    if '344' in shapes_by_id: set_shape_text(shapes_by_id['344'], "280.500,00")
    if '345' in shapes_by_id:
        set_shape_text(shapes_by_id['345'], "Receitas recebidas: R$ 280.500,00 (49,3% do convênio). Aportes pendentes: R$ 288.500,00.")

    # Right Box 1: Resumo Financeiro
    if '347' in shapes_by_id: set_shape_text(shapes_by_id['347'], "Resumo Financeiro Consolidado")
    if '349' in shapes_by_id: set_shape_text(shapes_by_id['349'], "Créditos de setembro")
    if '350' in shapes_by_id: set_shape_text(shapes_by_id['350'], "R$ 332,27")
    if '352' in shapes_by_id: set_shape_text(shapes_by_id['352'], "Débitos de setembro")
    if '353' in shapes_by_id: set_shape_text(shapes_by_id['353'], "R$ 61.440,33")
    if '354' in shapes_by_id: set_shape_text(shapes_by_id['354'], "Saldo em 30/09")
    if '355' in shapes_by_id: set_shape_text(shapes_by_id['355'], "R$ 137.823,81")

    # Right Box 2: Rendimentos de Aplicação
    if '357' in shapes_by_id: set_shape_text(shapes_by_id['357'], "Rendimentos de Aplicação Financeira")
    if '359' in shapes_by_id: set_shape_text(shapes_by_id['359'], "Saldo inicial acumulado (Ago)")
    if '360' in shapes_by_id: set_shape_text(shapes_by_id['360'], "R$ 4.414,24")
    if '362' in shapes_by_id: set_shape_text(shapes_by_id['362'], "Setembro/2026 – bruto")
    if '363' in shapes_by_id: set_shape_text(shapes_by_id['363'], "R$ 332,27")
    if '365' in shapes_by_id: set_shape_text(shapes_by_id['365'], "Setembro/2026 – IRRF")
    if '366' in shapes_by_id: set_shape_text(shapes_by_id['366'], "R$ 24,37")
    if '367' in shapes_by_id: set_shape_text(shapes_by_id['367'], "Acumulado Líquido")
    if '368' in shapes_by_id: set_shape_text(shapes_by_id['368'], "R$ 4.722,14")

    return ET.tostring(root, encoding='utf-8')

def update_slide4(xml_content):
    root = ET.fromstring(xml_content)
    shapes_by_id = {sp.find('.//p:nvSpPr/p:cNvPr', NS).get('id'): sp for sp in root.findall('.//p:sp', NS) if sp.find('.//p:nvSpPr/p:cNvPr', NS) is not None}

    # Headers
    if '374' in shapes_by_id: set_shape_text(shapes_by_id['374'], "5. GESTÃO FINANCEIRA")
    if '375' in shapes_by_id: set_shape_text(shapes_by_id['375'], "Análise de Execução e Pontos de Atenção")
    if '376' in shapes_by_id: set_shape_text(shapes_by_id['376'], "% de Execução por Rubrica Orçamentária")

    MAX_BAR_CX = 4529698

    # Row 1: RH Direto (29,31%)
    if '377' in shapes_by_id: set_shape_text(shapes_by_id['377'], "Recursos Humanos Diretos (Bolsas)")
    if '378' in shapes_by_id: set_shape_text(shapes_by_id['378'], "29,3%")
    if '380' in shapes_by_id: set_shape_width(shapes_by_id['380'], int(MAX_BAR_CX * 0.2931))

    # Row 2: RH Indireto (0,0%)
    if '381' in shapes_by_id: set_shape_text(shapes_by_id['381'], "Recursos Humanos Indiretos")
    if '382' in shapes_by_id: set_shape_text(shapes_by_id['382'], "0,0%")
    if '384' in shapes_by_id: set_shape_width(shapes_by_id['384'], 90589)

    # Row 3: Tributos / ISS FAEPI (75,00%)
    if '385' in shapes_by_id: set_shape_text(shapes_by_id['385'], "Tributos / ISS FAEPI")
    if '386' in shapes_by_id: set_shape_text(shapes_by_id['386'], "75,0%")
    if '388' in shapes_by_id: set_shape_width(shapes_by_id['388'], int(MAX_BAR_CX * 0.7500))

    # Row 4: Tarifas Bancárias (14,17% - Conta SEBRAE)
    if '389' in shapes_by_id: set_shape_text(shapes_by_id['389'], "Tarifas Bancárias (SEBRAE)")
    if '390' in shapes_by_id: set_shape_text(shapes_by_id['390'], "14,2%")
    if '392' in shapes_by_id: set_shape_width(shapes_by_id['392'], int(MAX_BAR_CX * 0.1417))

    # Row 5: Serviços Terceiros PJ (2,88%)
    if '393' in shapes_by_id: set_shape_text(shapes_by_id['393'], "Serviços Terceiros PJ (Rateio)")
    if '394' in shapes_by_id: set_shape_text(shapes_by_id['394'], "2,9%")
    if '396' in shapes_by_id: set_shape_width(shapes_by_id['396'], int(MAX_BAR_CX * 0.0288))

    # Row 6: Despesa de Suporte Operacional (DOA) (11,62%)
    if '397' in shapes_by_id: set_shape_text(shapes_by_id['397'], "Despesa de Suporte Operacional (DOA)")
    if '398' in shapes_by_id: set_shape_text(shapes_by_id['398'], "11,6%")
    if '400' in shapes_by_id: set_shape_width(shapes_by_id['400'], int(MAX_BAR_CX * 0.1162))

    # Right Cards
    if '402' in shapes_by_id: set_shape_text(shapes_by_id['402'], "25,9%")
    if '403' in shapes_by_id: set_shape_text(shapes_by_id['403'], "Execução acumulada – R$ 147.398,33 do orçamento total")
    if '405' in shapes_by_id: set_shape_text(shapes_by_id['405'], "R$ 137.823,81")
    if '406' in shapes_by_id: set_shape_text(shapes_by_id['406'], "Saldo financeiro em 30/09")
    if '408' in shapes_by_id: set_shape_text(shapes_by_id['408'], "PONTOS DE ATENÇÃO")
    if '409' in shapes_by_id:
        set_shape_text(shapes_by_id['409'], "Aporte SEBRAE 100% integralizado em conta única (R$ 150.000,00). 100% das bolsas do 1º trimestre quitadas e conciliadas com a FAEPI (34 ordens bancárias). Próximas parcelas previstas para o 4º mês: Empresa Parcela 02/04 (R$ 27,5k) e EMBRAPII Parcela 02/03 (R$ 103k).")

    return ET.tostring(root, encoding='utf-8')

# Now process the archive
temp_zip = target_pptx + ".tmp.zip"

with zipfile.ZipFile(pristine_pptx, 'r') as src_zip, zipfile.ZipFile(temp_zip, 'w', compression=zipfile.ZIP_DEFLATED) as dst_zip:
    for item in src_zip.infolist():
        data = src_zip.read(item.filename)
        if item.filename == 'ppt/slides/slide1.xml':
            data = update_slide1(data)
            print("Updated slide 1")
        elif item.filename == 'ppt/slides/slide2.xml':
            data = update_slide2(data)
            print("Updated slide 2")
        elif item.filename == 'ppt/slides/slide3.xml':
            data = update_slide3(data)
            print("Updated slide 3")
        elif item.filename == 'ppt/slides/slide4.xml':
            data = update_slide4(data)
            print("Updated slide 4")
        dst_zip.writestr(item, data)

try:
    if os.path.exists(target_pptx):
        os.remove(target_pptx)
    os.rename(temp_zip, target_pptx)
    print(f"Successfully re-generated updated PPTX: {target_pptx}")
except PermissionError:
    alt_target = os.path.join(base_dir, "2026-09_Acompanhamento_Conv002_2026_BioCaroco_Setembro_2026-teste-v2.pptx")
    if os.path.exists(alt_target):
        os.remove(alt_target)
    os.rename(temp_zip, alt_target)
    print(f"Arquivo principal aberto no PowerPoint. Nova versão salva com sucesso em: {alt_target}")

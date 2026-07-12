# almoxarifado/services.py

import re
import time
import json
from cadastros.models import Fornecedor
from decimal import Decimal
# pyrefly: ignore [missing-import]
from google import genai
# pyrefly: ignore [missing-import]
from google.genai import types
# pyrefly: ignore [missing-import]
from django.conf import settings
# pyrefly: ignore [missing-import]
from django.utils import timezone
# pyrefly: ignore [missing-import]
from django.db.models import F
from .models import CotaDiariaIA, NotaFiscalAlmoxarifado, ProdutoAlmoxarifado, Imposto, ImpostoNota


def _limpar_valor_ia(valor_bruto):
    """
    Filtro Sanitizador: Intercepta o dado bruto retornado pela IA (texto, float, int)
    e converte para um formato Decimal seguro para o ORM do Django.
    Corrige formatações brasileiras (ex: 1.500,50) para o padrão de banco de dados (1500.50).
    """
    if not valor_bruto:
        return Decimal('0.00')
        
    if isinstance(valor_bruto, (int, float)):
        return Decimal(str(valor_bruto))
        
    # É string. Remove letras, espaços e símbolos de moeda
    texto = str(valor_bruto).upper().replace('R$', '').replace(' ', '').strip()
    
    # Trata a pontuação
    if '.' in texto and ',' in texto:
        texto = texto.replace('.', '')  # Remove o separador de milhar
        texto = texto.replace(',', '.') # Transforma a vírgula dos centavos em ponto decimal
    elif ',' in texto:
        texto = texto.replace(',', '.')
        
    try:
        return Decimal(texto)
    except:
        return Decimal('0.00')


def _extrair_nfe_json_gemini(caminho_pdf):
    """
    Comunica-se com a API do Google Gemini para extrair os dados da NF-e estruturados em JSON.
    Controla o rate limit (Erro 429) e gerencia as cotas diárias da instituição.
    """
    cota_hoje, _ = CotaDiariaIA.objects.get_or_create(data=timezone.now().date())
    
    if cota_hoje.limite_diario > 0 and cota_hoje.requisicoes_feitas >= cota_hoje.limite_diario:
        raise Exception("Cota diária de IA excedida. Tente novamente amanhã ou atualize o plano.")

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    arquivo_ia = None
    
    try:
        arquivo_ia = client.files.upload(file=caminho_pdf)
            
        prompt = """
        Você é um auditor de logística do Almoxarifado do IFAM. Leia o PDF da Nota Fiscal (NF-e) em anexo.
        Sua tarefa é extrair os dados e formatá-los ESTRITAMENTE num JSON com duas chaves principais: "cabecalho" e "produtos".
        
        REGRA DE EXTRAÇÃO DE IMPOSTOS E FRETE:
        Procure no quadro de cálculo do imposto e nas informações complementares os valores dos impostos incidentes (ICMS, IPI, PIS, COFINS, etc.) e o valor do frete. Se o imposto não existir ou for zero, retorne 0.00.

        REGRA DE CLASSIFICAÇÃO DOS PRODUTOS:
        Para cada item, analise a descrição e classifique-o em uma destas 3 categorias na chave "categoria":
        - "CONSUMO": Materiais descartáveis, perecíveis, peças de reposição, parafusos, papel, canetas, tinta, insumos.
        - "PERMANENTE": Bens móveis duráveis que recebem tombamento, como TV, computadores, robôs, ferramentas pesadas, mobília, veículos.
        - "SERVICO": Mão de obra, frete, instalação, consultoria.

        Use exatamente o formato JSON abaixo (Mantenha objetos {} para cabecalho e impostos, e array [] para produtos). ATENÇÃO: a data de emissão DEVE estar no formato AAAA-MM-DD.
        {
          "cabecalho": {
            "numero": "string",
            "serie": "string",
            "data_emissao": "AAAA-MM-DD",
            "valor_total_produtos": 0.00,
            "valor_desconto": 0.00,
            "valor_frete": 0.00,
            "valor_total_nota": 0.00,
            "_cnpj": "string",
            "fornecedor_nome": "string",
            "destinatario_cnpj": "string",
            "destinatario_nome": "string",
            "impostos": {
              "ICMS": 0.00,
              "IPI": 0.00,
              "PIS": 0.00,
              "COFINS": 0.00,
              "ICMS_ST": 0.00
            }
          },    
          "produtos": [
            {
              "num": 1,
              "descricao": "...",
              "categoria": "CONSUMO", 
              "qtd": 0.0000,
              "unidade_comercial": "...",
              "valor_unitario": 0.0000,
              "valor_total": 0.00
            }
          ]
        }
        """
        
        configuracao_json = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.0
        )
        
        max_tentativas = 3
        tentativas = 0
        
        while tentativas < max_tentativas:
            try:
                # 1. Ação de Risco: Fazemos a chamada à API PRIMEIRO.
                resposta = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[arquivo_ia, prompt],
                    config=configuracao_json
                )
                
                # 2. SUCESSO: Incrementamos a cota com segurança. (Usando .pk para evitar avisos do Pylance)
                CotaDiariaIA.objects.filter(pk=cota_hoje.pk).update(requisicoes_feitas=F('requisicoes_feitas') + 1)
                
                # 3. Valida a existência do texto antes de fazer o parse
                texto_resposta = resposta.text
                if not texto_resposta:
                    raise ValueError("A IA retornou uma resposta vazia (possível bloqueio de segurança ou falha na rede).")
                    
                return json.loads(texto_resposta)
                
            except Exception as e:
                tentativas += 1
                erro_str = str(e)
                
                # Se esgotou as tentativas, aborta e avisa o sistema
                if tentativas >= max_tentativas:
                    raise Exception(f"Falha definitiva ao processar IA após {max_tentativas} tentativas. Último erro: {e}")
                    
                # BACKOFF EXPONENCIAL e By-Pass de bloqueio (Rate Limit)
                if any(erro in erro_str for erro in ["429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE"]):
                    tempo_espera = 2 ** tentativas # Exponencial: 2s, 4s, 8s
                    print(f"[{tentativas}/{max_tentativas}] Cota atingida ou serviço indisponível. Aguardando {tempo_espera}s...")
                    time.sleep(tempo_espera)
                else:
                    # Se for outro tipo de erro (ex: falha no JSON), levanta a exceção imediatamente
                    raise e 

    finally:
        # Garante a exclusão do arquivo no servidor do Google para evitar vazamento de dados do IFAM
        if arquivo_ia and arquivo_ia.name:
            try:
                client.files.delete(name=arquivo_ia.name)
            except:
                pass


def processar_nfe_com_gemini(caminho_pdf, usuario_logado):
    """
    Função Orquestradora: Aciona a IA, higieniza os retornos e persiste os dados na base do ARGUS.
    Contém a Trava de Sanidade para cálculo de descontos ocultos e Anti-Duplicidade.
    """
    dados = _extrair_nfe_json_gemini(caminho_pdf)
    
    if not dados:
        raise Exception("A Inteligência Artificial não conseguiu extrair os dados do PDF.")
        
    # --- ESCUDOS DE BLINDAGEM CONTRA IA REBELDE ---
    if isinstance(dados, list):
        dados = dados[0] if len(dados) > 0 else {}
        
    cabecalho = dados.get('cabecalho', {})
    if isinstance(cabecalho, list):
        cabecalho = cabecalho[0] if len(cabecalho) > 0 else {}
        
    impostos_extraidos = cabecalho.get('impostos', {})
    if isinstance(impostos_extraidos, list):
        impostos_extraidos = impostos_extraidos[0] if len(impostos_extraidos) > 0 else {}
    # -----------------------------------------------
    
    import re
    from cadastros.models import Fornecedor

    numero_nfe = cabecalho.get('numero', 'S/N')
    cnpj_emissor = cabecalho.get('fornecedor_cnpj', '')
    if not cnpj_emissor:
        cnpj_emissor = cabecalho.get('_cnpj', '')
    cnpj_emissor_limpo = re.sub(r'\D', '', cnpj_emissor)
    
    # =====================================================================
    # ESCUDO ANTI-DUPLICIDADE
    # =====================================================================
    if NotaFiscalAlmoxarifado.objects.filter(numero=numero_nfe, fornecedor__cnpj=cnpj_emissor_limpo).exists():
        raise Exception(f"A Nota Fiscal nº {numero_nfe} deste fornecedor já foi importada anteriormente. Verifique o histórico.")
    
    v_frete = Decimal(str(cabecalho.get('valor_frete', '0.00')))
    produtos = dados.get('produtos', [])
    
    data_emissao = cabecalho.get('data_emissao')
    if data_emissao == "AAAA-MM-DD" or not data_emissao:
        data_emissao = timezone.now().date()
        
    # 1. Captura os valores financeiros limpos pela nossa função sanitizadora
    v_produtos = _limpar_valor_ia(cabecalho.get('valor_total_produtos'))
    v_desconto = _limpar_valor_ia(cabecalho.get('valor_desconto'))
    v_nota = _limpar_valor_ia(cabecalho.get('valor_total_nota'))

    # =====================================================================
    # TRAVA DE SANIDADE (SANITY CHECK MATEMÁTICO)
    # =====================================================================
    if v_desconto == Decimal('0.00') and v_produtos > v_nota:
        v_desconto = v_produtos - v_nota

    # Upsert Fornecedor (MDM)
    fornecedor_obj = None
    if cnpj_emissor_limpo:
        nome_fornecedor = cabecalho.get('fornecedor_nome', 'FORNECEDOR NÃO IDENTIFICADO')[:255]
        fornecedor_obj, _ = Fornecedor.objects.get_or_create(
            cnpj=cnpj_emissor_limpo,
            defaults={'nome': nome_fornecedor}
        )

    # 2. Salva no banco de dados já validado
    nota = NotaFiscalAlmoxarifado.objects.create(
        numero=numero_nfe,
        serie=cabecalho.get('serie', ''),
        data_emissao=data_emissao,
        valor_total_produtos=v_produtos,
        valor_desconto=v_desconto,
        valor_frete=v_frete,
        valor_total_nota=v_nota,
        fornecedor=fornecedor_obj,
        destinatario_cnpj=cabecalho.get('destinatario_cnpj', ''),
        destinatario_nome=cabecalho.get('destinatario_nome', ''),
        usuario_recebedor=None,
        data_recebimento=None,
    )

    # 3. Interoperabilidade: Criação Relacional dos Impostos
    if isinstance(impostos_extraidos, dict):
        for sigla, valor in impostos_extraidos.items():
            if valor and float(valor) > 0:
                imposto_obj, created = Imposto.objects.get_or_create(
                    sigla=sigla.upper().strip(),
                    defaults={
                        'esfera': 'FEDERAL', 
                        'descricao': f'Imposto {sigla} extraído automaticamente'
                    }
                )
                
                ImpostoNota.objects.create(
                    nota=nota,
                    imposto=imposto_obj,
                    valor=Decimal(str(valor))
                )
    
    # 4. Itera e salva os insumos
    if isinstance(produtos, list):
        for p in produtos:
            ProdutoAlmoxarifado.objects.create(
                nota_fiscal=nota,
                numero_item=p.get('num', 1),
                descricao=p.get('descricao', ''),
                categoria=p.get('categoria', 'CONSUMO'),
                quantidade=_limpar_valor_ia(p.get('qtd')),
                unidade_comercial=p.get('unidade_comercial', 'UN'),
                valor_unitario=_limpar_valor_ia(p.get('valor_unitario')),
                valor_total=_limpar_valor_ia(p.get('valor_total'))
            )

    return nota
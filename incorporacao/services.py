import os
import shutil
import tempfile
import json
from google import genai
from google.genai import types
from django.conf import settings

def extrair_dados_do_termo(caminho_arquivo_pdf):
    """
    O cérebro do ARGUS. 
    Lê o PDF de forma blindada contra erros de caracteres no nome do arquivo 
    e extrai o OBJETO do termo de doação.
    """
    try:
        # Inicializa o cliente usando a NOVA sintaxe
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        # === TRUQUE ANTI-CARACTERE ESPECIAL (º, ç, ã) ===
        pasta_temp = tempfile.gettempdir()
        caminho_seguro = os.path.join(pasta_temp, "termo_seguro_argus_objeto.pdf")
        shutil.copy2(caminho_arquivo_pdf, caminho_seguro)
        # ================================================
        
        print("Fazendo upload do arquivo para o ARGUS (Extração do Objeto)...")
        arquivo_ia = client.files.upload(
            file=caminho_seguro, 
            config={'display_name': 'Termo de Doacao'}
        )
        
        # Destruímos a cópia física temporária por segurança
        if os.path.exists(caminho_seguro):
            os.remove(caminho_seguro)

        prompt = """
        Você é o ARGUS, um assistente especializado em leitura de Termos de Doação para o IFAM.
        Sua tarefa é extrair INTEGRALMENTE as cláusulas que definem o OBJETO do termo.
        
        Muitas vezes o objeto está dividido em 'CLÁUSULA PRIMEIRA' e 'CLÁUSULA SEGUNDA'. 
        Traga ambas se elas descreverem o que está sendo doado.

        EXEMPLO DE SAÍDA ESPERADA:
        "OBJETO
        Cláusula 1ª. Os bens móveis e imóveis, bem como demais recursos objetos desta doação são decorrente de investimentos promovido pela ora Anuente em Pesquisa, Desenvolvimento e Inovação nos termos do Convênio nº 013/2022.
        Cláusula 2ª. Os bens doados são os materiais relacionados no documento anexo, do Nº do Ativo de 3344 a 3382.
        Parágrafo único. O valor individualmente considerado de cada bem observará a depreciação na ordem descrita na Relação anexa, considerando o Art. 15 da Resolução 71 CAS-SUFRAMA, comprovadas por laudo de avaliação ou outra documentação em anexo a este que comprovará a plausibilidade da depreciação apontada."

        REGRAS:
        1. Se houver mais de uma cláusula sobre o objeto, concatene todas em um único texto.
        2. Não resuma. Transcreva o texto jurídico exatamente como está no PDF.
        3. Se não encontrar as cláusulas, traga o parágrafo de abertura que descreve a finalidade da doação.
        """
        
        print("Lendo o documento (pode levar alguns segundos)...")
        resposta = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=[arquivo_ia, prompt]
        )
        
        # Limpamos o arquivo lá da nuvem do Google
        client.files.delete(name=arquivo_ia.name)
        
        return resposta.text.strip()

    except Exception as e:
        print(f"====== ERRO FATAL ARGUS (Objeto) ======")
        print(e)
        print("=======================================")
        return None


def extrair_tudo_com_ia(caminho_pdf):
    """
    Função principal: Lê o PDF inteiro.
    Extrai:
    1. Lista de Notas Fiscais (pág 6 em diante).
    2. Lista de Itens Patrimoniais vinculados às notas.
    """
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        # Bloqueio Anti-Caractere Especial
        pasta_temp = tempfile.gettempdir()
        caminho_seguro = os.path.join(pasta_temp, "termo_seguro_argus_completo.pdf")
        shutil.copy2(caminho_pdf, caminho_seguro)
        
        print("Fazendo upload do arquivo para o ARGUS (Extração Completa)...")
        arquivo_ia = client.files.upload(
            file=caminho_seguro, 
            config={'display_name': 'Termo_Completo'}
        )
        
        if os.path.exists(caminho_seguro):
            os.remove(caminho_seguro)
        
        prompt = """
        Analise este Termo de Doação e seus anexos (especialmente as notas fiscais a partir da pág. 6).
        
        Retorne um JSON estrito com a seguinte estrutura:
        {
          "notas_fiscais": [
            {
              "numero": "...", "serie": "...", "chave_acesso": "...", 
              "data_emissao": "YYYY-MM-DD", "valor_total": 0.00,
              "fornecedor_nome": "...", "fornecedor_cnpj": "..."
            }
          ],
          "itens": [
            {
              "numero_ativo": "...", 
              "descricao": "...", 
              "valor_bem": 0.00, 
              "nota_fiscal_numero": "..." 
            }
          ]
        }
        
        IMPORTANTE: 
        1. "nota_fiscal_numero" nos itens deve bater com o "numero" na lista de notas.
        2. Converta datas para YYYY-MM-DD.
        3. Converta valores para float (use ponto).
        """
        
        configuracao_json = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1
        )
        
        print("Minerando Notas Fiscais e Itens...")
        resposta = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=[arquivo_ia, prompt],
            config=configuracao_json
        )
        
        dados = json.loads(resposta.text)
        client.files.delete(name=arquivo_ia.name)
        
        return dados

    except Exception as e:
        print(f"====== ERRO FATAL ARGUS (Extração Completa) ======")
        print(e)
        return None
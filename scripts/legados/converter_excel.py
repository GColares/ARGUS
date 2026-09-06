import os
import pandas as pd

def converter_em_massa():
    diretorio = 'importacao'
    arquivos_convertidos = 0
    
    print("--- Iniciando Conversão de XLSX para CSV ---")
    
    # Lista todos os arquivos na pasta importacao
    for arquivo in os.listdir(diretorio):
        # Ignora arquivos temporários do Excel (que começam com ~$) e pega só os .xlsx
        if arquivo.lower().endswith('.xlsx') and not arquivo.startswith('~$'):
            caminho_xlsx = os.path.join(diretorio, arquivo)
            nome_base = os.path.splitext(arquivo)[0]
            caminho_csv = os.path.join(diretorio, f"{nome_base}.csv")
            
            print(f"Lendo Excel: {arquivo}...")
            
            try:
                # Lê o Excel e salva como CSV separando por vírgula e usando codificação universal
                df = pd.read_excel(caminho_xlsx)
                df.to_csv(caminho_csv, index=False, encoding='utf-8')
                arquivos_convertidos += 1
                print(f"  -> Salvo com sucesso como CSV!")
            except Exception as e:
                print(f"  [ERRO] Não foi possível converter {arquivo}: {e}")

    print(f"\n--- Sucesso! {arquivos_convertidos} planilhas convertidas para CSV. ---")

if __name__ == '__main__':
    converter_em_massa()
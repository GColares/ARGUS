import pdfplumber
import os

def revelar_ocultos(pdf_path):
    print(f"\n--- REVELANDO CARACTERES OCULTOS NO PDF ---")
    if not os.path.exists(pdf_path):
        print("Arquivo não encontrado!")
        return

    with pdfplumber.open(pdf_path) as pdf:
        # Vamos olhar a página 4, onde estão os notebooks Samsung
        pagina = pdf.pages[3] 
        texto_bruto = pagina.extract_text()
        
        # Aqui a mágica acontece: trocamos o invisível pelo visível
        revelado = texto_bruto.replace("\n", " [ENTER]\n")
        revelado = revelado.replace("\t", " [TAB] ")
        
        print(revelado)
        print("\n--- FIM DA INSPEÇÃO ---")

# Substitua pelo nome real do seu arquivo PDF
revelar_ocultos("termo_teste.pdf")
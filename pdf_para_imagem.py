import pymupdf as fitz  # nome com que o PyMuPDF é importado
from pathlib import Path


def pdf_para_imagens(caminho_pdf, pasta_saida="imagens", zoom=2):
    # Cria a pasta de saída se ela ainda não existir
    Path(pasta_saida).mkdir(exist_ok=True)

    # Abre o PDF
    documento = fitz.open(caminho_pdf)

    # Pega só o nome do arquivo, sem a pasta e sem o ".pdf"
    nome_base = Path(caminho_pdf).stem

    caminhos_imagens = []

    # Percorre cada página do PDF (começando a contar do 1)
    for numero, pagina in enumerate(documento, start=1):
        # Define a qualidade da imagem
        matriz = fitz.Matrix(zoom, zoom)

        # Transforma a página em imagem
        imagem = pagina.get_pixmap(matrix=matriz)

        # Monta o nome do arquivo final e salva
        caminho_imagem = Path(pasta_saida) / f"{nome_base}_pagina{numero}.png"
        imagem.save(caminho_imagem)

        caminhos_imagens.append(str(caminho_imagem))

    documento.close()
    return caminhos_imagens


if __name__ == "__main__":
    resultado = pdf_para_imagens("nota_exemplo.pdf")
    print("Imagens geradas:")
    for caminho in resultado:
        print(" -", caminho)
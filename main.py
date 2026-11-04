import sys
from pathlib import Path

from banco import (
    criar_banco, salvar_nota, listar_notas,
    calcular_hash, hash_ja_existe, nota_ja_existe,
)
from pdf_para_imagem import pdf_para_imagens
from leitor_ia import ler_nota
from validacao import validar_nota, NotaInvalida


def processar_pdf(caminho_pdf):
    nome_arquivo = Path(caminho_pdf).name
    print(f"\nProcessando: {nome_arquivo}")

    # Camada 1: esse arquivo já foi processado? (não gasta cota da IA)
    hash_arquivo = calcular_hash(Path(caminho_pdf).read_bytes())
    if hash_ja_existe(hash_arquivo):
        print("  Já processado antes. Pulando (nenhuma requisição gasta).")
        return False

    imagens = pdf_para_imagens(caminho_pdf)

    for imagem in imagens:
        try:
            dados_brutos = ler_nota(imagem)
            dados_limpos = validar_nota(dados_brutos)
        except NotaInvalida as erro:
            print(f"  {Path(imagem).name} rejeitada: {erro}")
            continue

        # Camada 2: a mesma nota já está no banco, vinda de outro arquivo?
        if nota_ja_existe(dados_limpos):
            print("  Nota idêntica já existe no banco. Não salva de novo.")
            return False

        novo_id = salvar_nota(dados_limpos, nome_arquivo, hash_arquivo)
        print(f"  Salva com id {novo_id}: {dados_limpos}")
        return True

    print("  Nenhuma página válida. Nota NÃO foi salva.")
    return False
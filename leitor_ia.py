import os
import json
import time

from google import genai
from google.genai import types, errors

cliente = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Ordem de preferência. Confira os nomes exatos no Google AI Studio.
MODELOS = ["gemini-3.8-flash", "gemini-3.6-flash"]

PROMPT = """
Você está lendo uma nota fiscal (pode estar escaneada, torta ou amassada).
Extraia as informações abaixo e responda SOMENTE com um JSON, sem texto extra:

{
  "empresa": "nome da empresa que emitiu a nota",
  "valor_total": número com ponto decimal, sem símbolo de moeda (ex: 149.90),
  "data_emissao": "data de emissão no formato AAAA-MM-DD"
}

Se não conseguir ler algum campo com segurança, use null nele.
Não invente valores.
"""


def ler_nota(caminho_imagem, tentativas=3):
    with open(caminho_imagem, "rb") as arquivo:
        bytes_imagem = arquivo.read()

    imagem = types.Part.from_bytes(data=bytes_imagem, mime_type="image/png")

    for modelo in MODELOS:
        for tentativa in range(1, tentativas + 1):
            try:
                resposta = cliente.models.generate_content(
                    model=modelo,
                    contents=[imagem, PROMPT],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0,
                    ),
                )
                return json.loads(resposta.text)

            except errors.ServerError:
                print(f"{modelo} ocupado (tentativa {tentativa}/{tentativas}).")
                time.sleep(10 * tentativa)

            except errors.ClientError as erro:
                if erro.code in (404, 429):
                    motivo = "não existe para você" if erro.code == 404 else "sem cota hoje"
                    print(f"{modelo}: {motivo}. Tentando o próximo modelo...")
                    break
                raise

    raise RuntimeError("Todos os modelos estão ocupados ou sem cota. Tente mais tarde.")


if __name__ == "__main__":
    dados = ler_nota("imagens/nota_exemplo_pagina1.png")
    print(dados)
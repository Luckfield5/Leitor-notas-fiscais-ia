from datetime import datetime, date


class NotaInvalida(Exception):
    """Erro usado quando os dados lidos pela IA não passam na validação."""
    pass


def converter_valor(valor):
    # Se já é número, só garante que é float
    if isinstance(valor, (int, float)):
        return float(valor)

    # Se é texto (ex: "R$ 1.234,56"), limpa e converte
    if isinstance(valor, str):
        texto = valor.replace("R$", "").replace(" ", "")
        if "," in texto:
            # formato brasileiro: ponto separa milhar, vírgula separa decimal
            texto = texto.replace(".", "").replace(",", ".")
        return float(texto)

    raise ValueError("valor em formato desconhecido")


def validar_nota(dados):
    erros = []

    # --- Empresa ---
    empresa = dados.get("empresa")
    if not empresa or not str(empresa).strip():
        erros.append("empresa não foi lida")
    else:
        empresa = str(empresa).strip()

    # --- Valor total ---
    valor = None
    try:
        valor = converter_valor(dados.get("valor_total"))
        if valor <= 0:
            erros.append("valor_total precisa ser maior que zero")
    except (ValueError, TypeError):
        erros.append("valor_total não foi lido ou está inválido")

    # --- Data ---
    data_texto = dados.get("data_emissao")
    try:
        data = datetime.strptime(str(data_texto), "%Y-%m-%d").date()
        if data > date.today():
            erros.append("data_emissao está no futuro")
    except ValueError:
        erros.append("data_emissao não está no formato AAAA-MM-DD")

    # Se encontrou qualquer problema, interrompe e mostra todos
    if erros:
        raise NotaInvalida("; ".join(erros))

    # Tudo certo: devolve os dados limpos e padronizados
    return {
        "empresa": empresa,
        "valor_total": round(valor, 2),
        "data_emissao": data_texto,
    }


if __name__ == "__main__":
    # Teste 1: nota boa
    print(validar_nota({
        "empresa": "  Mercado Bom Preço ",
        "valor_total": "1.234,56",
        "data_emissao": "2026-10-15",
    }))

    # Teste 2: nota com problemas
    try:
        validar_nota({
            "empresa": None,
            "valor_total": -5,
            "data_emissao": "15/10/2026",
        })
    except NotaInvalida as erro:
        print("Rejeitada:", erro)
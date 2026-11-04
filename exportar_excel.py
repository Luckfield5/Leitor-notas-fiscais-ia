from datetime import datetime
from io import BytesIO
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

FORMATO_MOEDA = '[$R$-416] #,##0.00'
FORMATO_DATA = "DD/MM/YYYY"

LADO = Side(style="thin", color="BFBFBF")
BORDA = Border(left=LADO, right=LADO, top=LADO, bottom=LADO)


def estilizar_cabecalho(ws, cor="1F4E78"):
    for celula in ws[1]:
        celula.font = Font(bold=True, color="FFFFFF")
        celula.fill = PatternFill("solid", start_color=cor)
        celula.alignment = Alignment(horizontal="center", vertical="center")
        celula.border = BORDA
    ws.row_dimensions[1].height = 22
    ws.freeze_panes = "A2"


def ajustar_larguras(ws):
    for coluna in ws.columns:
        tamanhos = [len(str(c.value)) for c in coluna if c.value is not None]
        maior = max(tamanhos) if tamanhos else 10
        letra = coluna[0].column_letter
        ws.column_dimensions[letra].width = min(maior + 4, 50)


def gerar_excel(linhas):
    """Recebe a lista de notas do banco e devolve o arquivo .xlsx em bytes."""
    wb = Workbook()

    # ---------- Aba 1: Notas ----------
    ws = wb.active
    ws.title = "Notas"
    ws.append(["ID", "Empresa", "Valor total", "Data de emissão", "Arquivo"])

    for id_nota, empresa, valor, data_texto, arquivo in linhas:
        data = datetime.strptime(data_texto, "%Y-%m-%d").date()
        ws.append([id_nota, empresa, valor, data, arquivo])

    ultima = ws.max_row
    for numero in range(2, ultima + 1):
        ws.cell(numero, 3).number_format = FORMATO_MOEDA
        ws.cell(numero, 4).number_format = FORMATO_DATA
        ws.cell(numero, 4).alignment = Alignment(horizontal="center")
        for coluna in range(1, 6):
            ws.cell(numero, coluna).border = BORDA

    if ultima >= 2:
        linha_total = ultima + 1
        ws.cell(linha_total, 2, "TOTAL").font = Font(bold=True)
        total = ws.cell(linha_total, 3, f"=SUM(C2:C{ultima})")
        total.number_format = FORMATO_MOEDA
        total.font = Font(bold=True)
        ws.auto_filter.ref = f"A1:E{ultima}"

    estilizar_cabecalho(ws)
    ajustar_larguras(ws)

    # ---------- Aba 2: Resumo por empresa ----------
    resumo = wb.create_sheet("Resumo por empresa")
    resumo.append(["Empresa", "Quantidade de notas", "Valor total"])

    totais = {}
    for _, empresa, valor, _, _ in linhas:
        qtd, soma = totais.get(empresa, (0, 0.0))
        totais[empresa] = (qtd + 1, soma + valor)

    ordenado = sorted(totais.items(), key=lambda item: item[1][1], reverse=True)
    for empresa, (qtd, soma) in ordenado:
        resumo.append([empresa, qtd, round(soma, 2)])

    for numero in range(2, resumo.max_row + 1):
        resumo.cell(numero, 3).number_format = FORMATO_MOEDA
        resumo.cell(numero, 2).alignment = Alignment(horizontal="center")
        for coluna in range(1, 4):
            resumo.cell(numero, coluna).border = BORDA

    estilizar_cabecalho(resumo, cor="375623")
    ajustar_larguras(resumo)

    # ---------- Salvar em memória ----------
    from io import BytesIO
    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


if __name__ == "__main__":
    # Teste rápido: gera o arquivo na pasta do projeto
    from banco import listar_notas

    Path("notas_fiscais.xlsx").write_bytes(gerar_excel(listar_notas()))
    print("Arquivo notas_fiscais.xlsx criado!")
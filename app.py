import tempfile
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from banco import (
    criar_banco, salvar_nota, listar_notas,
    calcular_hash, hash_ja_existe, nota_ja_existe,
    atualizar_nota, excluir_nota,
)
from exportar_excel import gerar_excel
from leitor_ia import ler_nota
from pdf_para_imagem import pdf_para_imagens
from validacao import validar_nota, NotaInvalida

criar_banco()


def formatar_real(valor):
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def limpar(valor):
    """Troca valores vazios do pandas (NaN/NaT) por None."""
    return None if pd.isna(valor) else valor


st.set_page_config(page_title="Leitor de Notas Fiscais", page_icon="🧾")
st.title("🧾 Leitor de Notas Fiscais")
st.write("Envie notas em PDF e a IA extrai empresa, valor total e data.")

arquivos = st.file_uploader(
    "Escolha os PDFs",
    type="pdf",
    accept_multiple_files=True,
)

if st.button("Processar notas") and arquivos:
    for arquivo in arquivos:
        # Camada 1: arquivo já processado? Pula sem gastar a IA
        hash_arquivo = calcular_hash(arquivo.getvalue())
        if hash_ja_existe(hash_arquivo):
            st.info(f"{arquivo.name}: já foi processado antes. Pulando.")
            continue

        resolvida = False  # salvou ou identificou duplicata

        with st.spinner(f"Lendo {arquivo.name}..."):
            with tempfile.TemporaryDirectory() as pasta:
                caminho = Path(pasta) / arquivo.name
                caminho.write_bytes(arquivo.getbuffer())

                imagens = pdf_para_imagens(str(caminho), pasta_saida=pasta)

                for imagem in imagens:
                    try:
                        dados_brutos = ler_nota(imagem)
                        dados_limpos = validar_nota(dados_brutos)
                    except NotaInvalida as erro:
                        st.warning(f"{arquivo.name}: página rejeitada ({erro})")
                        continue
                    except RuntimeError as erro:
                        st.error(f"IA indisponível: {erro}")
                        resolvida = True
                        break

                    # Camada 2: nota idêntica já existe?
                    if nota_ja_existe(dados_limpos):
                        st.warning(
                            f"{arquivo.name}: nota idêntica "
                            f"({dados_limpos['empresa']}, "
                            f"R$ {dados_limpos['valor_total']:.2f}, "
                            f"{dados_limpos['data_emissao']}) já está no banco."
                        )
                        resolvida = True
                        break

                    novo_id = salvar_nota(dados_limpos, arquivo.name, hash_arquivo)
                    st.success(
                        f"{arquivo.name} salva (id {novo_id}): "
                        f"{dados_limpos['empresa']} | "
                        f"R$ {dados_limpos['valor_total']:.2f} | "
                        f"{dados_limpos['data_emissao']}"
                    )
                    resolvida = True
                    break

        if not resolvida:
            st.error(f"{arquivo.name}: nenhuma página válida. Nota não salva.")

st.divider()
st.subheader("Notas salvas")

# Mensagem deixada pelo "Salvar alterações" antes de recarregar a página
if "mensagem" in st.session_state:
    st.success(st.session_state.pop("mensagem"))

linhas = listar_notas()
if linhas:
    tabela = pd.DataFrame(
        linhas,
        columns=["ID", "Empresa", "Valor total", "Data", "Arquivo"],
    )

    # Cópia só para exibição (a original continua numérica)
    exibicao = tabela.copy()
    exibicao["Valor total"] = exibicao["Valor total"].map(formatar_real)
    exibicao["Data"] = pd.to_datetime(exibicao["Data"]).dt.strftime("%d/%m/%Y")

    st.dataframe(exibicao)
    st.metric("Soma de todas as notas", formatar_real(tabela["Valor total"].sum()))

    st.download_button(
        label="📥 Baixar Excel",
        data=gerar_excel(linhas),
        file_name=f"notas_fiscais_{date.today():%Y-%m-%d}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # ---------- Editar ou excluir ----------
    with st.expander("✏️ Editar ou excluir notas"):
        st.caption(
            "Altere as células e marque 'Excluir' nas notas que quer apagar. "
            "A exclusão é definitiva."
        )

        original = tabela[["ID", "Empresa", "Valor total", "Data"]].copy()
        original["Data"] = pd.to_datetime(original["Data"]).dt.date
        original["Excluir"] = False

        versao = st.session_state.get("versao_editor", 0)

        editada = st.data_editor(
            original,
            key=f"editor_notas_{versao}",
            hide_index=True,
            num_rows="fixed",
            disabled=["ID"],
            column_config={
                "Valor total": st.column_config.NumberColumn(
                    "Valor total", format="R$ %.2f", min_value=0.01, step=0.01
                ),
                "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "Excluir": st.column_config.CheckboxColumn("Excluir"),
            },
        )

        if st.button("Salvar alterações"):
            para_atualizar = []
            para_excluir = []
            erros = []

            for i in range(len(original)):
                antes = original.iloc[i]
                depois = editada.iloc[i]
                id_nota = int(depois["ID"])

                if depois["Excluir"]:
                    para_excluir.append(id_nota)
                    continue

                mudou = (
                    str(antes["Empresa"]) != str(depois["Empresa"])
                    or str(antes["Valor total"]) != str(depois["Valor total"])
                    or str(antes["Data"]) != str(depois["Data"])
                )
                if not mudou:
                    continue

                try:
                    dados = validar_nota({
                        "empresa": limpar(depois["Empresa"]),
                        "valor_total": limpar(depois["Valor total"]),
                        "data_emissao": str(limpar(depois["Data"])),
                    })
                except NotaInvalida as erro:
                    erros.append(f"ID {id_nota}: {erro}")
                    continue

                para_atualizar.append((id_nota, dados))

            if erros:
                # Tudo ou nada: se houver erro, nada é salvo
                for erro in erros:
                    st.error(erro)
                st.warning("Nenhuma alteração foi salva. Corrija e tente de novo.")
            elif not para_atualizar and not para_excluir:
                st.info("Nenhuma alteração para salvar.")
            else:
                for id_nota, dados in para_atualizar:
                    atualizar_nota(id_nota, dados)
                for id_nota in para_excluir:
                    excluir_nota(id_nota)

                st.session_state["mensagem"] = (
                    f"{len(para_atualizar)} nota(s) atualizada(s) e "
                    f"{len(para_excluir)} excluída(s)."
                )
                st.session_state["versao_editor"] = versao + 1
                st.rerun()
else:
    st.info("Nenhuma nota salva ainda.")
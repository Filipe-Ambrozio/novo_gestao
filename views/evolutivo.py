from datetime import datetime

import requests
import pandas as pd
import plotly.express as px
import streamlit as st


MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


def _mes_nome(valor):
    texto = str(valor).strip()
    if texto.isdigit() and 1 <= int(texto) <= 12:
        return MESES[int(texto) - 1]
    texto_lower = texto.lower()
    for mes in MESES:
        if texto_lower == mes.lower() or texto_lower.startswith(mes[:3].lower()):
            return mes
    return texto.title()


def _valor(valor):
    if pd.isna(valor) or str(valor).strip() in ("", "-"):
        return 0.0
    texto = str(valor).strip().replace("R$", "").replace("%", "")
    texto = texto.replace(".", "").replace(",", ".").replace(" ", "")
    try:
        return float(texto)
    except ValueError:
        return 0.0


@st.cache_data(ttl=300, show_spinner=False)
def carregar_dados(url):
    resposta = requests.get(
        f"{url}?tipo_registro=evolutivo_pereciveis",
        headers={"Cache-Control": "no-cache"},
        timeout=15,
    )
    resposta.raise_for_status()
    dados = resposta.json()
    if isinstance(dados, dict) and "error" in dados:
        raise ValueError(dados["error"])
    return pd.DataFrame(dados)


def render(url):
    st.title("Evolutivo de Quebras | Perecíveis")
    st.caption("Consulte a quebra mensal por setor e compare diferentes anos.")

    try:
        df = carregar_dados(url)
    except (requests.RequestException, ValueError) as error:
        mensagem = str(error)
        if "tipo_registro inválido" in mensagem:
            mensagem += " Publique novamente o google_apps_script.gs no Apps Script e selecione a nova implantação."
        st.error(f"Não foi possível carregar a aba Evolutivo_Pereciveis: {mensagem}")
        return

    required = {"ano", "mes", "setor", "quebra"}
    if df.empty or not required.issubset(df.columns):
        st.warning("A aba Evolutivo_Pereciveis precisa conter as colunas ano, mes, setor e quebra.")
        return

    df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    df["mes_nome"] = df["mes"].map(_mes_nome)
    df["setor"] = df["setor"].astype(str).str.strip()
    df["quebra"] = df["quebra"].map(_valor)
    df = df.dropna(subset=["ano"])
    df["ano"] = df["ano"].astype(int)
    df = df[df["setor"].ne("")]

    if df.empty:
        st.info("Não há registros válidos para exibir.")
        return

    setores = sorted(df["setor"].unique().tolist())
    anos = sorted(df["ano"].unique().tolist(), reverse=True)
    anos_selecionados = st.multiselect("Anos para comparar", anos, default=anos)
    if not anos_selecionados:
        st.info("Selecione pelo menos um ano.")
        return
    mes_atual = MESES[datetime.now().month - 1]
    mes_selecionado = st.selectbox(
        "Mês para somar todos os setores",
        MESES,
        index=MESES.index(mes_atual),
    )
    setor = st.selectbox("Setor para visualizar a evolução", setores)

    filtrado = df[df["setor"].eq(setor) & df["ano"].isin(anos_selecionados)].copy()
    total_mes_todos_setores = df[
        df["ano"].isin(anos_selecionados) & df["mes_nome"].eq(mes_selecionado)
    ]["quebra"].sum()
    resumo = filtrado.groupby(["ano", "mes_nome"], as_index=False)["quebra"].sum()
    resumo["mes_nome"] = pd.Categorical(resumo["mes_nome"], categories=MESES, ordered=True)
    resumo = resumo.sort_values(["ano", "mes_nome"])

    total = resumo["quebra"].sum()
    media_mensal = resumo.groupby("mes_nome", observed=False)["quebra"].sum().mean()
    maior_mes = resumo.loc[resumo["quebra"].abs().idxmax(), "mes_nome"] if not resumo.empty else "-"
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Quebra no período", f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    col2.metric("Média mensal", f"R$ {media_mensal:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    col3.metric("Mês de maior quebra", maior_mes)
    col4.metric(
        f"{mes_selecionado} - todos os setores",
        f"R$ {total_mes_todos_setores:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    )

    grafico = px.line(
        resumo,
        x="mes_nome",
        y="quebra",
        color="ano",
        markers=True,
        category_orders={"mes_nome": MESES},
        labels={"mes_nome": "Mês", "quebra": "Quebra (R$)", "ano": "Ano"},
        title=f"Quebra mensal do setor {setor}",
    )
    grafico.update_layout(hovermode="x unified")
    st.plotly_chart(grafico, use_container_width=True)

    tabela = resumo.pivot(index="mes_nome", columns="ano", values="quebra").reindex(MESES)
    tabela.columns = [str(ano) for ano in tabela.columns]
    st.dataframe(tabela.style.format("R$ {:,.2f}"), use_container_width=True)
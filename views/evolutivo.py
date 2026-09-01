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

    anos = sorted(df["ano"].unique().tolist(), reverse=True)
    mes_atual = MESES[datetime.now().month - 1]
    col_periodo_1, col_periodo_2 = st.columns(2)
    with col_periodo_1:
        ano_1 = st.selectbox("Ano do mês principal", anos, key="evolutivo_ano_1")
        mes_1 = st.selectbox("Mês principal", MESES, index=MESES.index(mes_atual), key="evolutivo_mes_1")
    with col_periodo_2:
        ano_2 = st.selectbox("Ano para comparação", anos, key="evolutivo_ano_2")
        mes_2 = st.selectbox("Mês para comparação", MESES, index=(MESES.index(mes_atual) - 1) % 12, key="evolutivo_mes_2")

    setores = sorted(df["setor"].unique().tolist())
    periodo_1 = df[df["ano"].eq(ano_1) & df["mes_nome"].eq(mes_1)]
    periodo_2 = df[df["ano"].eq(ano_2) & df["mes_nome"].eq(mes_2)]
    tabela_setores = pd.DataFrame({"Setor": setores})
    valores_1 = periodo_1.groupby("setor")["quebra"].sum()
    valores_2 = periodo_2.groupby("setor")["quebra"].sum()
    tabela_setores["quebra_principal"] = tabela_setores["Setor"].map(valores_1).fillna(0)
    tabela_setores["quebra_comparacao"] = tabela_setores["Setor"].map(valores_2).fillna(0)
    tabela_setores["variação"] = tabela_setores["quebra_principal"] - tabela_setores["quebra_comparacao"]

    total_principal = tabela_setores["quebra_principal"].sum()
    total_comparacao = tabela_setores["quebra_comparacao"].sum()
    variacao_total = tabela_setores["variação"].sum()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(f"Total {mes_1}/{ano_1}", f"R$ {total_principal:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    col2.metric(f"Total {mes_2}/{ano_2}", f"R$ {total_comparacao:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    col3.metric("Variação total", f"R$ {variacao_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    col4.metric("Setores exibidos", len(setores))

    st.subheader("Quebra por setor")
    tabela_exibicao = tabela_setores.rename(columns={
        "quebra_principal": f"Quebra {mes_1}/{ano_1}",
        "quebra_comparacao": f"Quebra {mes_2}/{ano_2}",
        "variação": "Variação",
    })
    st.dataframe(
        tabela_exibicao.style.format({
            f"Quebra {mes_1}/{ano_1}": "R$ {:,.2f}",
            f"Quebra {mes_2}/{ano_2}": "R$ {:,.2f}",
            "Variação": "R$ {:,.2f}",
        }),
        use_container_width=True,
        hide_index=True,
    )

    setor = st.selectbox("Setor para visualizar a evolução mensal", setores)
    filtrado = df[df["setor"].eq(setor) & df["ano"].isin([ano_1, ano_2])].copy()
    resumo = filtrado.groupby(["ano", "mes_nome"], as_index=False)["quebra"].sum()
    resumo["mes_nome"] = pd.Categorical(resumo["mes_nome"], categories=MESES, ordered=True)
    resumo = resumo.sort_values(["ano", "mes_nome"])
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

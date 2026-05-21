import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from views.dashboard import moeda

MESES_ORDEM = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]


def limpar_valor_monetario(v):
    if pd.isna(v) or v == '' or v == '-' or v == 'R$ -':
        return 0
    try:
        if isinstance(v, str):
            eh_negativo = '-' in v
            valor = v.replace('R$', '').replace('-', '').replace('.', '').replace(',', '.').strip()
            num = float(valor) if valor else 0
            return -num if eh_negativo else num
        return float(v)
    except:
        return 0


def normalizar_mes(valor):
    if pd.isna(valor):
        return ""
    if isinstance(valor, (int, float)):
        if 1 <= int(valor) <= 12:
            return MESES_ORDEM[int(valor) - 1]
        return str(valor).strip()

    texto = str(valor).strip()
    if texto.isdigit():
        indice = int(texto)
        if 1 <= indice <= 12:
            return MESES_ORDEM[indice - 1]
        return texto

    texto_lower = texto.lower()
    for mes in MESES_ORDEM:
        if texto_lower == mes.lower() or texto_lower.startswith(mes[:3].lower()):
            return mes
    return texto.title()


def fetch_dados(URL):
    try:
        url_com_param = f"{URL}?tipo_registro=dados&_ts={datetime.now().timestamp()}"
        response = requests.get(url_com_param, headers={"Cache-Control": "no-cache"}, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as error:
        st.error(f"❌ Erro ao carregar dados: {error}")
        return []


def agregar_periodo(df, ano, mes):
    if df is None or df.empty:
        return None

    valores = {
        "Ano": ano,
        "Mês": mes,
        "Vendas": 0,
        "Quebra Inicial": 0,
        "Quebra Ident.": 0,
        "Quebra Não Ident.": 0,
        "Quebra FINAL": 0,
        "TOTAL RECEITAS": 0,
        "CONTRATOS": 0,
        "ACORDOS": 0,
        "REVERSÃO": 0,
        "Real %": None,
        "Meta %": None,
    }

    for coluna in valores:
        if coluna in ["Ano", "Mês"]:
            continue
        if coluna in df.columns:
            if coluna in ["Real %", "Meta %"]:
                valores[coluna] = df[coluna].mean() if not df.empty else None
            else:
                valores[coluna] = df[coluna].sum()

    return valores


def formatar_linha(row):
    return {
        "Vendas": moeda(row["Vendas"]),
        "Quebra Inicial": moeda(row["Quebra Inicial"]),
        "Quebra Ident.": moeda(row["Quebra Ident."]),
        "Quebra Não Ident.": moeda(row["Quebra Não Ident."]),
        "Quebra FINAL": moeda(row["Quebra FINAL"]),
        "Total Receitas": moeda(row["TOTAL RECEITAS"]),
        "Contratos": moeda(row["CONTRATOS"]),
        "Acordos": moeda(row["ACORDOS"]),
        "Reversão": moeda(row["REVERSÃO"]),
        "Real %": f"{row['Real %']:.2f}%" if row["Real %"] is not None else "-",
        "Meta %": f"{row['Meta %']:.2f}%" if row["Meta %"] is not None else "-",
    }


def render(URL):
    st.title("📊 Comparativo de Vendas e Quebras")

    dados_raw = fetch_dados(URL)
    if isinstance(dados_raw, dict) and "error" in dados_raw:
        st.error(f"❌ Erro: {dados_raw['error']}")
        return

    if not dados_raw:
        st.warning("⚠️ Nenhum dado encontrado na planilha.")
        return

    if isinstance(dados_raw, dict):
        dados_raw = [dados_raw]

    try:
        df = pd.DataFrame(dados_raw)
    except Exception as e:
        st.error(f"❌ Erro ao converter dados: {e}")
        return

    df.columns = df.columns.str.strip()
    numeric_cols = [
        "Vendas", "Quebra Inicial", "Quebra Ident.", "Quebra Não Ident.",
        "Quebra FINAL", "CONTRATOS", "ACORDOS", "TOTAL RECEITAS", "REVERSÃO",
        "Real %", "Meta %"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(limpar_valor_monetario)

    if "ano" in df.columns:
        df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    if "mes" in df.columns:
        df["mes_nome"] = df["mes"].apply(normalizar_mes)
    else:
        df["mes_nome"] = ""

    if "ano" in df.columns:
        df = df[df["ano"].notna()]

    anos_disponiveis = sorted(df["ano"].dropna().unique()) if "ano" in df.columns else []
    if not anos_disponiveis:
        st.warning("⚠️ A coluna 'ano' não está disponível ou não possui valores válidos.")
        return

    mes_disponiveis = [mes for mes in MESES_ORDEM if mes in df["mes_nome"].unique()]
    if not mes_disponiveis:
        mes_disponiveis = MESES_ORDEM

    st.markdown("### Selecione os dois períodos para comparação")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ano1 = st.selectbox("Ano 1", anos_disponiveis, index=0, key="comparativo_ano1")
    with col2:
        mes1 = st.selectbox("Mês 1", mes_disponiveis, key="comparativo_mes1")
    with col3:
        ano2 = st.selectbox("Ano 2", anos_disponiveis, index=1 if len(anos_disponiveis) > 1 else 0, key="comparativo_ano2")
    with col4:
        mes2 = st.selectbox("Mês 2", mes_disponiveis, key="comparativo_mes2")

    if ano1 == ano2 and mes1 == mes2:
        st.info("Você selecionou o mesmo mês/ano nos dois períodos. Se quiser comparar anos diferentes, escolha outro período.")

    df1 = df[(df["ano"] == ano1) & (df["mes_nome"] == mes1)]
    df2 = df[(df["ano"] == ano2) & (df["mes_nome"] == mes2)]

    valores1 = agregar_periodo(df1, ano1, mes1)
    valores2 = agregar_periodo(df2, ano2, mes2)

    colA, colB = st.columns(2)
    with colA:
        st.subheader(f"Período 1: {mes1} / {int(ano1)}")
        if valores1:
            st.metric("💰 Vendas", moeda(valores1["Vendas"]))
            st.metric("⚠️ Quebra Ident.", moeda(valores1["Quebra Ident."]))
            st.metric("⚠️ Quebra Não Ident.", moeda(valores1["Quebra Não Ident."]))
            st.metric("🚨 Quebra FINAL", moeda(valores1["Quebra FINAL"]))
            if valores1["Real %"] is not None and valores1["Meta %"] is not None:
                st.metric("🎯 Real %", f"{valores1['Real %']:.2f}%", delta=f"Meta {valores1['Meta %']:.2f}%")
            st.metric("💵 Total Receitas", moeda(valores1["TOTAL RECEITAS"]))
            st.metric("📄 Contratos", moeda(valores1["CONTRATOS"]))
            st.metric("🤝 Acordos", moeda(valores1["ACORDOS"]))
        else:
            st.warning("Nenhum dado encontrado para o período 1.")

    with colB:
        st.subheader(f"Período 2: {mes2} / {int(ano2)}")
        if valores2:
            st.metric("💰 Vendas", moeda(valores2["Vendas"]))
            st.metric("⚠️ Quebra Ident.", moeda(valores2["Quebra Ident."]))
            st.metric("⚠️ Quebra Não Ident.", moeda(valores2["Quebra Não Ident."]))
            st.metric("🚨 Quebra FINAL", moeda(valores2["Quebra FINAL"]))
            if valores2["Real %"] is not None and valores2["Meta %"] is not None:
                st.metric("🎯 Real %", f"{valores2['Real %']:.2f}%", delta=f"Meta {valores2['Meta %']:.2f}%")
            st.metric("💵 Total Receitas", moeda(valores2["TOTAL RECEITAS"]))
            st.metric("📄 Contratos", moeda(valores2["CONTRATOS"]))
            st.metric("🤝 Acordos", moeda(valores2["ACORDOS"]))
        else:
            st.warning("Nenhum dado encontrado para o período 2.")

    st.markdown("---")
    st.markdown("### Comparação lado a lado")

    rows = [valores1, valores2]
    df_compare = pd.DataFrame(rows)
    if not df_compare.empty:
        df_compare_display = df_compare.copy()
        for col in ["Vendas", "Quebra Inicial", "Quebra Ident.", "Quebra Não Ident.", "Quebra FINAL", "TOTAL RECEITAS", "CONTRATOS", "ACORDOS", "REVERSÃO"]:
            if col in df_compare_display.columns:
                df_compare_display[col] = df_compare_display[col].apply(moeda)
        df_compare_display["Real %"] = df_compare_display["Real %"].apply(lambda x: f"{x:.2f}%" if x is not None else "-")
        df_compare_display["Meta %"] = df_compare_display["Meta %"].apply(lambda x: f"{x:.2f}%" if x is not None else "-")
        st.dataframe(df_compare_display.set_index(["Ano", "Mês"]), use_container_width=True)

    if valores1 and valores2:
        diff = {
            "Métrica": [],
            "Período 2 - Período 1": []
        }
        for col in ["Vendas", "Quebra Inicial", "Quebra Ident.", "Quebra Não Ident.", "Quebra FINAL", "TOTAL RECEITAS", "CONTRATOS", "ACORDOS", "REVERSÃO"]:
            if col in valores1 and col in valores2:
                diff[col] = valores2[col] - valores1[col]
                diff["Métrica"].append(col)
                diff["Período 2 - Período 1"].append(moeda(diff[col]))
        if valores1["Real %"] is not None and valores2["Real %"] is not None:
            diff["Métrica"].append("Real %")
            diff["Período 2 - Período 1"].append(f"{valores2['Real %'] - valores1['Real %']:.2f}%")
        if valores1["Meta %"] is not None and valores2["Meta %"] is not None:
            diff["Métrica"].append("Meta %")
            diff["Período 2 - Período 1"].append(f"{valores2['Meta %'] - valores1['Meta %']:.2f}%")

        st.markdown("### Delta entre os períodos")
        st.dataframe(pd.DataFrame(diff).set_index("Métrica"), use_container_width=True)

    st.markdown("---")
    st.markdown("### Dados detalhados por período")
    col_det1, col_det2 = st.columns(2)
    with col_det1:
        st.write(f"#### Detalhes Período 1: {mes1} / {int(ano1)}")
        if not df1.empty:
            st.dataframe(df1, use_container_width=True)
        else:
            st.write("Nenhum registro encontrado para este período.")

    with col_det2:
        st.write(f"#### Detalhes Período 2: {mes2} / {int(ano2)}")
        if not df2.empty:
            st.dataframe(df2, use_container_width=True)
        else:
            st.write("Nenhum registro encontrado para este período.")

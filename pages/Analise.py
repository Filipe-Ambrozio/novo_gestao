# import streamlit as st
# from views import gestao

# st.set_page_config(page_title="Gestão Diária", page_icon="🧾", layout="wide")

# URL = "https://script.google.com/macros/s/AKfycbwm4g0-syNMM3RFdviJLJej_h7yqNW9xaCBtj7PYkHxFwxGc4vpThnlfGkrI1c-Na83mQ/exec"


# def main():
#     gestao.render(URL)


# if __name__ == "__main__":
#     main()

import streamlit as st
import requests
import pandas as pd
import pytz
from datetime import datetime
import urllib.parse
import plotly.graph_objects as go

st.set_page_config(page_title="Análise", layout="wide")

URL = "https://script.google.com/macros/s/AKfycbwm4g0-syNMM3RFdviJLJej_h7yqNW9xaCBtj7PYkHxFwxGc4vpThnlfGkrI1c-Na83mQ/exec"


def moeda(v):
    return f"{abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


MESES_ORDEM = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


def limpar_valor_monetario(v):
    if pd.isna(v) or v == "" or v == "-" or v == "R$ -":
        return 0
    try:
        if isinstance(v, str):
            eh_negativo = "-" in v
            string_val = v.replace("R$", "").replace("-", "").replace(".", "").replace(",", ".").strip()
            num = float(string_val) if string_val else 0
            return -num if eh_negativo else num
        return float(v)
    except Exception:
        return 0


def normalizar_mes(valor):
    if pd.isna(valor):
        return ""
    texto = str(valor).strip()
    if texto.isdigit():
        indice = int(texto)
        if 1 <= indice <= 12:
            return MESES_ORDEM[indice - 1]
    for mes in MESES_ORDEM:
        if texto.lower() == mes.lower() or texto.lower().startswith(mes[:3].lower()):
            return mes
    return texto.title()


def fetch_dados(URL):
    try:
        url_com_param = f"{URL}?tipo_registro=dados&_ts={datetime.now().timestamp()}"
        response = requests.get(url_com_param, headers={"Cache-Control": "no-cache"}, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as error:
        return {"error": str(error), "url": URL}


def formatar_valor(v):
    if v > 0:
        return f"+R$ {moeda(v)}"
    elif v < 0:
        return f"-R$ {moeda(v)}"
    else:
        return f"R$ {moeda(v)}"


def find_column(df, names):
    columns = {c.strip().lower(): c for c in df.columns}
    for name in names:
        key = name.strip().lower()
        if key in columns:
            return columns[key]
    for name in names:
        key = name.strip().lower()
        for column_key, original in columns.items():
            if key in column_key:
                return original
    return None


def fetch_qb_id(URL):
    last_error = None
    tipos = ["qb_id", "QB_ID", "qbId"]
    for tipo in tipos:
        try:
            response = requests.get(
                URL,
                params={"tipo_registro": tipo, "_ts": datetime.now().timestamp()},
                headers={"Cache-Control": "no-cache"},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and data.get("error"):
                if "tipo_registro" in str(data.get("error")).lower():
                    last_error = data.get("error")
                    continue
            return data
        except Exception as error:
            last_error = str(error)

    return {
        "error": (
            "tipo_registro inválido ou não informado. "
            "Verifique se o Google Apps Script foi publicado com suporte a qb_id. "
            f"Último erro: {last_error}"
        ),
        "url": URL,
    }


def campo_valor(label, key):
    v = st.number_input(label, value=0.0, key=key)
    if v < 0:
        st.markdown("<span style='color:red'>🔴 Valor negativo</span>", unsafe_allow_html=True)
    return v

def render(URL):

    st.title("📌 Quebra Venda")


    dados_raw = fetch_dados(URL)
    if isinstance(dados_raw, dict) and "error" in dados_raw:
        st.warning(f"Não foi possível carregar os dados mensais: {dados_raw['error']}")
    elif not dados_raw:
        st.warning("Nenhum dado encontrado para montar o resumo mensal.")
    else:
        if isinstance(dados_raw, dict):
            dados_raw = [dados_raw]

        try:
            df = pd.DataFrame(dados_raw)
        except Exception as e:
            st.error(f"Erro ao criar tabela de dados: {e}")
            df = pd.DataFrame()

        if not df.empty:
            df.columns = df.columns.str.strip()
            if "ano" in df.columns:
                df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
            if "mes" in df.columns:
                df["mes"] = df["mes"].astype(str).str.strip()

            if "ano" in df.columns and "mes" in df.columns:
                df = df[df["ano"].notna()]
                anos_disponiveis = sorted(df["ano"].dropna().unique())
                if anos_disponiveis:
                    agora = datetime.now(pytz.timezone("America/Sao_Paulo"))
                    ano_atual = agora.year
                    mes_atual = MESES_ORDEM[agora.month - 1]

                    ano_index = anos_disponiveis.index(ano_atual) if ano_atual in anos_disponiveis else 0
                    ano_selecionado = st.selectbox("Filtrar por ano:", anos_disponiveis, index=ano_index, key="gestao_ano_filtro")
                    df_ano = df[df["ano"] == ano_selecionado].copy()
                    df_ano["mes_nome"] = df_ano["mes"].apply(normalizar_mes)
                    df_ano["mes_nome"] = pd.Categorical(df_ano["mes_nome"], categories=MESES_ORDEM, ordered=True)
                    if "Meta %" in df_ano.columns:
                        df_ano["Meta %"] = df_ano["Meta %"].apply(lambda v: limpar_valor_monetario(str(v).replace("%", "")))
                    if "Real %" in df_ano.columns:
                        df_ano["Real %"] = df_ano["Real %"].apply(lambda v: limpar_valor_monetario(str(v).replace("%", "")))

                    meses_disponiveis = [mes for mes in MESES_ORDEM if mes in df_ano["mes_nome"].dropna().unique()]
                    if not meses_disponiveis:
                        meses_disponiveis = [mes for mes in MESES_ORDEM if mes in df["mes_nome"].dropna().unique()]
                    if not meses_disponiveis:
                        meses_disponiveis = MESES_ORDEM.copy()

                    mes_index = meses_disponiveis.index(mes_atual) if mes_atual in meses_disponiveis else 0
                    mes_selecionado = st.selectbox("Filtrar por mês:", meses_disponiveis, index=mes_index, key="gestao_mes_filtro")
                    df_mes_selecionado = df_ano[df_ano["mes_nome"] == mes_selecionado].copy()

                    vendas = df_mes_selecionado["Vendas"].apply(limpar_valor_monetario).sum() if "Vendas" in df.columns else 0
                    quebra_ident = df_mes_selecionado["Quebra Ident."].apply(limpar_valor_monetario).sum() if "Quebra Ident." in df.columns else 0
                    quebra_nao_ident = df_mes_selecionado["Quebra Não Ident."].apply(limpar_valor_monetario).sum() if "Quebra Não Ident." in df.columns else 0
                    quebra_final = df_mes_selecionado["Quebra FINAL"].apply(limpar_valor_monetario).sum() if "Quebra FINAL" in df.columns else 0
                    meta_percent = df_mes_selecionado["Meta %"].mean() if "Meta %" in df_ano.columns else 0
                    real_percent = df_mes_selecionado["Real %"].mean() if "Real %" in df_ano.columns else 0

                    st.markdown("#### Informações do mês selecionado")
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    with col_m1:
                        st.metric("💰 Vendas", moeda(vendas), delta=None)
                    with col_m2:
                        st.metric("⚠️ Quebra Ident.", moeda(quebra_ident), delta=None)
                    with col_m3:
                        st.metric("⚠️ Quebra Não Ident.", moeda(quebra_nao_ident), delta=None)
                    with col_m4:
                        st.metric("📌 Quebra Final", moeda(quebra_final), delta=None)

                    st.markdown("---")
                    c5, c6 = st.columns(2)
                    with c5:
                        st.metric("🎯 Meta %", f"{meta_percent:.2f}%", delta=None)
                    with c6:
                        st.metric("✅ Real %", f"{real_percent:.2f}%", delta=None)

                    st.markdown("---")
                    if not df_mes_selecionado.empty:
                        st.markdown("##### Detalhes do mês selecionado")
                        st.dataframe(df_mes_selecionado.reset_index(drop=True), use_container_width=True)
                    else:
                        st.info("Nenhum registro encontrado para o mês selecionado.")

                    meses_dados = []
                    for mes in MESES_ORDEM:
                        df_mes = df_ano[df_ano["mes_nome"] == mes]
                        meses_dados.append({
                            "Mês": mes,
                            "Vendas": df_mes["Vendas"].apply(limpar_valor_monetario).sum() if "Vendas" in df.columns else 0,
                            "Quebra Ident.": df_mes["Quebra Ident."].apply(limpar_valor_monetario).sum() if "Quebra Ident." in df.columns else 0,
                            "Quebra Não Ident.": df_mes["Quebra Não Ident."].apply(limpar_valor_monetario).sum() if "Quebra Não Ident." in df.columns else 0,
                            "Quebra FINAL": df_mes["Quebra FINAL"].apply(limpar_valor_monetario).sum() if "Quebra FINAL" in df.columns else 0,
                        })

                    df_meses = pd.DataFrame(meses_dados)
                    df_meses["Mês"] = pd.Categorical(df_meses["Mês"], categories=MESES_ORDEM, ordered=True)
                    df_meses = df_meses.sort_values("Mês")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("💰 Total Vendas", moeda(df_meses["Vendas"].sum()), delta=None)
                    with col2:
                        st.metric("⚠️ Quebra Final", moeda(df_meses["Quebra FINAL"].sum()), delta=None)
                    with col3:
                        st.metric("📊 Média Vendas", moeda(df_meses["Vendas"].mean()), delta=None)

                    st.markdown("---")
                    st.markdown("#### Detalhamento por mês")

                    df_display = df_meses.copy()
                    df_display["Vendas"] = df_display["Vendas"].apply(moeda)
                    df_display["Quebra Ident."] = df_display["Quebra Ident."].apply(moeda)
                    df_display["Quebra Não Ident."] = df_display["Quebra Não Ident."].apply(moeda)
                    df_display["Quebra FINAL"] = df_display["Quebra FINAL"].apply(moeda)
                    st.dataframe(df_display.set_index("Mês"), use_container_width=True)

                    st.markdown("---")
                    st.markdown("#### Gráficos por mês")
                    g1, g2 = st.columns(2)
                    with g1:
                        st.markdown("**💰 Vendas por mês**")
                        # Plotly bar chart com formatação de moeda (pt-BR)
                        import numpy as _np

                        vals = df_meses.set_index("Mês")["Vendas"].values.tolist()
                        months = df_meses.set_index("Mês").index.tolist()
                        formatted = [moeda(v) for v in vals]

                        bar_fig = go.Figure(go.Bar(
                            x=months,
                            y=vals,
                            marker_color='#2b8cbe',
                            customdata=formatted,
                            hovertemplate='<b>%{x}</b><br>Vendas: %{customdata}<extra></extra>',
                            text=formatted,
                            textposition='auto'
                        ))

                        maxv = max(vals) if vals else 0
                        tick_vals = _np.linspace(0, maxv, num=5).tolist() if maxv > 0 else [0]
                        tick_text = [moeda(tv) for tv in tick_vals]

                        bar_fig.update_layout(
                            height=420,
                            margin=dict(t=10, b=40, l=80, r=20),
                            yaxis=dict(tickmode='array', tickvals=tick_vals, ticktext=tick_text, title='R$')
                        )

                        st.plotly_chart(bar_fig, use_container_width=True)
                    with g2:
                        st.markdown("**🎯 Meta % vs Real %**")

                        if "Meta %" in df_ano.columns and "Real %" in df_ano.columns:

                            meta_real = df_ano[["mes_nome", "Meta %", "Real %"]].copy()

                            meta_real = (
                                meta_real
                                .groupby("mes_nome")[["Meta %", "Real %"]]
                                .mean()
                            )

                            # Ordena obrigatoriamente Janeiro até Dezembro
                            meta_real = meta_real.reindex(MESES_ORDEM)

                            # Meses sem informação ficam zerados
                            meta_real = meta_real.fillna(0)

                            meta_real.index.name = "Mês"

                            # Criar gráfico Plotly com melhor visualização
                            fig = go.Figure()
                            
                            # Adicionar linha de Meta %
                            fig.add_trace(go.Scatter(
                                x=meta_real.index,
                                y=meta_real['Meta %'],
                                mode='lines+markers+text',
                                name='Meta %',
                                line=dict(color='#1f77b4', width=3),
                                marker=dict(size=8),
                                text=[f"{val:.2f}%" for val in meta_real['Meta %']],
                                textposition="top center",
                                hovertemplate='<b>%{x}</b><br>Meta: %{y:.2f}%<extra></extra>'
                            ))
                            
                            # Adicionar linha de Real % com marcadores vermelhos quando acima da Meta %
                            months = list(meta_real.index)
                            meta_vals = list(meta_real['Meta %'])
                            real_vals = list(meta_real['Real %'])

                            # Linha contínua para Real %
                            fig.add_trace(go.Scatter(
                                x=months,
                                y=real_vals,
                                mode='lines',
                                name='Real %',
                                line=dict(color='#ff7f0e', width=3),
                                hoverinfo='skip'
                            ))

                            def _is_bad(r, m):
                                try:
                                    if r is None or m is None:
                                        return False
                                    return (m >= 0 and r > m) or (m < 0 and r < m)
                                except Exception:
                                    return False

                            # Marcadores para pontos considerados ruins
                            above_y = [r if _is_bad(r, m) else None for r, m in zip(real_vals, meta_vals)]
                            above_text = [f"{v:.2f}%" if _is_bad(v, m) else "" for v, m in zip(real_vals, meta_vals)]
                            fig.add_trace(go.Scatter(
                                x=months,
                                y=above_y,
                                mode='markers+text',
                                name='Real % (fora da Meta)',
                                marker=dict(size=10, color='red'),
                                text=above_text,
                                textposition='bottom center',
                                textfont=dict(color='red'),
                                hovertemplate='<b>%{x}</b><br>Real: %{y:.2f}%<br>Meta: %{customdata:.2f}%<extra></extra>',
                                customdata=[m if _is_bad(r, m) else None for r, m in zip(real_vals, meta_vals)]
                            ))

                            # Marcadores para pontos dentro do limite (não ruins)
                            below_y = [r if (r is not None and not _is_bad(r, m)) else None for r, m in zip(real_vals, meta_vals)]
                            below_text = [f"{v:.2f}%" if (v is not None and not _is_bad(v, m)) else "" for v, m in zip(real_vals, meta_vals)]
                            fig.add_trace(go.Scatter(
                                x=months,
                                y=below_y,
                                mode='markers+text',
                                name='Real % (dentro da Meta)',
                                marker=dict(size=8, color='#ff7f0e'),
                                text=below_text,
                                textposition='bottom center',
                                textfont=dict(color='#8a3b00'),
                                hovertemplate='<b>%{x}</b><br>Real: %{y:.2f}%<br>Meta: %{customdata:.2f}%<extra></extra>',
                                customdata=[m if (r is not None and not _is_bad(r, m)) else None for r, m in zip(real_vals, meta_vals)]
                            ))
                            
                            # Customizar layout
                            fig.update_layout(
                                height=400,
                                hovermode='x unified',
                                title=None,
                                xaxis_title="Mês",
                                yaxis_title="Percentual (%)",
                                font=dict(size=11),
                                plot_bgcolor='rgba(240,240,240,0.5)',
                                margin=dict(t=40, b=40, l=60, r=60),
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=1.02,
                                    xanchor="right",
                                    x=1
                                )
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)

                        else:
                            st.info("Meta % ou Real % não estão disponíveis nos dados para gerar o gráfico.")

                    # with g2:
                    #     st.markdown("**🎯 Meta % vs Real %**")
                    #     if "Meta %" in df_ano.columns and "Real %" in df_ano.columns:
                        #     meta_real = df_ano[["mes_nome", "Meta %", "Real %"]].copy()
                        #     meta_real = meta_real.dropna(subset=["mes_nome"])
                        #     meta_real = meta_real.groupby("mes_nome", sort=False).mean()
                        #     meta_real = meta_real.reindex(MESES_ORDEM)
                        #     meta_real.index.name = "Mês"
                        #     meta_real = meta_real.fillna(0)
                        #     if not meta_real.empty:
                        #         st.line_chart(meta_real)
                        #     else:
                        #         st.info("Não há dados de Meta % e Real % para o ano selecionado.")
                        # else:
                        #     st.info("Meta % ou Real % não estão disponíveis nos dados para gerar o gráfico.")
                else:
                    st.info("Nenhum ano válido encontrado nos dados para fazer o filtro.")
            else:
                st.info("Os dados carregados precisam ter as colunas 'ano' e 'mes' para mostrar o resumo mensal.")
        else:
            st.warning("Os dados da planilha não contêm registros válidos para a análise mensal.")

    st.markdown("---")
    st.markdown("## 📊 QB_ID: custo por categoria")
    qb_raw = fetch_qb_id(URL)
    if isinstance(qb_raw, dict) and "error" in qb_raw:
        st.warning(f"Não foi possível carregar os dados de QB_ID: {qb_raw['error']}")
    elif not qb_raw:
        st.info("Nenhum dado encontrado na aba QB_ID.")
    else:
        if isinstance(qb_raw, dict):
            qb_raw = [qb_raw]

        try:
            df_qb = pd.DataFrame(qb_raw)
        except Exception as e:
            st.error(f"Erro ao criar tabela de QB_ID: {e}")
            df_qb = pd.DataFrame()

        if not df_qb.empty:
            df_qb.columns = df_qb.columns.str.strip()
            ano_col = find_column(df_qb, ["ano", "year"])
            mes_col = find_column(df_qb, ["mes", "month"])
            categoria_col = find_column(df_qb, ["categoria", "category", "Categoria"])
            custo_col = find_column(df_qb, ["CUSTO", "custo", "Custo", "valor", "Valor"])

            if ano_col is not None:
                df_qb[ano_col] = pd.to_numeric(df_qb[ano_col], errors="coerce")
            if mes_col is not None:
                df_qb[mes_col] = df_qb[mes_col].astype(str).str.strip()
                df_qb["mes_nome_qb"] = df_qb[mes_col].apply(normalizar_mes)
                df_qb["mes_nome_qb"] = pd.Categorical(df_qb["mes_nome_qb"], categories=MESES_ORDEM, ordered=True)
            else:
                df_qb["mes_nome_qb"] = ""

            if custo_col is not None:
                df_qb["custo_valor"] = df_qb[custo_col].apply(limpar_valor_monetario)
            else:
                df_qb["custo_valor"] = 0

            if categoria_col is None:
                df_qb["categoria_norm"] = "Sem categoria"
                categoria_col = "categoria_norm"

            anos_disponiveis_qb = sorted(df_qb[ano_col].dropna().unique()) if ano_col is not None else []
            meses_disponiveis_qb = [mes for mes in MESES_ORDEM if mes in df_qb["mes_nome_qb"].dropna().unique()]

            if anos_disponiveis_qb:
                agora = datetime.now(pytz.timezone("America/Sao_Paulo"))
                ano_atual = agora.year
                ano_index = anos_disponiveis_qb.index(ano_atual) if ano_atual in anos_disponiveis_qb else 0
                ano_selecionado_qb = st.selectbox("Filtrar QB_ID por ano:", anos_disponiveis_qb, index=ano_index, key="qb_id_ano")
            else:
                ano_selecionado_qb = None

            if meses_disponiveis_qb:
                mes_atual = MESES_ORDEM[datetime.now(pytz.timezone("America/Sao_Paulo")).month - 1]
                mes_index = meses_disponiveis_qb.index(mes_atual) if mes_atual in meses_disponiveis_qb else 0
                mes_selecionado_qb = st.selectbox("Filtrar QB_ID por mês:", meses_disponiveis_qb, index=mes_index, key="qb_id_mes")
            else:
                mes_selecionado_qb = None

            df_qb_filtrado = df_qb.copy()
            if ano_selecionado_qb is not None and ano_col is not None:
                df_qb_filtrado = df_qb_filtrado[df_qb_filtrado[ano_col] == ano_selecionado_qb]
            if mes_selecionado_qb is not None and mes_col is not None:
                df_qb_filtrado = df_qb_filtrado[df_qb_filtrado["mes_nome_qb"] == mes_selecionado_qb]

            df_qb_filtrado[categoria_col] = df_qb_filtrado[categoria_col].fillna("Sem categoria")
            resumo_cat = (
                df_qb_filtrado
                .groupby(categoria_col, dropna=False)["custo_valor"]
                .sum()
                .reset_index()
                .sort_values("custo_valor", ascending=False)
            )

            total_custos = resumo_cat["custo_valor"].sum()
            st.metric("Total CUSTO", moeda(total_custos), delta=None)
            st.markdown("##### Custo por categoria")
            if not resumo_cat.empty:
                resumo_cat_display = resumo_cat.copy()
                resumo_cat_display["Custo"] = resumo_cat_display["custo_valor"].apply(moeda)
                resumo_cat_display = resumo_cat_display.drop(columns=["custo_valor"])
                resumo_cat_display = resumo_cat_display.rename(columns={categoria_col: "Categoria"})
                st.dataframe(resumo_cat_display.reset_index(drop=True), use_container_width=True)
            else:
                st.info("Nenhum registro de QB_ID encontrado para os filtros aplicados.")
        else:
            st.info("Os dados da aba QB_ID não contêm registros válidos.")


if __name__ == "__main__":
    render(URL)


import streamlit as st
import requests
import pandas as pd
import pytz
from datetime import datetime
import plotly.graph_objects as go

MESES_ORDEM = [
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
]


def moeda(valor):
    try:
        valor = float(valor)
    except Exception:
        return "R$ 0,00"

    sinal = "-" if valor < 0 else ""
    valor_abs = abs(valor)
    texto = f"{valor_abs:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{sinal}R$ {texto}"


def limpar_valor(v):
    if pd.isna(v) or v == "" or v == "-" or v == "R$ -":
        return 0.0
    if isinstance(v, str):
        texto = v.strip().replace("R$", "").replace("%", "").replace(".", "").replace(",", ".")
        texto = texto.replace(" ", "")
        if texto == "":
            return 0.0
        try:
            return float(texto)
        except Exception:
            return 0.0
    try:
        return float(v)
    except Exception:
        return 0.0


def normalizar_mes(valor):
    if pd.isna(valor):
        return ""
    texto = str(valor).strip()
    if texto.isdigit():
        idx = int(texto)
        if 1 <= idx <= 12:
            return MESES_ORDEM[idx - 1]
    texto_lower = texto.lower()
    for mes in MESES_ORDEM:
        if texto_lower == mes.lower() or texto_lower.startswith(mes[:3].lower()):
            return mes
    return texto.title()


def fetch_dados(URL):
    try:
        url_com_param = f"{URL}?tipo_registro=dados&_ts={int(datetime.now().timestamp())}"
        response = requests.get(url_com_param, headers={"Cache-Control": "no-cache"}, timeout=12)
        response.raise_for_status()
        return response.json()
    except Exception as error:
        return {"error": str(error), "url": URL}


def render(URL):
    st.title("📊 Quebra Venda")
    st.write("Visualização da aba `dados` do Google Sheets. Use os filtros para ajustar o ano e o mês.")

    dados_raw = fetch_dados(URL)
    if isinstance(dados_raw, dict) and "error" in dados_raw:
        st.error(f"Não foi possível carregar os dados: {dados_raw['error']}")
        return

    if not dados_raw:
        st.warning("Nenhum dado retornado pela aba dados.")
        return

    if isinstance(dados_raw, dict):
        dados_raw = [dados_raw]

    try:
        df = pd.DataFrame(dados_raw)
    except Exception as error:
        st.error(f"Erro ao montar o DataFrame: {error}")
        return

    if df.empty:
        st.warning("A tabela de dados está vazia.")
        return

    # Normaliza colunas para evitar problemas com espaços ou letras maiúsculas
    df.columns = df.columns.str.strip()
    colunas = {col.lower(): col for col in df.columns}

    if "ano" not in colunas or "mes" not in colunas:
        st.warning("A planilha precisa conter as colunas 'ano' e 'mes' para filtragem por período.")
        return

    df_ano = df.rename(columns={
        colunas["ano"]: "ano",
        colunas["mes"]: "mes",
    })

    if "vendas" in colunas:
        df_ano = df_ano.rename(columns={colunas["vendas"]: "Vendas"})
    if "quebra ident." in colunas:
        df_ano = df_ano.rename(columns={colunas["quebra ident."]: "Quebra Ident."})
    if "quebra não ident." in colunas:
        df_ano = df_ano.rename(columns={colunas["quebra não ident."]: "Quebra Não Ident."})
    if "quebra final" in colunas:
        df_ano = df_ano.rename(columns={colunas["quebra final"]: "Quebra FINAL"})
    if "meta %" in colunas:
        df_ano = df_ano.rename(columns={colunas["meta %"]: "Meta %"})
    if "real %" in colunas:
        df_ano = df_ano.rename(columns={colunas["real %"]: "Real %"})

    df_ano["ano"] = pd.to_numeric(df_ano["ano"], errors="coerce")
    df_ano = df_ano[df_ano["ano"].notna()].copy()

    if df_ano.empty:
        st.warning("Nenhum registro com ano válido encontrado.")
        return

    df_ano["mes_nome"] = df_ano["mes"].apply(normalizar_mes)
    df_ano["mes_nome"] = pd.Categorical(df_ano["mes_nome"], categories=MESES_ORDEM, ordered=True)

    anos_disponiveis = sorted(df_ano["ano"].dropna().unique().astype(int).tolist())
    ano_atual = datetime.now(pytz.timezone("America/Sao_Paulo")).year
    ano_index = anos_disponiveis.index(ano_atual) if ano_atual in anos_disponiveis else 0
    ano_selecionado = st.selectbox("Ano", anos_disponiveis, index=ano_index, key="quebra_venda_ano")

    df_filtrado = df_ano[df_ano["ano"] == ano_selecionado].copy()
    meses_disponiveis = [mes for mes in MESES_ORDEM if mes in df_filtrado["mes_nome"].dropna().unique()]
    if not meses_disponiveis:
        meses_disponiveis = [mes for mes in MESES_ORDEM if mes in df_ano["mes_nome"].dropna().unique()]
    mes_atual = MESES_ORDEM[datetime.now(pytz.timezone("America/Sao_Paulo")).month - 1]
    mes_index = meses_disponiveis.index(mes_atual) if mes_atual in meses_disponiveis else 0
    mes_selecionado = st.selectbox("Mês", meses_disponiveis, index=mes_index, key="quebra_venda_mes")

    df_mes = df_filtrado[df_filtrado["mes_nome"] == mes_selecionado].copy()

    vendas_mes = df_mes["Vendas"].apply(limpar_valor).sum() if "Vendas" in df_mes.columns else 0.0
    quebra_ident = df_mes["Quebra Ident."].apply(limpar_valor).sum() if "Quebra Ident." in df_mes.columns else 0.0
    quebra_nao_ident = df_mes["Quebra Não Ident."].apply(limpar_valor).sum() if "Quebra Não Ident." in df_mes.columns else 0.0
    quebra_final = df_mes["Quebra FINAL"].apply(limpar_valor).sum() if "Quebra FINAL" in df_mes.columns else 0.0

    meta_percent = 0.0
    real_percent = 0.0
    if "Meta %" in df_mes.columns:
        meta_percent = df_mes["Meta %"].apply(limpar_valor).mean()
    if "Real %" in df_mes.columns:
        real_percent = df_mes["Real %"].apply(limpar_valor).mean()

    meta_real_diff = None
    if meta_percent and real_percent:
        meta_real_diff = real_percent - meta_percent

    st.markdown("### Resultado do mês selecionado")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Vendas", moeda(vendas_mes))
    col2.metric("Quebra Ident.", moeda(quebra_ident))
    col3.metric("Quebra Não Ident.", moeda(quebra_nao_ident))
    col4.metric("Quebra FINAL", moeda(quebra_final))

    st.markdown("---")
    col5, col6, col7 = st.columns(3)
    col5.metric("Meta %", f"{meta_percent:.2f}%")
    col6.metric("Real %", f"{real_percent:.2f}%")
    if meta_real_diff is not None:
        col7.metric("Desvio Real vs Meta", f"{meta_real_diff:+.2f}%")
    else:
        col7.write("&nbsp;")

    st.markdown("---")
    st.markdown("#### Tabela de dados do mês")
    if df_mes.empty:
        st.info("Não há registros para o mês selecionado.")
    else:
        df_visual = df_mes.copy()
        df_visual = df_visual.drop(columns=[c for c in ["mes_nome"] if c in df_visual.columns])
        st.dataframe(df_visual.reset_index(drop=True), use_container_width=True)

    st.markdown("---")
    st.markdown("#### Evolução por mês no ano selecionado")

    resumo = []
    for mes in MESES_ORDEM:
        df_temp = df_filtrado[df_filtrado["mes_nome"] == mes]
        resumo.append({
            "Mês": mes,
            "Vendas": df_temp["Vendas"].apply(limpar_valor).sum() if "Vendas" in df_temp.columns else 0.0,
            "Quebra FINAL": df_temp["Quebra FINAL"].apply(limpar_valor).sum() if "Quebra FINAL" in df_temp.columns else 0.0,
            "Meta %": df_temp["Meta %"].apply(limpar_valor).mean() if "Meta %" in df_temp.columns else 0.0,
            "Real %": df_temp["Real %"].apply(limpar_valor).mean() if "Real %" in df_temp.columns else 0.0,
        })

    df_resumo = pd.DataFrame(resumo)
    df_resumo["Mês"] = pd.Categorical(df_resumo["Mês"], categories=MESES_ORDEM, ordered=True)
    df_resumo = df_resumo.sort_values("Mês")

    if not df_resumo.empty:
        grafico_vendas = df_resumo.set_index("Mês")["Vendas"]
        grafico_meta_real = df_resumo.set_index("Mês")[['Meta %', 'Real %']]

        graf1, graf2 = st.columns(2)
        with graf1:
            st.markdown("**Vendas por mês**")
            # Plotly bar chart com formatação de moeda (pt-BR)
            import numpy as _np

            vals = grafico_vendas.values.tolist()
            months = grafico_vendas.index.tolist()
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

            # Gerar ticks legíveis e formatados em R$
            maxv = max(vals) if vals else 0
            tick_vals = _np.linspace(0, maxv, num=5).tolist() if maxv > 0 else [0]
            tick_text = [moeda(tv) for tv in tick_vals]

            bar_fig.update_layout(
                height=420,
                margin=dict(t=10, b=40, l=80, r=20),
                yaxis=dict(tickmode='array', tickvals=tick_vals, ticktext=tick_text, title='R$')
            )

            st.plotly_chart(bar_fig, use_container_width=True)
        with graf2:
            st.markdown("**Meta % vs Real %**")
            if grafico_meta_real[['Meta %', 'Real %']].sum().sum() != 0:
                # Criar gráfico Plotly com melhor visualização
                fig = go.Figure()
                
                # Adicionar linha de Meta %
                fig.add_trace(go.Scatter(
                    x=grafico_meta_real.index,
                    y=grafico_meta_real['Meta %'],
                    mode='lines+markers+text',
                    name='Meta %',
                    line=dict(color='#1f77b4', width=3),
                    marker=dict(size=8),
                    text=[f"{val:.2f}%" for val in grafico_meta_real['Meta %']],
                    textposition="top center",
                    hovertemplate='<b>%{x}</b><br>Meta: %{y:.2f}%<extra></extra>'
                ))
                
                # Adicionar linha de Real % com marcadores vermelhos quando acima da Meta %
                months = list(grafico_meta_real.index)
                meta_vals = list(grafico_meta_real['Meta %'])
                real_vals = list(grafico_meta_real['Real %'])

                # Linha contínua para Real % (sem marcadores para permitir marcadores separados)
                fig.add_trace(go.Scatter(
                    x=months,
                    y=real_vals,
                    mode='lines',
                    name='Real %',
                    line=dict(color='#ff7f0e', width=3),
                    hoverinfo='skip'
                ))

                # Marcadores para pontos acima da meta (vermelhos)
                def _is_bad(r, m):
                    try:
                        if r is None or m is None:
                            return False
                        # se meta >= 0, maior que meta é pior; se meta < 0, menor que meta é pior
                        return (m >= 0 and r > m) or (m < 0 and r < m)
                    except Exception:
                        return False

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
                st.info("Não há dados suficientes de Meta % / Real % para gráfico neste ano.")

    st.markdown("#### Dados brutos da aba dados")
    df_ano_exibir = df_filtrado.copy()
    df_ano_exibir["mes_nome"] = df_ano_exibir["mes_nome"].astype(str)
    st.dataframe(df_ano_exibir.reset_index(drop=True), use_container_width=True)

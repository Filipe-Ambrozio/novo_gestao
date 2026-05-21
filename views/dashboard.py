import streamlit as st
import requests
import pandas as pd
import pytz
from datetime import datetime


def moeda(v):
    """Formata valor em moeda brasileira"""
    try:
        num = float(v) if v else 0
        return f"R$ {num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(v)


def fetch_dados(URL):
    """Busca dados da aba 'dados' do Google Sheets"""
    try:
        # Construir URL com parâmetro
        url_com_param = f"{URL}?tipo_registro=dados&_ts={datetime.now().timestamp()}"
        st.write(f"🔗 Requisição: {url_com_param[:100]}...")
        
        response = requests.get(
            url_com_param,
            headers={"Cache-Control": "no-cache"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        st.write(f"✅ Resposta recebida: {type(data)} com {len(data) if isinstance(data, (list, dict)) else 'N/A'} itens")
        return data
    except Exception as error:
        st.error(f"❌ Erro ao carregar dados: {error}")
        st.write(f"URL: {URL}")
        return []


def render(URL):
    st.title("📊 Dashboard - Análise de Dados")
    
    # Buscar dados
    dados_raw = fetch_dados(URL)
    
    # Verificar se há erro
    if isinstance(dados_raw, dict) and 'error' in dados_raw:
        st.error(f"❌ Erro: {dados_raw['error']}")
        return
    
    if not dados_raw:
        st.warning("⚠️ Nenhum dado encontrado na planilha.")
        return
    
    # Garantir que é uma lista
    if isinstance(dados_raw, dict):
        dados_raw = [dados_raw]
    
    # Converter para DataFrame
    try:
        df = pd.DataFrame(dados_raw)
    except Exception as e:
        st.error(f"❌ Erro ao converter dados: {e}")
        return
    
    # Normalizar colunas
    df.columns = df.columns.str.strip()
    
    st.success(f"✅ Dados carregados: {len(df)} registros")
    
    # Mostrar dados brutos para debug
    with st.expander("📂 Dados Brutos (Debug)"):
        st.dataframe(df, use_container_width=True)
        st.write(f"Tipos de dados: {df.dtypes.to_dict()}")
    
    # Função para limpar valores monetários
    def limpar_valor_monetario(v):
        if pd.isna(v) or v == '' or v == '-' or v == 'R$ -':
            return 0
        try:
            # Se for string, remove "R$" e espaços
            if isinstance(v, str):
                # Preservar o sinal negativo
                eh_negativo = '-' in v
                v = v.replace('R$', '').replace('-', '').replace('.', '').replace(',', '.').strip()
                num = float(v) if v else 0
                return -num if eh_negativo else num
            return float(v)
        except:
            return 0
    
    # Converter colunas numéricas
    numeric_cols = ["Vendas", "Quebra Inicial", "Quebra Ident.", "Quebra Não Ident.", 
                    "Quebra FINAL", "CONTRATOS", "ACORDOS", "TOTAL RECEITAS", 
                    "REVERSÃO", "Real %", "Meta %"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(limpar_valor_monetario)
    
    # Converter colunas de data/ano/mes
    if "ano" in df.columns:
        df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    
    if "mes" in df.columns:
        df["mes"] = df["mes"].astype(str).str.strip()
    
    # Remover linhas com ano vazio
    if "ano" in df.columns:
        df = df[df["ano"].notna()]
    
    st.divider()
    
    # ═══════════════════════════════════════════════════════════════════
    # SEÇÃO PRINCIPAL: ANÁLISE POR MÊS E ANO (PARA APRESENTAÇÃO)
    # ═══════════════════════════════════════════════════════════════════
    st.markdown(
        "<h2 style='text-align: center; font-size: 28px; color: #1f77b4;'>📅 Dados por Mês e Ano</h2>",
        unsafe_allow_html=True
    )
    
    if "ano" in df.columns and "mes" in df.columns:
        # Permitir filtro por ano
        anos_disponiveis = sorted(df["ano"].dropna().unique())
        ano_selecionado = st.selectbox("Selecione o Ano:", anos_disponiveis, key="ano_filtro")
        
        df_ano_filtrado = df[df["ano"] == ano_selecionado]
        
        df_ano_filtrado = df_ano_filtrado.copy()
        df_ano_filtrado["mes_nome"] = df_ano_filtrado["mes"].astype(str).str.strip()
        
        # Criar tabela consolidada por mês
        meses_dados = []
        meses_ordem = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                       "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        
        for mes in meses_ordem:
            df_mes = df_ano_filtrado[df_ano_filtrado["mes_nome"] == mes]
            
            # Incluir o mês mesmo que esteja vazio
            meses_dados.append({
                "Mês": mes,
                "Vendas": df_mes["Vendas"].sum() if "Vendas" in df.columns and not df_mes.empty else 0,
                "Quebra Ident.": df_mes["Quebra Ident."].sum() if "Quebra Ident." in df.columns and not df_mes.empty else 0,
                "Quebra Não Ident.": df_mes["Quebra Não Ident."].sum() if "Quebra Não Ident." in df.columns and not df_mes.empty else 0,
                "Quebra FINAL": df_mes["Quebra FINAL"].sum() if "Quebra FINAL" in df.columns and not df_mes.empty else 0,
                "Contratos": df_mes["CONTRATOS"].sum() if "CONTRATOS" in df.columns and not df_mes.empty else 0,
                "Acordos": df_mes["ACORDOS"].sum() if "ACORDOS" in df.columns and not df_mes.empty else 0,
                "Total Receitas": df_mes["TOTAL RECEITAS"].sum() if "TOTAL RECEITAS" in df.columns and not df_mes.empty else 0,
            })
        
        if meses_dados:
            df_meses = pd.DataFrame(meses_dados)
            
            # Definir ordem dos meses como categoria para manter ordem nos gráficos
            meses_ordem = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                           "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            df_meses["Mês"] = pd.Categorical(df_meses["Mês"], categories=meses_ordem, ordered=True)
            df_meses = df_meses.sort_values("Mês")
            
            # Formatação com fontes maiores para apresentação
            st.markdown(f"<h3 style='font-size: 20px; color: #333;'>Ano: {int(ano_selecionado)}</h3>", unsafe_allow_html=True)
            
            # Mostrar métricas principais em destaque
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                vendas_total = df_meses["Vendas"].sum()
                st.metric("💰 Total Vendas", moeda(vendas_total), delta=None, label_visibility="visible")
            with col2:
                quebra_total = df_meses["Quebra FINAL"].sum()
                st.metric("⚠️ Quebra Final", moeda(quebra_total), delta=None, label_visibility="visible")
            with col3:
                receita_total = df_meses["Total Receitas"].sum()
                st.metric("💵 Total Receitas", moeda(receita_total), delta=None, label_visibility="visible")
            with col4:
                media_vendas = df_meses["Vendas"].mean()
                st.metric("📊 Média Vendas", moeda(media_vendas), delta=None, label_visibility="visible")
            
            st.markdown("---")
            
            # Tabela formatada com fontes maiores
            st.markdown("<h4 style='font-size: 18px;'>Detalhamento por Mês</h4>", unsafe_allow_html=True)
            
            # Criar DataFrame formatado para exibição
            df_display = df_meses.copy()
            df_display["Vendas"] = df_display["Vendas"].apply(moeda)
            df_display["Quebra Ident."] = df_display["Quebra Ident."].apply(moeda)
            df_display["Quebra Não Ident."] = df_display["Quebra Não Ident."].apply(moeda)
            df_display["Quebra FINAL"] = df_display["Quebra FINAL"].apply(moeda)
            df_display["Contratos"] = df_display["Contratos"].apply(moeda)
            df_display["Acordos"] = df_display["Acordos"].apply(moeda)
            df_display["Total Receitas"] = df_display["Total Receitas"].apply(moeda)
            
            df_display = df_display.set_index("Mês")
            
            # Exibir com configuração de fonte média
            st.dataframe(
                df_display,
                use_container_width=True,
                height=None
            )
            
            # Gráficos por mês
            st.markdown("---")
            st.markdown("<h4 style='font-size: 18px;'>Visualização Gráfica</h4>", unsafe_allow_html=True)
            
            # Gráficos em 2 colunas
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown("<p style='font-size: 16px; font-weight: bold;'>💰 Vendas por Mês</p>", unsafe_allow_html=True)
                st.bar_chart(df_meses.set_index("Mês")["Vendas"], use_container_width=True)
            
            with col_chart2:
                st.markdown("<p style='font-size: 16px; font-weight: bold;'>⚠️ Quebras por Mês</p>", unsafe_allow_html=True)
                st.line_chart(df_meses.set_index("Mês")[["Quebra FINAL", "Quebra Ident.", "Quebra Não Ident."]], use_container_width=True)
            
            st.divider()
            
            # Gráfico adicional: Meta Real % vs Meta %
            col_chart3, col_chart4 = st.columns(2)
            
            with col_chart3:
                st.markdown("<p style='font-size: 16px; font-weight: bold;'>📊 Meta Real % vs Meta % por Mês</p>", unsafe_allow_html=True)
                # Preparar dados para o gráfico de metas
                df_metas = df_ano_filtrado[["mes", "Real %", "Meta %"]].copy()
                df_metas["mes"] = pd.Categorical(df_metas["mes"], categories=meses_ordem, ordered=True)
                df_metas = df_metas.sort_values("mes")
                if not df_metas.empty:
                    st.line_chart(df_metas.set_index("mes")[["Real %", "Meta %"]], use_container_width=True)
                else:
                    st.info("Nenhum dado de metas disponível para este período")
            
            with col_chart4:
                st.markdown("<p style='font-size: 16px; font-weight: bold;'>💵 Receitas vs Contratos/Acordos</p>", unsafe_allow_html=True)
                df_fin = df_meses.set_index("Mês")[["Total Receitas", "Contratos", "Acordos"]].copy()
                st.bar_chart(df_fin, use_container_width=True)
    
    st.divider()
    st.divider()
    
    # ═══════════════════════════════════════════════════════════════════
    # SEÇÃO DE ANÁLISE: RESUMOS ANUAIS
    # ═══════════════════════════════════════════════════════════════════
    st.markdown(
        "<h2 style='text-align: center; font-size: 28px; color: #2ca02c;'>📈 Análise Anual</h2>",
        unsafe_allow_html=True
    )
    
    # TAB 1: Vendas por Ano
    st.markdown("<h3 style='font-size: 20px;'>💰 Vendas por Ano</h3>", unsafe_allow_html=True)
    if "ano" in df.columns and "Vendas" in df.columns:
        vendas_ano = df.groupby("ano")["Vendas"].sum().sort_index()
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.bar_chart(vendas_ano)
        with col2:
            vendas_table = pd.DataFrame({
                "Ano": vendas_ano.index.astype(int),
                "Total": vendas_ano.apply(moeda)
            }).set_index("Ano")
            st.dataframe(vendas_table, use_container_width=True)
    
    st.divider()
    
    # TAB 2: Quebras por Tipo e Ano
    st.markdown("<h3 style='font-size: 20px;'>⚠️ Análise de Quebras por Tipo</h3>", unsafe_allow_html=True)
    
    quebra_cols = ["Quebra Ident.", "Quebra Não Ident.", "Quebra FINAL"]
    quebra_exists = [col for col in quebra_cols if col in df.columns]
    
    if quebra_exists and "ano" in df.columns:
        quebras_ano = df.groupby("ano")[quebra_exists].sum().sort_index()
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.bar_chart(quebras_ano)
        with col2:
            st.dataframe(quebras_ano.astype(str), use_container_width=True)
    
    st.divider()
    
    # TAB 3: Quebra Final por Ano e Mês
    st.markdown("<h3 style='font-size: 20px;'>📌 Quebra FINAL - Evolução</h3>", unsafe_allow_html=True)
    if "ano" in df.columns and "Quebra FINAL" in df.columns:
        # Por ano
        quebra_final_ano = df.groupby("ano")["Quebra FINAL"].sum().sort_index()
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.line_chart(quebra_final_ano)
        with col2:
            tabela_qfinal = pd.DataFrame({
                "Ano": quebra_final_ano.index.astype(int),
                "Quebra Final": quebra_final_ano.apply(moeda)
            }).set_index("Ano")
            st.dataframe(tabela_qfinal, use_container_width=True)
    
    st.divider()
    
    # TAB 4: Meta Real vs Meta (Inventário)
    st.markdown("<h3 style='font-size: 20px;'>🎯 Meta Real vs Meta (Inventário)</h3>", unsafe_allow_html=True)
    if "Real %" in df.columns and "Meta %" in df.columns:
        metas_compare = df[["ano", "mes", "Real %", "Meta %"]].copy()
        metas_compare = metas_compare.dropna(subset=["Real %", "Meta %"])
        
        if not metas_compare.empty:
            # Agrupar por ano
            metas_ano = df.groupby("ano")[["Real %", "Meta %"]].mean()
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.line_chart(metas_ano)
            with col2:
                metas_table = pd.DataFrame({
                    "Ano": metas_ano.index.astype(int),
                    "Real %": metas_ano["Real %"].apply(lambda x: f"{x:.2f}%"),
                    "Meta %": metas_ano["Meta %"].apply(lambda x: f"{x:.2f}%")
                }).set_index("Ano")
                st.dataframe(metas_table, use_container_width=True)
    
    st.divider()
    
    # TAB 5: Financeiro (CONTRATOS, ACORDOS, RECEITAS, REVERSÃO)
    st.markdown("<h3 style='font-size: 20px;'>💵 Análise Financeira por Ano</h3>", unsafe_allow_html=True)
    financeiro_cols = ["CONTRATOS", "ACORDOS", "TOTAL RECEITAS", "REVERSÃO"]
    financeiro_exists = [col for col in financeiro_cols if col in df.columns]
    
    if financeiro_exists and "ano" in df.columns:
        fin_ano = df.groupby("ano")[financeiro_exists].sum().sort_index()
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.bar_chart(fin_ano)
        with col2:
            # Formatar valores em moeda
            fin_display = fin_ano.copy()
            for col in fin_display.columns:
                fin_display[col] = fin_display[col].apply(moeda)
            st.dataframe(fin_display, use_container_width=True)
    
    st.divider()
    
    # TAB 6: Resumo Geral
    st.subheader("📋 Resumo Geral por Ano")
    
    if "ano" in df.columns:
        resumo_data = []
        for ano in sorted(df["ano"].dropna().unique()):
            df_ano = df[df["ano"] == ano]
            resumo_data.append({
                "Ano": int(ano),
                "Vendas": moeda(df_ano["Vendas"].sum()) if "Vendas" in df.columns else "-",
                "Quebra Ident.": moeda(df_ano["Quebra Ident."].sum()) if "Quebra Ident." in df.columns else "-",
                "Quebra Não Ident.": moeda(df_ano["Quebra Não Ident."].sum()) if "Quebra Não Ident." in df.columns else "-",
                "Quebra FINAL": moeda(df_ano["Quebra FINAL"].sum()) if "Quebra FINAL" in df.columns else "-",
                "Meta Real %": f"{df_ano['Real %'].mean():.2f}%" if "Real %" in df.columns else "-",
                "Meta %": f"{df_ano['Meta %'].mean():.2f}%" if "Meta %" in df.columns else "-",
            })
        
        resumo_df = pd.DataFrame(resumo_data).set_index("Ano")
        st.dataframe(resumo_df, use_container_width=True)
    
    st.divider()
    
    # Dados Brutos (para verificação)
    with st.expander("📂 Dados Brutos - Tabela Completa"):
        st.dataframe(df, use_container_width=True)


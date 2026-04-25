import streamlit as st
import urllib.parse
from datetime import datetime

st.set_page_config(page_title="Gestão Loja", layout="centered")

st.title("📊 Sistema de Gestão")

# =========================
# FUNÇÃO VALIDAR HORA
# =========================

def validar_hora(hora_str):
    try:
        return datetime.strptime(hora_str, "%H:%M").time()
    except:
        return None

def moeda(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# =========================
# ABAS
# =========================

aba1, aba2 = st.tabs(["📊 Gestão Diária", "🚨 Registro de Evento"])

# =========================================================
# =================== ABA 1 - GESTÃO =======================
# =========================================================

with aba1:

    st.header("📊 Gestão Diária")

    loja = st.text_input("🚟 Loja", "10 - São Lourenço", key="loja")

    data = st.date_input("📆 Data", value=datetime.now(), key="data_gestao")

    hora_str = st.text_input("⏰ Horário", datetime.now().strftime("%H:%M"), key="hora_gestao")
    hora = validar_hora(hora_str)

    if not hora:
        st.warning("Formato de hora inválido (HH:MM)")

    responsaveis = [
        "Luiz Cláudio - GS Prevenção",
        "Filipe Ambrozio - Ass - P.P",
    ]

    responsavel = st.selectbox("👤 Responsável", responsaveis, key="resp")

    if st.checkbox("Digitar outro responsável", key="check_resp"):
        responsavel = st.text_input("Digite o nome do responsável", key="resp_outro")

    st.subheader("📌 Vendas")
    venda_mes = st.number_input("Venda Acumulada (R$)", value=0.0, key="venda")
    atingimento = st.number_input("Atingimento (%)", value=0.0, key="ating")

    estoque_geral = st.number_input("Estoque Geral (R$)", value=0.0, key="estoque")

    st.subheader("⚠️ Quebras")
    quebra_pi = st.number_input("Quebra PI", value=0.0, key="pi")
    quebra_pni = st.number_input("Quebra PNI", value=0.0, key="pni")
    quebra_total = st.number_input("Quebra Total", value=0.0, key="total")

    st.subheader("💰 Financeiro")
    contratos = st.number_input("Contratos", value=0.0, key="contratos")
    acordos = st.number_input("Acordos", value=0.0, key="acordos")
    receitas = st.number_input("Receitas", value=0.0, key="receitas")
    reversao = st.number_input("Reversão (R$)", value=0.0, key="reversao")

    st.subheader("📊 Resultado")
    quebra_final = st.number_input("Quebra Final", value=0.0, key="qfinal")
    quebra_meta = st.number_input("Quebra Meta (%)", value=0.0, key="qmeta")
    quebra_realizada = st.number_input("Quebra Realizada (%)", value=0.0, key="qreal")

    estoque_troca = st.number_input("Estoque Troca", value=0.0, key="troca")
    estoque_t30 = st.number_input("Estoque +30", value=0.0, key="t30")

    # =========================
    # PRÉ-VISUALIZAÇÃO
    # =========================

    hora_final = hora.strftime('%H:%M') if hora else hora_str

    texto = f"""GESTÃO DIÁRIA

🚟 Loja: {loja}
📆 Data: {data.strftime('%d/%m/%Y')}
⏰ Horário: {hora_final}

👤 Responsável:
{responsavel}

📌 Venda Acumulada Mês
R$: {moeda(venda_mes)}

Atingimento da meta de venda {atingimento:.0f}%

Estoque Geral Loja
R$: {moeda(estoque_geral)}

Quebra PI R$: {moeda(quebra_pi)}
Quebra PNI R$: {moeda(quebra_pni)}
Quebra Total R$: {moeda(quebra_total)}

Contratos R$: {moeda(contratos)}
Acordos R$: {moeda(acordos)}
Receitas R$: {moeda(receitas)}
Reversão R$: {moeda(reversao)}

Quebra Final R$: {moeda(quebra_final)}
Quebra Meta {quebra_meta:.2f}%
Quebra Realizada {quebra_realizada:.2f}%

Estoque Troca R$: {moeda(estoque_troca)}
Estoque T +30 R$: {moeda(estoque_t30)}
"""

    st.text_area("📋 Pré-visualização", texto, height=300)

    if st.button("📤 Compartilhar Gestão", key="btn_gestao"):

        link = f"https://api.whatsapp.com/send?text={urllib.parse.quote(texto)}"

        st.success("✅ Clique abaixo para compartilhar")
        st.markdown(f"[👉 Abrir WhatsApp]({link})")


# =========================================================
# =================== ABA 2 - EVENTO =======================
# =========================================================

with aba2:

    st.header("🚨 Registro de Evento")

    data_evento = st.date_input("📆 Data", value=datetime.now(), key="data_evento")

    hora_str_evento = st.text_input("⏰ Horário", datetime.now().strftime("%H:%M"), key="hora_evento")
    hora_evento = validar_hora(hora_str_evento)

    if not hora_evento:
        st.warning("Formato inválido (HH:MM)")

    tipo = st.text_input("🚨 Tipo", key="tipo")
    filial = st.text_input("🏫 Filial", "São Lourenço", key="filial")
    local = st.text_input("📍 Local", key="local")

    st.subheader("📝 Ocorrência")
    ocorrencia = st.text_area("", height=200, key="ocorrencia")

    st.subheader("📌 Providências")
    providencias = st.text_area("", height=150, key="providencias")

    # =========================
    # PRÉ-VISUALIZAÇÃO
    # =========================

    hora_final = hora_evento.strftime('%H:%M') if hora_evento else hora_str_evento

    texto_evento = f"""REGISTRO DE EVENTO

📆 Data: {data_evento.strftime('%d/%m/%y')}
⏰ Horário: {hora_final}

🚨 Tipo: {tipo}
🏫 Filial: {filial}
📍 Local: {local}

📝 *DISCRIMINAÇÃO DA OCORRÊNCIA*
{ocorrencia}

📌 *PROVIDÊNCIAS TOMADAS*
{providencias}
"""

    st.text_area("📋 Pré-visualização", texto_evento, height=300)

    if st.button("📤 Compartilhar Evento", key="btn_evento"):

        link = f"https://api.whatsapp.com/send?text={urllib.parse.quote(texto_evento)}"

        st.success("✅ Clique abaixo para compartilhar")
        st.markdown(f"[👉 Abrir WhatsApp]({link})")

import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import urllib.parse

st.set_page_config(page_title="Sistema Loja", layout="wide")

# =========================
# MENU LATERAL
# =========================
menu = st.sidebar.radio(
    "📌 Menu",
    [
        "🌡️ Temperatura",
        "📦 Paletes",
        "📊 Dashboard",
        "📊 Gestão Diária",
        "🚨 Registro de Evento",
        "📅 Agenda"
    ]
)

# =========================
# CONFIG
# =========================
URL = "https://script.google.com/macros/s/AKfycbz8wNjzEAD8u_3vzqkEdF4CK0ArnWpX4cYtX8mJwneAK2Oj39i_Ks4hjDHCsWIzNSxKJw/exec"

# nomes = ["Luiz Cláudio", "Filipe Ambrozio", "Outro"]
nomes = ["Luiz Claudio", "Filipe Ambrozio", "Lucia", "Gennif Santana", "Jhonattan",	"Gernan", "Giovane", "Anderson", "Kesia", "Janaina Fernandes", "Sérgio Medeiros", "Josenildo Jose", "Roni Vicente", "Erick", "Daniel", "Angelo", "Alberto"]


# =========================
# SESSION STATE
# =========================
if "temp" not in st.session_state:
    st.session_state.temp = []

if "palete" not in st.session_state:
    st.session_state.palete = []

# =========================
# FUNÇÕES (FORA DOS IFs)
# =========================
def validar_hora(hora_str):
    try:
        return datetime.strptime(hora_str, "%H:%M").time()
    except:
        return None

def moeda(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def campo_valor(label, key):
    v = st.number_input(label, value=0.0, key=key)
    if v < 0:
        st.markdown("<span style='color:red'>🔴 Valor negativo</span>", unsafe_allow_html=True)
    return v


# =====================================================
# 🌡️ TEMPERATURA
# =====================================================
if menu == "🌡️ Temperatura":

    st.title("🌡️ Controle de Temperatura")

    nome = st.selectbox("Responsável", nomes)
    local = st.selectbox("Local", ["Freezer 1", "Freezer 2", "Geladeira 1", "Geladeira 2"])

    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    st.info(data_hora)

    # =========================
    # FORM (resolve o problema)
    # =========================
    with st.form("form_temp", clear_on_submit=True):

        area = st.selectbox("Área", ["Área 1", "Área 2", "Área 3"])
        temperatura = st.number_input("Temperatura (°C)", step=0.1)
        status = st.text_input("Status / Observação")

        submitted = st.form_submit_button("Adicionar")

        if submitted:
            st.session_state.temp.append({
                "tipo_registro": "temperatura",
                "data_hora": data_hora,
                "nome": nome,
                "local": local,
                "area": area,
                "temperatura": temperatura,
                "status": status
            })

            st.success("Adicionado!")

    # =========================
    # LISTA
    # =========================
    st.subheader("📋 Lista")

    for i, r in enumerate(st.session_state.temp):
        col1, col2, col3, col4, col5, col6 = st.columns([2,2,2,2,2,1])

        col1.write(r["local"])
        col2.write(r["area"])
        col3.write(f'{r["temperatura"]} °C')
        col4.write(r["status"])
        col5.write(r["nome"])

        if col6.button("❌", key=f"t{i}"):
            st.session_state.temp.pop(i)
            st.rerun()

    # =========================
    # SALVAR
    # =========================
    if st.button("💾 Salvar"):
        for r in st.session_state.temp:
            requests.post(URL, json=r)

        st.success("Salvo!")
        st.session_state.temp = []
        st.rerun()


# =====================================================
# 📦 PALETES
# =====================================================
elif menu == "📦 Paletes":

    st.title("📦 Contagem de Paletes")

    nome = st.selectbox("Responsável", nomes)
    tipo = st.selectbox("Tipo", ["CHEP", "Normal"])
    local = st.selectbox("Local", ["Loja", "Depósito"])
    quantidade = st.number_input("Quantidade", min_value=0)

    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    st.info(data_hora)

    if st.button("Adicionar"):
        st.session_state.palete.append({
            "tipo_registro": "palete",
            "data_hora": data_hora,
            "nome": nome,
            "tipo": tipo,
            "local": local,
            "quantidade": quantidade
        })
        st.success("Adicionado!")
        st.rerun()

    st.subheader("📋 Lista")

    for i, r in enumerate(st.session_state.palete):
        col1, col2, col3, col4, col5 = st.columns([2,2,2,2,1])

        col1.write(r["tipo"])
        col2.write(r["local"])
        col3.write(r["quantidade"])
        col4.write(r["nome"])

        if col5.button("❌", key=f"p{i}"):
            st.session_state.palete.pop(i)
            st.rerun()

    if st.button("💾 Salvar"):
        for r in st.session_state.palete:
            requests.post(URL, json=r)

        st.success("Salvo!")
        st.session_state.palete = []
        st.rerun()


# =====================================================
# 📊 DASHBOARD
# =====================================================
elif menu == "📊 Dashboard":

    st.title("📊 Dashboard")
    st.info("Conecte com a planilha futuramente")


# =====================================================
# 📊 GESTÃO DIÁRIA
# =====================================================
elif menu == "📊 Gestão Diária":

    st.title("🧾 Gestão Diária")

    # =========================
    # FUNÇÕES
    # =========================
    def moeda(v):
        return f"{abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def formatar_valor(v):
        if v > 0:
            return f"+R$ {moeda(v)}"
        elif v < 0:
            return f"-R$ {moeda(v)}"
        else:
            return f"R$ {moeda(v)}"

    def campo_valor(label, key):
        v = st.number_input(label, value=0.0, key=key)
        if v < 0:
            st.markdown("<span style='color:red'>🔴 Valor negativo</span>", unsafe_allow_html=True)
        return v

    # =========================
    # CAMPOS
    # =========================
    loja = st.text_input("🚟 Loja", "10 - São Lourenço")
    data = st.date_input("📆 Data", value=datetime.now())
    hora = st.text_input("⏰ Horário", datetime.now().strftime("%H:%M"))
    

    # responsavel = st.text_input(
    #     "👤 Responsável",
    #     "Filipe Ambrozio - Assistente Prevenção"
    # )
    nomes = [
    "Filipe Ambrozio - Assistente Prevenção",
    "Luiz Cláudio - GS Prevenção",
    "Fiscal",
]

    responsavel = st.selectbox("👤 Responsável", nomes)
    


    st.divider()

    st.subheader("📌 Vendas")
    venda = campo_valor("Venda Acumulada", "venda")
    ating = st.number_input("Atingimento (%)", value=0.0)

    estoque = campo_valor("Estoque Geral", "estoque")

    st.subheader("⚠️ Quebras")
    pi = campo_valor("Quebra PI", "pi")
    pni = campo_valor("Quebra PNI", "pni")
    total = campo_valor("Quebra Total", "total")

    st.subheader("💰 Financeiro")
    contratos = campo_valor("Contratos", "contratos")
    acordos = campo_valor("Acordos", "acordos")
    receitas = campo_valor("Receitas", "receitas")
    reversao = campo_valor("Reversão", "reversao")

    st.subheader("📊 Resultado")
    qfinal = campo_valor("Quebra Final", "qfinal")
    qmeta = st.number_input("Quebra Meta (%)", value=0.0)
    qreal = st.number_input("Quebra Real (%)", value=0.0)

    troca = campo_valor("Estoque Troca", "troca")
    t30 = campo_valor("Estoque T +30", "t30")

    # =========================
    # TEXTO FINAL PADRÃO
    # =========================
    texto = f"""🧾 GESTÃO DIÁRIA

🚟 Loja: {loja}
📆 Data: {data.strftime('%d/%m/%Y')}
⏰ Horário: {hora}h

👤 Responsável: {responsavel}

📌 Venda Acumulada Mês:
R$ {moeda(venda)}
Atingimento da meta de venda {ating:.0f}%

Estoque Geral Loja R$ {moeda(estoque)}

Quebra PI: {formatar_valor(pi)}
Quebra PNI: {formatar_valor(pni)}
Quebra Total: {formatar_valor(total)}

Contratos: {formatar_valor(contratos)}
Acordos: {formatar_valor(acordos)}
Receitas: {formatar_valor(receitas)}
Reversão: {formatar_valor(reversao)}

Quebra Final: {formatar_valor(qfinal)}
Quebra Meta: {qmeta:.2f}%
Quebra Real: {qreal:.2f}%

Estoque Troca: R$ {moeda(troca)}
Estoque T +30: R$ {moeda(t30)}
"""

    # =========================
    # PRÉVIA
    # =========================
    st.text_area("📋 Pré-visualização", texto, height=400)

    # =========================
    # WHATSAPP
    # =========================
    if st.button("📤 Compartilhar Gestão"):
        link = f"https://api.whatsapp.com/send?text={urllib.parse.quote(texto)}"
        st.success("Clique abaixo para enviar")
        st.markdown(f"[👉 Abrir WhatsApp]({link})")


# =====================================================
# 🚨 EVENTO
# =====================================================
elif menu == "🚨 Registro de Evento":

    st.title("🚨 Evento")

    data = st.date_input("Data", value=datetime.now())
    hora = st.text_input("Hora", datetime.now().strftime("%H:%M"))

    tipo = st.text_input("Tipo")
    local = st.text_input("Local")

    ocorrencia = st.text_area("Ocorrência")
    providencias = st.text_area("Providências")

    texto = f"""REGISTRO DE EVENTO

📆 {data.strftime('%d/%m/%y')}
⏰ {hora}

🚨 {tipo}
📍 {local}

📝 {ocorrencia}

📌 {providencias}
"""

    st.text_area("Prévia", texto, height=250)

    if st.button("📤 Compartilhar Evento"):
        link = f"https://api.whatsapp.com/send?text={urllib.parse.quote(texto)}"
        st.markdown(f"[👉 WhatsApp]({link})")


# =====================================================
# 📅 AGENDA
# =====================================================
elif menu == "📅 Agenda":

    st.title("📅 Agenda")

    data = st.date_input("Data")

    agenda = {
        "2026-05-04": ["Contagem FLV"],
        "2026-05-05": ["Inventário Padaria"],
    }

    atividades = agenda.get(str(data), ["Sem atividades"])

    checks = []
    for i, a in enumerate(atividades):
        c = st.checkbox(a)
        checks.append((a, c))

    concluido = [a for a, c in checks if c]
    pendente = [a for a, c in checks if not c]

    texto = f"""AGENDA

📆 {data.strftime('%d/%m/%Y')}

✔ {', '.join(concluido)}
⏳ {', '.join(pendente)}
"""

    st.text_area("Prévia", texto, height=200)

    if st.button("📤 Compartilhar Agenda"):
        link = f"https://api.whatsapp.com/send?text={urllib.parse.quote(texto)}"
        st.markdown(f"[👉 WhatsApp]({link})")

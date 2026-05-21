import streamlit as st
import pytz
from datetime import datetime
from views import temperatura, paletes, dashboard, gestao, evento, agenda, comparativo

st.set_page_config(page_title="Sistema Loja", layout="wide")

# URL antigo (publicação anterior sem doGet/dados válidos)
# URL = "https://script.google.com/macros/s/AKfycbz8wNjzEAD8u_3vzqkEdF4CK0ArnWpX4cYtX8mJwneAK2Oj39i_Ks4hjDHCsWIzNSxKJw/exec"
URL = "https://script.google.com/macros/s/AKfycbwm4g0-syNMM3RFdviJLJej_h7yqNW9xaCBtj7PYkHxFwxGc4vpThnlfGkrI1c-Na83mQ/exec"

NOMES = [
    "Luiz Claudio",
    "Filipe Ambrozio",
    "Lucia",
    "Gennif Santana",
    "Jhonattan",
    "Gernan",
    "Giovane",
    "Anderson",
    "Kesia",
    "Janaina Fernandes",
    "Sérgio Medeiros",
    "Josenildo Jose",
    "Roni Vicente",
    "Erick",
    "Daniel",
    "Angelo",
    "Alberto",
]

tz = pytz.timezone("America/Sao_Paulo")
data_hora = datetime.now(tz)

st.sidebar.title("📌 Navegação")
menu = st.sidebar.radio(
    "Menu",
    [
        "🌡️ Temperatura",
        "📦 Paletes",
        "📦\u200bPaleteria",
        "📊 Dashboard",        "📊 Comparativo",        "📊 Gestão Diária",
        "🚨 Registro de Evento",
        "📅 Agenda",
    ],
)


if "temp" not in st.session_state:
    st.session_state.temp = []

if "palete" not in st.session_state:
    st.session_state.palete = []

if menu == "🌡️ Temperatura":
    temperatura.render(URL, NOMES)
elif menu in ["📦 Paletes", "📦\u200bPaleteria"]:
    paletes.render(URL, NOMES)
elif menu == "📊 Dashboard":
    dashboard.render(URL)
elif menu == "📊 Comparativo":
    comparativo.render(URL)
elif menu == "📊 Gestão Diária":
    gestao.render()
elif menu == "🚨 Registro de Evento":
    evento.render()
elif menu == "📅 Agenda":
    agenda.render(URL)

#streamlit run app.py
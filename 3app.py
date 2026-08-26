import streamlit as st
import pytz
from datetime import datetime
from views import evento, agenda, Quebra_Venda, gestao_diaria, evolutivo

st.set_page_config(page_title="Sistema Loja", layout="wide")

URL = "https://script.google.com/macros/s/AKfycbx4ABerzNTK2GJgUJ56KBMZkONEXf_6Y2yslzdrQZA8Tlyo7wKHQjPqkZxjLIVexf_xpw/exec"

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
        "📊 Quebra Venda",
        "📈 Evolutivo Perecíveis",
        "🧾 Gestão Diária",
        "🚨 Registro de Evento",
        "📅 Agenda",
    ],
)


if "temp" not in st.session_state:
    st.session_state.temp = []

if "palete" not in st.session_state:
    st.session_state.palete = []

if menu == "📊 Quebra Venda":
    Quebra_Venda.render(URL)
elif menu == "📈 Evolutivo Perecíveis":
    evolutivo.render(URL)
elif menu == "🧾 Gestão Diária":
    gestao_diaria.render(URL)
elif menu == "🚨 Registro de Evento":
    evento.render()
elif menu == "📅 Agenda":
    agenda.render(URL)

#streamlit run 3app.py
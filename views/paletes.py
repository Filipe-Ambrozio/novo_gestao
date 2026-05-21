import streamlit as st
import requests
import pytz
from datetime import datetime


def render(URL, nomes):
    st.title("📦 Contagem de Paletes")

    nome = st.selectbox("Responsável", nomes, key="paletes_nome")
    tipo = st.selectbox("Tipo", ["CHEP", "Normal"], key="paletes_tipo")
    local = st.selectbox("Local", ["Loja", "Depósito"], key="paletes_local")
    quantidade = st.number_input("Quantidade", min_value=0, key="paletes_quantidade")

    tz = pytz.timezone("America/Sao_Paulo")
    data_hora = datetime.now(tz).strftime("%d/%m/%Y %H:%M:%S")
    st.info(data_hora)

    if st.button("Adicionar", key="paletes_add"):
        st.session_state.palete.append(
            {
                "tipo_registro": "palete",
                "data_hora": data_hora,
                "nome": nome,
                "tipo": tipo,
                "local": local,
                "quantidade": quantidade,
            }
        )
        st.success("Adicionado!")
        st.rerun()

    st.subheader("📋 Lista")

    for i, r in enumerate(st.session_state.palete):
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])

        col1.write(r["tipo"])
        col2.write(r["local"])
        col3.write(r["quantidade"])
        col4.write(r["nome"])

        if col5.button("❌", key=f"p{i}"):
            st.session_state.palete.pop(i)
            st.rerun()

    if st.button("💾 Salvar", key="paletes_salvar"):
        for r in st.session_state.palete:
            requests.post(URL, json=r)

        st.success("Salvo!")
        st.session_state.palete = []
        st.rerun()

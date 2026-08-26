import streamlit as st
import urllib.parse
import pytz
from datetime import datetime


def render():
    st.title("🚨 Evento")

    tz = pytz.timezone("America/Sao_Paulo")
    data = st.date_input("Data", value=datetime.now(tz), key="evento_data")
    hora = datetime.now(tz).strftime("%H:%M")

    tipo = st.text_input("Tipo", key="evento_tipo")
    local = st.text_input("Local", key="evento_local")

    ocorrencia = st.text_area("Ocorrência", key="evento_ocorrencia")
    providencias = st.text_area("Providências", key="evento_providencias")

    texto = f"""REGISTRO DE EVENTO

📆 {data.strftime('%d/%m/%y')}
⏰ {hora}

🚨 {tipo}
📍 {local}

📝 {ocorrencia}

📌 {providencias}
"""

    # Responsive preview for mobile
    from html import escape
    preview_html = f"""
    <div class='preview-card'>
      <div class='preview-title'>📋 Prévia</div>
      <div class='preview-body'>{escape(texto).replace('\n','<br>')}</div>
    </div>
    <style>
      .preview-card {{ background:#f1f5f8; padding:14px; border-radius:10px; max-width:100%; box-sizing:border-box; }}
      .preview-title {{ font-weight:700; margin-bottom:6px; }}
      .preview-body {{ white-space:pre-wrap; word-wrap:break-word; overflow-wrap:anywhere; }}
      @media (max-width:600px) {{ .preview-card {{ padding:10px; font-size:14px; }} }}
    </style>
    """
    st.markdown(preview_html, unsafe_allow_html=True)

    if st.button("📤 Compartilhar Evento", key="evento_share"):
        link = f"https://api.whatsapp.com/send?text={urllib.parse.quote(texto)}"
        st.markdown(f"[👉 WhatsApp]({link})")

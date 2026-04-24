import streamlit as st
import urllib.parse
from datetime import datetime

st.set_page_config(page_title="Gestão Diária", layout="centered")

st.title("📊 Gestão Diária - Compartilhar WhatsApp")

# =========================
# DADOS BÁSICOS
# =========================

loja = st.text_input("🚟 Loja", "10 - São Lourenço")

data = st.date_input("📆 Data")

# Hora editável
hora = st.text_input("⏰ Horário", datetime.now().strftime("%H:%M"))

# =========================
# RESPONSÁVEL
# =========================

responsaveis = [
    "Luiz Cláudio - GS Prevenção",
    "Filipe Ambrozio - Ass - P.P",
    "Nome3 (Subgerente)",
    "Nome4 (Fiscal)"
]

responsavel = st.selectbox("👤 Responsável", responsaveis)

if st.checkbox("Digitar outro responsável"):
    responsavel = st.text_input("Digite o nome do responsável")

# =========================
# VENDAS
# =========================

st.subheader("📌 Vendas")

venda_mes = st.number_input("Venda Acumulada Mês (R$)", value=0.0)

# Meta em percentual (como você pediu)
meta_percentual = st.number_input("Meta (%)", value=100.0)

# Base opcional para cálculo real
meta_base = st.number_input("Meta Base (R$) - opcional", value=0.0)

# Cálculo correto
if meta_base > 0:
    meta_valor = meta_base * (meta_percentual / 100)
    atingimento = (venda_mes / meta_valor * 100) if meta_valor != 0 else 0
    dif_venda = venda_mes - meta_valor
else:
    meta_valor = 0
    atingimento = 0
    dif_venda = 0

# =========================
# ESTOQUE
# =========================

estoque_geral = st.number_input("Estoque Geral Loja", value=0.0)

# =========================
# QUEBRAS
# =========================

quebra_inicial = st.number_input("Quebra Inicial", value=0.0)
quebra_pi = st.number_input("Quebra PI", value=0.0)
quebra_pni = st.number_input("Quebra PNI", value=0.0)
quebra_total = st.number_input("Quebra Total", value=0.0)

# =========================
# FINANCEIRO
# =========================

contratos = st.number_input("Contratos", value=0.0)
acordos = st.number_input("Acordos", value=0.0)
receitas = st.number_input("Receitas", value=0.0)
reversao = st.number_input("Reversão (%)", value=0.0)

# =========================
# RESULTADO
# =========================

quebra_final = st.number_input("Quebra Final", value=0.0)
quebra_meta = st.number_input("Quebra Meta (%)", value=0.0)
quebra_realizada = st.number_input("Quebra Realizada (%)", value=0.0)

estoque_troca = st.number_input("Estoque Troca", value=0.0)
estoque_t30 = st.number_input("Estoque T +30", value=0.0)

# =========================
# FORMATAÇÃO
# =========================

def moeda(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# =========================
# BOTÃO
# =========================

if st.button("📤 Compartilhar no WhatsApp"):

    data_formatada = data.strftime('%d/%m/%Y') if data else ""

    texto = f"""GESTÃO DIÁRIA

🚟 Loja: {loja}
📆 Data: {data_formatada}
⏰ Horário: {hora}

👤 Responsável:
{responsavel}

📌 Venda Acumulada Mês
R$: {moeda(venda_mes)}

Atingimento da meta de venda {atingimento:.0f}%

Meta Venda Mês
{meta_percentual:.0f}%"""

    if meta_base > 0:
        texto += f"""
Meta Base R$: {moeda(meta_base)}
Meta Calculada R$: {moeda(meta_valor)}

Dif. Venda
R$: {moeda(dif_venda)}"""

    texto += f"""

Estoque Geral Loja
R$: {moeda(estoque_geral)}

Quebra Inicial {moeda(quebra_inicial)}
Quebra PI R$: {moeda(quebra_pi)}
Quebra PNI R$: {moeda(quebra_pni)}
Quebra Total R$: {moeda(quebra_total)}

Contratos R$: {moeda(contratos)}
Acordos R$: {moeda(acordos)}
Receitas R$: {moeda(receitas)}
Reversão {reversao:.2f}%

Quebra Final R$: {moeda(quebra_final)}
Quebra Meta {quebra_meta:.2f}%
Quebra Realizada {quebra_realizada:.2f}%

Estoque Troca R$: {moeda(estoque_troca)}
Estoque T +30 R$: {moeda(estoque_t30)}
"""

    texto_url = urllib.parse.quote(texto)

    link = f"https://api.whatsapp.com/send?text={texto_url}"

    st.success("✅ Clique abaixo para escolher o contato no WhatsApp")

    st.markdown(f"[👉 Abrir WhatsApp para compartilhar]({link})")

    st.text_area("📋 Pré-visualização", texto, height=400)
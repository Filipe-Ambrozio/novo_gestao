import streamlit as st
import requests
import urllib.parse
import unicodedata
import re
from datetime import datetime
import pytz

TIMEZONE = pytz.timezone("America/Sao_Paulo")


def strip_accents(text):
    if not isinstance(text, str):
        return ""
    return unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("ascii")


def normalize_key(key):
    return strip_accents(str(key or "")).strip().lower()


def parse_number(value):
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if text == "":
        return None

    text = text.replace("R$", "").replace("r$", "").replace("%", "").replace(" ", "")
    text = text.replace("(", "-").replace(")", "")

    # Preserve decimal comma in Brazilian format
    if text.count(",") == 1 and text.count(".") > 0:
        text = text.replace(".", "").replace(",", ".")
    elif text.count(",") > 1 and text.count(".") == 0:
        text = text.replace(".", "").replace(",", ".")
    else:
        text = text.replace(",", ".")

    try:
        return float(text)
    except ValueError:
        return None


def format_brl(value, space_after_prefix=True, plus_sign=False):
    number = parse_number(value)
    if number is None:
        text = str(value or "").strip()
        return text

    formatted = f"{abs(number):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    if number < 0:
        return f"-R$ {formatted}"

    if plus_sign:
        return f"+R$ {formatted}"

    if space_after_prefix:
        return f"R$ {formatted}"

    return f"R$ {formatted}"


def format_percent(value):
    number = parse_number(value)
    if number is None:
        text = str(value or "").strip()
        if text and not text.endswith("%"):
            return f"{text}%"
        return text

    formatted = f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted}%"


def format_horario(value):
    text = str(value or "").strip()
    if not text:
        return ""
    if text.endswith("h"):
        return text
    return f"{text}h"


def normalize_month(value):
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    month_names = {
        "janeiro": 1,
        "fevereiro": 2,
        "marco": 3,
        "março": 3,
        "abril": 4,
        "maio": 5,
        "junho": 6,
        "julho": 7,
        "agosto": 8,
        "setembro": 9,
        "outubro": 10,
        "novembro": 11,
        "dezembro": 12,
    }

    lower = strip_accents(text).lower()
    if lower in month_names:
        return month_names[lower]

    try:
        month = int(lower)
        if 1 <= month <= 12:
            return month
    except ValueError:
        pass

    return None


def get_message_preview(text):
    html = text
    html = html.replace("\n", "<br>")
    
    # Destaca valores negativos em vermelho: -R$ 12.345,67
    html = re.sub(
        r"(-R\$\s[\d.,]+)",
        lambda m: f"<span style='color:red;font-weight:bold;'>{m.group(1)}</span>",
        html
    )
    
    # Destaca percentuais negativos em vermelho: -1,23%
    html = re.sub(
        r"(-[\d.,]+%)",
        lambda m: f"<span style='color:red;font-weight:bold;'>{m.group(1)}</span>",
        html
    )
    
    return f"<div style='background:#f8f9fa;padding:16px;border-radius:12px;white-space:pre-wrap;font-family:monospace;color:#111;'>{html}</div>"


def map_row_data(row):
    mapped = {}
    for key, value in (row or {}).items():
        normalized = normalize_key(key)
        if "estoque geral" in normalized and "loja" in normalized:
            mapped["estoque_geral"] = value
        elif any(pattern in normalized for pattern in ["nome da loja", "nome loja", "nome da filial", "nome da unidade", "loja", "filial", "unidade"]):
            if "estoque" not in normalized and "geral" not in normalized:
                mapped["loja"] = str(value).strip()
        elif "responsavel" in normalized or "responsavel" in normalized:
            mapped["responsavel"] = str(value).strip()
        elif "data" in normalized and "hora" not in normalized:
            mapped["data"] = str(value).strip()
        elif "horario" in normalized or "hora" in normalized:
            mapped["horario"] = str(value).strip()
        elif "ano" == normalized:
            mapped["ano"] = parse_number(value)
        elif "mes" == normalized:
            mapped["mes"] = str(value).strip()
        elif "venda" in normalized and ("acumul" in normalized or "vendas" in normalized):
            mapped["venda_acumulada"] = value
        elif "quebra inicial" in normalized:
            mapped["quebra_total"] = value
        elif "quebra ident" in normalized and "nao" not in normalized:
            mapped["quebra_pi"] = value
        elif "quebra nao" in normalized or "quebra nao ident" in normalized or "quebra naoident" in normalized:
            mapped["quebra_pni"] = value
        elif "quebra final" in normalized:
            mapped["quebra_final"] = value
        elif "contratos" in normalized:
            mapped["contratos"] = value
        elif "acordo" in normalized:
            mapped["acordos"] = value
        elif "receita" in normalized or "total receitas" in normalized:
            mapped["receitas"] = value
        elif "revers" in normalized and "real" not in normalized:
            mapped["reversao"] = value
        elif "real" in normalized and "%" in str(key):
            mapped["quebra_realizada"] = value
        elif "meta" in normalized and "%" in str(key):
            mapped["quebra_meta"] = value
        elif "troca" in normalized:
            mapped["estoque_troca"] = value
        elif "t+30" in normalized or "t 30" in normalized or "t30" in normalized:
            mapped["estoque_t30"] = value
            
        elif "atingimento" in normalized or "meta de venda" in normalized:
            mapped["atingimento_meta"] = value
        elif "lista" in normalized and ("susp" in normalized or "suspen" in normalized):
            mapped["lista_suspensa"] = str(value).strip()
    return mapped


def fetch_dados(URL):
    try:
        url_with_param = f"{URL}?tipo_registro=dados&_ts={int(datetime.now(TIMEZONE).timestamp())}"
        response = requests.get(url_with_param, headers={"Cache-Control": "no-cache"}, timeout=10)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and data.get("error"):
            st.warning(f"Erro ao carregar dados: {data.get('error')}")
            return []
        if isinstance(data, dict):
            return [data]
        if isinstance(data, list):
            return data
        return []
    except Exception as error:
        st.warning(f"Não foi possível carregar os dados da planilha: {error}")
        return []


def render(URL):
    st.title("🧾 Gestão Diária")
    st.write("Preencha o formulário abaixo para gerar a mensagem de WhatsApp com os dados da aba `dados` do Google Sheets.")

    dados = fetch_dados(URL)
    selected_index = 0
    if dados:
        rows_with_date = []
        for idx, row in enumerate(dados):
            mapped_row = map_row_data(row)
            row_year = int(mapped_row.get("ano") or 0) if mapped_row.get("ano") is not None else None
            row_month = normalize_month(mapped_row.get("mes"))
            rows_with_date.append((idx, row_year, row_month, mapped_row))

        available_years = sorted({year for _, year, month, _ in rows_with_date if year is not None and month is not None})
        if not available_years:
            available_years = [datetime.now(TIMEZONE).year]

        selected_year = st.selectbox(
            "Ano",
            available_years,
            index=available_years.index(datetime.now(TIMEZONE).year) if datetime.now(TIMEZONE).year in available_years else 0,
            key="gestao_year_search"
        )

        available_months = sorted({month for _, year, month, _ in rows_with_date if year == selected_year and month is not None})
        if not available_months:
            available_months = [datetime.now(TIMEZONE).month]

        month_names = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
        ]

        selected_month = st.selectbox(
            "Mês",
            available_months,
            format_func=lambda month: month_names[month - 1],
            index=available_months.index(datetime.now(TIMEZONE).month) if datetime.now(TIMEZONE).month in available_months else 0,
            key="gestao_month_search"
        )

        matching_indexes = [idx for idx, year, month, _ in rows_with_date if year == selected_year and month == selected_month]
        if matching_indexes:
            if len(matching_indexes) > 1:
                select_options = [f"Registro {i + 1}" for i in matching_indexes]
                chosen = st.selectbox("Registros do mês selecionado", select_options, key="gestao_same_month_select")
                selected_index = matching_indexes[select_options.index(chosen)]
            else:
                selected_index = matching_indexes[0]
        else:
            st.warning("Nenhum registro encontrado para o mês/ano selecionado. Mostrando o primeiro registro disponível.")
            selected_index = 0

    row = dados[selected_index] if dados else {}
    mapped = map_row_data(row)
    if not mapped.get("loja"):
        mapped["loja"] = "10 - São Lourenço"

    responsavel_options = [
        "Filipe Ambrozio (ASS - P.P)",
        "Luiz Cláudio - GS Prevenção",
        "Outros",
    ]
    default_responsavel = mapped.get("responsavel", responsavel_options[0])
    if default_responsavel not in responsavel_options:
        responsavel_options = [default_responsavel] + responsavel_options
    responsavel = st.selectbox("Responsável", options=responsavel_options, index=responsavel_options.index(default_responsavel), key="gestao_responsavel_select")

    col1, col2, col3 = st.columns(3)
    with col1:
        loja_value = mapped.get("loja") or "10 - São Lourenço"
        loja = st.text_input("Loja", value=loja_value, disabled=True, key="gestao_loja")
        venda_acumulada = st.text_input(
            "Venda Acumulada Mês",
            value=format_brl(mapped.get("venda_acumulada", ""), space_after_prefix=True),
            disabled=True,
            key="gestao_venda_acumulada"
        )
        quebra_pi = st.text_input("Quebra PI", value=format_brl(mapped.get("quebra_pi", ""), space_after_prefix=False), disabled=True, key="gestao_quebra_pi")
        quebra_total = st.text_input("Quebra Total", value=format_brl(mapped.get("quebra_total", ""), space_after_prefix=False), disabled=True, key="gestao_quebra_total")
        contratos = st.text_input("Contratos", value=format_brl(mapped.get("contratos", ""), space_after_prefix=False, plus_sign=True), disabled=True, key="gestao_contratos")
        quebra_final = st.text_input("Quebra Final", value=format_brl(mapped.get("quebra_final", ""), space_after_prefix=False), disabled=True, key="gestao_quebra_final")
        estoque_troca = st.text_input("Estoque Troca", value=format_brl(mapped.get("estoque_troca", ""), space_after_prefix=False), key="gestao_estoque_troca")

    with col2:
        data_value = mapped.get("data", datetime.now(TIMEZONE).strftime("%d/%m/%Y"))
        data_text = st.text_input("Data", value=data_value, disabled=True, key="gestao_data")
        horario = st.text_input("Horário", value=format_horario(mapped.get("horario", datetime.now(TIMEZONE).strftime("%H:%M"))), disabled=True, key="gestao_horario")
        quebra_pni = st.text_input("Quebra PNI", value=format_brl(mapped.get("quebra_pni", ""), space_after_prefix=False), disabled=True, key="gestao_quebra_pni")
        acordos = st.text_input("Acordos", value=format_brl(mapped.get("acordos", ""), space_after_prefix=False, plus_sign=True), disabled=True, key="gestao_acordos")
        quebra_meta = st.text_input("Quebra Meta", value=format_percent(mapped.get("quebra_meta", "")), disabled=True, key="gestao_quebra_meta")
        estoque_t30 = st.text_input("Estoque T+30", value=format_brl(mapped.get("estoque_t30", ""), space_after_prefix=False), key="gestao_estoque_t30")

    with col3:
        st.write("**Apenas campos manuais abaixo**")
        atingimento_meta = st.text_input(
            "Atingimento da meta de venda",
            value=format_percent(mapped.get("atingimento_meta", "")),
            key="gestao_atingimento_meta",

        )
        estoque_geral = st.text_input(
            "Estoque Geral Loja",
            value=format_brl(mapped.get("estoque_geral", ""), space_after_prefix=False, plus_sign=True),
            key="gestao_estoque_geral",
        )
        receitas = st.text_input(
            "Receitas",
            value=format_brl(mapped.get("receitas", ""), space_after_prefix=False, plus_sign=True),
            disabled=True,
            key="gestao_receitas",
        )
        reversao = st.text_input(
            "Reversão",
            value=format_brl(mapped.get("reversao", ""), space_after_prefix=False),
            disabled=True,
            key="gestao_reversao",
        )
        quebra_realizada = st.text_input(
            "Quebra Realizada",
            value=format_percent(mapped.get("quebra_realizada", "")),
            disabled=True,
            key="gestao_quebra_realizada",
        )

    st.markdown("---")
    st.subheader("Pré-visualização da mensagem")

    quebra_total = locals().get("quebra_total", format_brl(mapped.get("quebra_total", ""), space_after_prefix=False))
    horario = format_horario(horario)
    if not data_text:
        data_text = datetime.now(TIMEZONE).strftime("%d/%m/%Y")

    texto = f"*GESTÃO DIÁRIA*\n"
    texto += f"🚟 Loja: {loja}\n"
    texto += f"📆 Data: {data_text}\n"
    texto += f"⏰ Horário: {horario}\n\n"
    texto += f"👤 Responsável:\n{responsavel}\n\n"
    texto += f"📌 Venda Acumulada Mês:\n"
    texto += f"{format_brl(venda_acumulada, space_after_prefix=True)}\n\n"
    texto += f"Atingimento da meta de venda: {format_percent(atingimento_meta)}\n\n"
    texto += f"Estoque Geral Loja: {format_brl(estoque_geral, space_after_prefix=False)}\n\n"
    texto += f"Quebra PI: {format_brl(quebra_pi, space_after_prefix=False)}\n"
    texto += f"Quebra PNI: {format_brl(quebra_pni, space_after_prefix=False)}\n"
    texto += f"Quebra Total: {format_brl(quebra_total, space_after_prefix=False)}\n\n"
    texto += f"Contratos: {format_brl(contratos, space_after_prefix=False, plus_sign=True)}\n"
    texto += f"Acordos: {format_brl(acordos, space_after_prefix=False, plus_sign=True)}\n"
    texto += f"Receitas: {format_brl(receitas, space_after_prefix=False, plus_sign=True)}\n"
    texto += f"Reversão: {format_brl(reversao, space_after_prefix=False)}\n\n"
    texto += f"Quebra Final: {format_brl(quebra_final, space_after_prefix=False)}\n"
    texto += f"Quebra Meta: {format_percent(quebra_meta)}\n"
    texto += f"Quebra Realizada: {format_percent(quebra_realizada)}\n\n"
    texto += f"Estoque Troca: {format_brl(estoque_troca, space_after_prefix=False)}\n"
    texto += f"Estoque T+30: {format_brl(estoque_t30, space_after_prefix=False)}"

    st.markdown(get_message_preview(texto), unsafe_allow_html=True)

    st.markdown("---")
    st.write("Use o botão abaixo para abrir o WhatsApp Web com o texto formatado.")

    link = f"https://api.whatsapp.com/send?text={urllib.parse.quote(texto)}"
    st.markdown(f"[👉 Abrir WhatsApp]({link})", unsafe_allow_html=True)


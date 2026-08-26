import streamlit as st
import requests
import pytz
from datetime import datetime

st.set_page_config(page_title="Home", page_icon="🏠", layout="wide")

# st.markdown(
#     "[🔗 Acessar gráfico em BI](https://app.powerbi.com/view?r=eyJrIjoiOWQ0ZjBjZTMtZTYzNy00OTcyLWIwNjUtZWViZGQ0MWM0NjU2IiwidCI6ImU1MzA4M2Y2LTYwOWItNDQzMi05NmVkLWJjZGM2NmM1MjI2YSJ9)"
# )
st.title("☕ Link de Acessos")

st.markdown(
    "[🔗 Acessar gráfico em BI](https://app.powerbi.com/view?r=eyJrIjoiOWQ0ZjBjZTMtZTYzNy00OTcyLWIwNjUtZWViZGQ0MWM0NjU2IiwidCI6ImU1MzA4M2Y2LTYwOWItNDQzMi05NmVkLWJjZGM2NmM1MjI2YSJ9)"
)
st.markdown(
    "[🔗 Acessar PLanilha de Dados](https://docs.google.com/spreadsheets/d/1wvOvJJ8KnD3-DbHRvuMyTgWZYbkiqELIUNpKiExVVQ4/edit?usp=sharing)"
)
st.markdown(
    "[🔗 Acessar PLanilha de Atividades](https://docs.google.com/spreadsheets/d/1PPObC1YVFTzHyxWZqtNwocvr53ZDfyszo69DVkjvIxc/edit?usp=sharing)"
)
st.markdown(
    "[🔗 Acessar Planila de Processos](https://docs.google.com/spreadsheets/d/1E37vAop5Cd4RhopYW7baRgIlkf_DjYfqHzz1gfy7-ZE/edit?usp=sharing)"
)

URL = "https://script.google.com/macros/s/AKfycbx7BTCWvv7Qksv6NeuIp2q4-PLHYyDrfYAUdDBnyosIFBKOFn6c0Z-cD8aEhzPntw3brw/exec"
      #https://script.google.com/macros/s/AKfycbx7BTCWvv7Qksv6NeuIp2q4-PLHYyDrfYAUdDBnyosIFBKOFn6c0Z-cD8aEhzPntw3brw/exec
PRIORITY_MAP = {
    "high": {"color": "#f8d7da", "label": "ALTA PRIORIDADE", "icon": "🔴"},
    "medium": {"color": "#fff3cd", "label": "PRIORIDADE MÉDIA", "icon": "🟡"},
    "low": {"color": "#d4edda", "label": "BAIXA PRIORIDADE", "icon": "🟢"},
}


def normalize_key(key):
    return str(key or "").strip().lower()


def detect_priority(value):
    text = str(value or "").strip().lower()
    if not text:
        return "low"

    high_tokens = ["alto", "alta", "urgente", "urgencia", "vermelho", "vermelha", "critical", "critico", "crítico"]
    medium_tokens = ["medio", "médio", "média", "amarelo", "yellow", "média"]
    low_tokens = ["baixo", "baixa", "verde", "green", "low"]

    if any(token in text for token in high_tokens):
        return "high"
    if any(token in text for token in medium_tokens):
        return "medium"
    if any(token in text for token in low_tokens):
        return "low"

    try:
        number = float(text.replace("%", "").replace(",", "."))
        if number >= 7:
            return "high"
        if number >= 4:
            return "medium"
        return "low"
    except Exception:
        return "low"


def get_value(row, keys):
    for key, value in (row or {}).items():
        normalized = normalize_key(key)
        for candidate in keys:
            if candidate in normalized:
                return str(value or "").strip()
    return ""


def fetch_home_data(url):
    try:
        params = {
            "tipo_registro": "home",
            "_ts": int(datetime.now(pytz.timezone("America/Sao_Paulo")).timestamp()),
        }
        response = requests.get(url, params=params, headers={"Cache-Control": "no-cache"}, timeout=12)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and data.get("error"):
            st.error(f"Erro ao carregar a aba home: {data.get('error')}")
            return []
        if isinstance(data, dict):
            return [data]
        return data or []
    except Exception as error:
        st.error(f"Não foi possível carregar os dados da aba home: {error}")
        return []


def render_task_list(rows):
    cards = []
    high_count = medium_count = low_count = 0

    for row in rows:
        task = get_value(row, ["descrição", "descricao", "tarefa", "task", "item", "acao", "ação", "atividade"])
        priority_text = get_value(row, ["nível", "nivel", "prioridade"])
        note = get_value(row, ["observação", "observacao", "obs", "comentario", "comentário", "detalhe"])

        if not task:
            task = " | ".join([f"{key}: {value}" for key, value in (row or {}).items() if value is not None and str(value).strip()])

        if not priority_text:
            priority_text = get_value(row, ["status", "situacao", "situação", "impacto", "categoria", "tipo"])

        priority = detect_priority(priority_text)
        if priority == "high":
            high_count += 1
        elif priority == "medium":
            medium_count += 1
        else:
            low_count += 1

        date_info = get_value(row, ["data", "date"])
        card = f"""
<div style='background: {PRIORITY_MAP[priority]['color']}; border-radius: 16px; padding: 16px; margin-bottom: 12px; border: 1px solid rgba(0,0,0,0.08);'>
  <div style='font-weight: 700; margin-bottom: 4px; color:#222;'>{PRIORITY_MAP[priority]['icon']} {task}</div>
  <div style='font-size: 14px; color: #333;'>
    <strong>{PRIORITY_MAP[priority]['label']}</strong>
    {f" • {priority_text}" if priority_text else ""}
    {f" • {date_info}" if date_info else ""}
  </div>
  {f"<div style='margin-top:10px;font-size:14px;color:#2a2a2a;'>📎 {note}</div>" if note else ""}
</div>
"""
        cards.append(card)

    return cards, high_count, medium_count, low_count


def render():
    st.title("🏠 Home")
    st.markdown("### 📌 Atualizações da Aplicação")

    rows = fetch_home_data(URL)
    if not rows:
        st.warning("A aba home não retornou dados ou está vazia. Verifique a planilha do Google Sheets.")
        return

    cards, high_count, medium_count, low_count = render_task_list(rows)

    if high_count:
        st.error(f"🚨 Alta prioridade: {high_count} tarefa(s) detectada(s).")
    else:
        st.success("✅ Sem tarefas de alta prioridade no momento.")

    if medium_count:
        st.warning(f"⚠️ Prioridade média: {medium_count} tarefa(s).")
    if low_count:
        st.success(f"🟢 Baixa prioridade: {low_count} tarefa(s).")

    st.markdown("---")
    st.markdown(
        "<div style='background:#fff8e1;padding:20px;border-radius:20px;'>"
        "<strong style='font-size:18px;'>Lista de tarefas da aba Home</strong>"
        "</div>",
        unsafe_allow_html=True,
    )

    for card in cards:
        st.markdown(card, unsafe_allow_html=True)

    st.markdown("---")
    # st.markdown(
    #     "[🔗 Acessar gráfico em BI](https://app.powerbi.com/view?r=eyJrIjoiOWQ0ZjBjZTMtZTYzNy00OTcyLWIwNjUtZWViZGQ0MWM0NjU2IiwidCI6ImU1MzA4M2Y2LTYwOWItNDQzMi05NmVkLWJjZGM2NmM1MjI2YSJ9)",
    #     unsafe_allow_html=True,
    # )


if __name__ == "__main__":
    render()

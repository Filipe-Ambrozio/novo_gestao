import streamlit as st
import pytz
from datetime import datetime
import urllib.parse
import requests

DEFAULT_AGENDA = [
    {
        "id": 1,
        "data": "2026-05-01",
        "evento": "Inventario não contavel",
        "status": "Finalizado",
        "observacao": "Tratativa",
    },
    {
        "id": 2,
        "data": "2026-05-03",
        "evento": "Reunião de reciclagem",
        "status": "Aberto",
        "observacao": "Reunião com os colaboradore para traigem de abordagem",
    },
    {
        "id": 3,
        "data": "2026-05-20",
        "evento": "Inventario Acougue",
        "status": "Aberto",
        "observacao": "Inventario de acougue parcial",
    },
    {
        "id": 4,
        "data": "2026-05-25",
        "evento": "Final ferias (Nome)",
        "status": "Aberto",
        "observacao": "Terminou das ferias",
    },
    {
        "id": 5,
        "data": "2026-05-25",
        "evento": "Teste de alarme",
        "status": "Aberto",
        "observacao": "Será realizado teste de alarme com o grupo segue.",
    },
]


def normalize_agenda_date(value):
    text = str(value or "").strip()
    if not text:
        return ""

    # Already in yyyy-mm-dd
    if text.count("-") == 2:
        parts = text.split("-")
        if len(parts[0]) == 4 and len(parts[1]) <= 2 and len(parts[2]) <= 2:
            return text

    # Accept dd/mm/yyyy, dd-mm-yyyy, dd.mm.yyyy
    for sep in ["/", "-", "."]:
        if sep in text:
            parts = text.split(sep)
            if len(parts) == 3:
                a, b, c = parts
                if len(c) == 4:
                    if len(a) == 4:
                        return f"{a.zfill(4)}-{b.zfill(2)}-{c.zfill(2)}"
                    return f"{c.zfill(4)}-{b.zfill(2)}-{a.zfill(2)}"

    # Accept ddmmyyyy
    if len(text) == 8 and text.isdigit():
        return f"{text[4:8]}-{text[2:4]}-{text[0:2]}"

    return text


def normalize_status(text):
    return str(text or "").strip().lower()


def load_agenda_events(URL):
    try:
        response = requests.get(
            URL,
            params={"tipo_registro": "agenda", "_ts": str(datetime.now(pytz.timezone("America/Sao_Paulo")).timestamp())},
            headers={"Cache-Control": "no-cache"},
            timeout=10,
        )
        response.raise_for_status()
        events = response.json()
        if isinstance(events, list) and events:
            for event in events:
                event["data"] = normalize_agenda_date(event.get("data", ""))
                event["status"] = str(event.get("status", "")).strip()
            return events
    except Exception as error:
        st.warning(
            "Não foi possível carregar a agenda diretamente do servidor. Verifique o URL do Apps Script e recarregue."
        )
        st.write(f"Erro de carregamento: {error}")

    return [dict(item) for item in DEFAULT_AGENDA]


def save_event_status(URL, event_id, status="Finalizado"):
    try:
        payload = {
            "tipo_registro": "agenda_status",
            "id": event_id,
            "status": status,
        }
        requests.post(URL, json=payload, timeout=5)
    except Exception:
        pass


def get_event_status(event, today):
    status = normalize_status(event.get("status", ""))
    date_text = event.get("data", "")

    if status == "finalizado":
        return "Finalizado", "#6c757d", "#e9ecef"

    if not date_text:
        return "Sem data", "#0d6efd", "#cff4fc"

    try:
        event_date = datetime.fromisoformat(date_text).date()
    except ValueError:
        return "Data inválida", "#fd7e14", "#fff3cd"

    delta = (event_date - today).days
    if delta < 0:
        return "Vencido", "#dc3545", "#f8d7da"
    if delta <= 10:
        return f"Faltam {delta} dia(s)", "#ffb703", "#fff3cd"

    return f"Ativo ({delta} dias)", "#198754", "#d4edda"


def render_event_card(event, today):
    badge_text, badge_color, background = get_event_status(event, today)
    status_text = event.get("status", "Aberto")
    date_text = event.get("data", "-")
    observacao = event.get("observacao", "-")
    evento = event.get("evento", "-")

    return f"""
<div style='background: {background}; padding: 16px; border-radius: 12px; margin-bottom: 12px; border: 1px solid rgba(0,0,0,0.08);'>
  <div style='display: flex; justify-content: space-between; gap: 16px; align-items: start;'>
    <div style='flex: 1; min-width: 0;'>
      <div style='font-size: 17px; font-weight: 700; margin-bottom: 6px;'>{evento}</div>
      <div style='font-size: 14px; color: #333; margin-bottom: 6px;'>Data: {date_text}</div>
      <div style='font-size: 13px; color: #444;'>{observacao}</div>
    </div>
    <div style='text-align: right; min-width: 130px;'>
      <div style='display: inline-block; padding: 8px 12px; border-radius: 999px; background: {badge_color}; color: #000; font-weight: 700; font-size: 13px;'>{badge_text}</div>
      <div style='margin-top: 8px; color: #555; font-size: 13px;'>Status: {status_text}</div>
    </div>
  </div>
</div>
"""


def get_action_label(event):
    return "Reabrir" if normalize_status(event.get("status", "")) == "finalizado" else "Finalizar"


def apply_event_status_change(event, URL):
    current_status = normalize_status(event.get("status", ""))
    new_status = "Aberto" if current_status == "finalizado" else "Finalizado"
    save_event_status(URL, event["id"], new_status)
    event["status"] = new_status
    return new_status


def render_events_section(events, today, URL, section_key_prefix=""):
    for event in events:
        st.markdown(render_event_card(event, today), unsafe_allow_html=True)
        action_label = get_action_label(event)
        if st.button(action_label, key=f"{section_key_prefix}agenda_action_{event['id']}"):
            new_status = apply_event_status_change(event, URL)
            st.success(f"Evento '{event.get('evento', '')}' atualizado para {new_status}.")
        st.write("")


def render(URL):
    st.title("📅 Agenda")

    if st.button("⟳ Recarregar agenda", key="agenda_refresh"):
        pass

    agenda_events = load_agenda_events(URL)
    tz = pytz.timezone("America/Sao_Paulo")
    today = datetime.now(tz).date()
    selected_date = st.date_input("Filtrar por data", value=today, key="agenda_data")
    selected_key = selected_date.strftime("%Y-%m-%d")

    st.caption(f"Eventos carregados: {len(agenda_events)}")

    overdue_events = [event for event in agenda_events if event.get("data") and datetime.fromisoformat(event["data"]).date() < today and normalize_status(event.get("status")) != "finalizado"]
    soon_events = [event for event in agenda_events if event.get("data") and 0 <= (datetime.fromisoformat(event["data"]).date() - today).days <= 10 and normalize_status(event.get("status")) != "finalizado"]
    active_events = [event for event in agenda_events if event.get("data") and (datetime.fromisoformat(event["data"]).date() - today).days > 10 and normalize_status(event.get("status")) != "finalizado"]
    finished_events = [event for event in agenda_events if normalize_status(event.get("status")) == "finalizado"]

    st.markdown(
        """
<div style='display: flex; gap: 12px; flex-wrap: wrap;'>
  <div style='flex: 1; min-width: 180px; padding: 14px; border-radius: 12px; background: #f8d7da; border: 1px solid #f5c2c7;'>
    <div style='font-size: 24px; font-weight: 700;'>{}</div>
    <div style='color: #842029;'>Vencidos</div>
  </div>
  <div style='flex: 1; min-width: 180px; padding: 14px; border-radius: 12px; background: #fff3cd; border: 1px solid #ffecb5;'>
    <div style='font-size: 24px; font-weight: 700;'>{}</div>
    <div style='color: #664d03;'>Faltam até 10 dias</div>
  </div>
  <div style='flex: 1; min-width: 180px; padding: 14px; border-radius: 12px; background: #d4edda; border: 1px solid #c3e6cb;'>
    <div style='font-size: 24px; font-weight: 700;'>{}</div>
    <div style='color: #0f5132;'>Ativos</div>
  </div>
  <div style='flex: 1; min-width: 180px; padding: 14px; border-radius: 12px; background: #e2e3e5; border: 1px solid #d3d6d8;'>
    <div style='font-size: 24px; font-weight: 700;'>{}</div>
    <div style='color: #41464b;'>Finalizados</div>
  </div>
</div>
""".format(len(overdue_events), len(soon_events), len(active_events), len(finished_events)),
        unsafe_allow_html=True,
    )

    st.write("---")
    st.subheader("🔎 Eventos por data")
    filtered_events = [event for event in agenda_events if event.get("data", "") == selected_key]

    if filtered_events:
        render_events_section(filtered_events, today, URL, section_key_prefix="filtered_")
    else:
        st.info("Nenhum evento encontrado para essa data.")

    st.write("---")
    st.subheader("📍 Todos os eventos")
    if agenda_events:
        render_events_section(sorted(agenda_events, key=lambda item: item.get("data", "")), today, URL, section_key_prefix="all_")
    else:
        st.info("A planilha de agenda está vazia ou não foi possível carregar os dados.")

        texto = f"""AGENDA

Data filtrada: {selected_date.strftime('%d/%m/%Y')}

{', '.join([event['evento'] for event in filtered_events]) or 'Sem atividades'}
"""

        # Responsive preview for mobile
        from html import escape
        preview_html = f"""
        <div class='preview-card'>
            <div class='preview-title'>📋 Prévia</div>
            <div class='preview-body'>{escape(texto).replace('\n','<br>')}</div>
        </div>
        <style>
            .preview-card {{ background:#f8f9fa; padding:12px; border-radius:10px; max-width:100%; box-sizing:border-box; }}
            .preview-title {{ font-weight:700; margin-bottom:6px; }}
            .preview-body {{ white-space:pre-wrap; word-wrap:break-word; overflow-wrap:anywhere; }}
            @media (max-width:600px) {{ .preview-card {{ padding:10px; font-size:14px; }} }}
        </style>
        """
        st.markdown(preview_html, unsafe_allow_html=True)

    if st.button("📤 Compartilhar Agenda", key="agenda_share"):
        link = f"https://api.whatsapp.com/send?text={urllib.parse.quote(texto)}"
        st.markdown(f"[👉 WhatsApp]({link})")

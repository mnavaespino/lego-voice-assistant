import streamlit as st
import requests
import re
import json
import pandas as pd
from datetime import datetime

# ------------------------------------------------------------
# CONFIGURACIÓN GENERAL
# ------------------------------------------------------------
st.set_page_config(page_title="LEGO IA", page_icon="🧱", layout="centered")
st.title("🧱 LEGO IA")
st.caption("Consulta y administra tu colección LEGO")

# Endpoints
LAMBDA_SEARCH = "https://ztpcx6dks9.execute-api.us-east-1.amazonaws.com/default/legoSearch"
LAMBDA_SEARCH_FILTER = "https://pzj4u8wwxc.execute-api.us-east-1.amazonaws.com/default/legoSearchFilter"

# ------------------------------------------------------------
# FUNCIONES AUXILIARES
# ------------------------------------------------------------
def limpiar_md_rotas(txt: str) -> str:
    return re.sub(r"!\[.*?\]\(\s*\)", "", txt or "")

def mostrar_detalle_expandido(set_data):
    """Muestra el detalle completo del set dentro del expander"""
    image_url = set_data.get("image_url", set_data.get("thumb_url", ""))
    if image_url:
        st.image(image_url, width=350)

    st.markdown(f"**🧩 Piezas:** {set_data.get('pieces', '')}")
    st.markdown(f"**🎁 Condición:** {set_data.get('condition', '')}")
    st.markdown(f"**🏠 Ubicación:** {set_data.get('storage', '')}")
    st.markdown(f"**📦 Caja:** {set_data.get('storage_box', '')}")
    st.markdown(f"**📅 Año:** {set_data.get('year', '')}")
    st.markdown(f"**🏷️ Tema:** {set_data.get('theme', '')}")

    manuals = set_data.get("manuals", [])
    if manuals:
        links = [f"[Manual {i+1}]({m})" for i, m in enumerate(manuals)]
        st.markdown("**📘 Manuales:** " + " · ".join(links))

    minifigs = set_data.get("minifigs_names", [])
    numbers = set_data.get("minifigs_numbers", [])
    if minifigs:
        figs = ", ".join([f"{n} ({num})" for n, num in zip(minifigs, numbers)])
        st.markdown(f"**🧍 Minifigs:** {figs}")

    if set_data.get("lego_web_url"):
        st.markdown(f"[🌐 Página oficial LEGO]({set_data.get('lego_web_url')})")

# ------------------------------------------------------------
# PESTAÑAS
# ------------------------------------------------------------
tab1, tab3 = st.tabs(["🔍 Buscar", "📦 Listado"])

# ============================================================
# TAB 1 — BÚSQUEDA
# ============================================================
with tab1:
    pregunta = st.text_input("🔍 Pregunta", placeholder="Ejemplo: ¿Qué sets de Star Wars tengo?")
    if st.button("Buscar"):
        if not pregunta.strip():
            st.warning("Escribe una pregunta.")
        else:
            with st.spinner("Buscando..."):
                try:
                    r = requests.post(LAMBDA_SEARCH, json={"pregunta": pregunta}, timeout=40)
                    if r.status_code != 200:
                        st.error(f"Error {r.status_code}: {r.text}")
                    else:
                        data = r.json()
                        body = data.get("body")
                        if isinstance(body, str):
                            data = json.loads(body)
                        respuesta = limpiar_md_rotas(data.get("respuesta", ""))
                        if respuesta:
                            st.markdown(f"### 💬 {respuesta}")
                        resultados = data.get("resultados", [])
                        if not resultados:
                            st.info("No se encontraron resultados.")
                        else:
                            for set_data in resultados:
                                set_number = set_data.get("set_number", "")
                                name = set_data.get("name", "")
                                theme = set_data.get("theme", "")
                                year = set_data.get("year", "")
                                piezas = set_data.get("pieces", "")
                                resumen = f"{theme} · {year} · 🧩 {piezas} piezas"

                                with st.expander(f"**{set_number} · {name}**  \n{resumen}"):
                                    mostrar_detalle_expandido(set_data)
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# ============================================================
# TAB 3 — LISTADO POR TEMA
# ============================================================
with tab3:
    st.subheader("📦 Listado por tema")
    tema = st.selectbox("Selecciona el tema:", ["Star Wars", "Technic", "Ideas", "F1"])

    if st.button("Mostrar sets"):
        with st.spinner(f"Obteniendo sets de {tema}..."):
            try:
                r = requests.post(LAMBDA_SEARCH_FILTER, json={"tema": tema}, timeout=40)
                if r.status_code != 200:
                    st.error(f"Error {r.status_code}: {r.text}")
                else:
                    data = r.json()
                    body = data.get("body")
                    if isinstance(body, str):
                        data = json.loads(body)

                    resultados = data.get("resultados", [])
                    if not resultados:
                        st.info(f"No hay sets registrados en el tema {tema}.")
                    else:
                        for set_data in resultados:
                            set_number = set_data.get("set_number", "")
                            name = set_data.get("name", "")
                            piezas = set_data.get("pieces", "")
                            resumen = f"🧩 {piezas} piezas · 🎁 {set_data.get('condition','')}"

                            with st.expander(f"**{set_number} · {name}**  \n{resumen}"):
                                mostrar_detalle_expandido(set_data)
            except Exception as e:
                st.error(f"Ocurrió un error: {str(e)}")

# ------------------------------------------------------------
# PIE
# ------------------------------------------------------------
st.markdown("---")
st.caption("Desarrollado por Mike Nava · Firestore + OpenAI + AWS Lambda + Streamlit")

import streamlit as st
import requests
import re
import json
import base64
from datetime import datetime
import pandas as pd

# ------------------------------------------------------------
# CONFIGURACIÓN GENERAL
# ------------------------------------------------------------
st.set_page_config(page_title="LEGO IA", page_icon="🧱", layout="centered")
st.title("🧱 LEGO IA")
st.caption("Consulta y administra tu colección LEGO")

LAMBDA_SEARCH = "https://ztpcx6dks9.execute-api.us-east-1.amazonaws.com/default/legoSearch"
LAMBDA_ADMIN = "https://nn41og73w2.execute-api.us-east-1.amazonaws.com/default/legoAdmin"
LAMBDA_SEARCH_FILTER = "https://pzj4u8wwxc.execute-api.us-east-1.amazonaws.com/default/legoSearchFilter"

# ------------------------------------------------------------
# FUNCIONES AUXILIARES
# ------------------------------------------------------------
def convertir_a_base64(archivo):
    if archivo is None:
        return None
    contenido = archivo.read()
    b64 = base64.b64encode(contenido).decode("utf-8")
    tipo = archivo.type
    return f"data:{tipo};base64,{b64}"

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
tab1, tab2, tab3 = st.tabs(["🔍 Buscar", "⚙️ Administrar", "📦 Listado"])

# ============================================================
# TAB 3: LISTADO CON MINIATURA SIEMPRE VISIBLE
# ============================================================
with tab3:
    st.subheader("📦 Listado de sets por tema")
    tema = st.selectbox("Selecciona el tema a mostrar:", ["Star Wars", "Technic", "Ideas", "F1"])

    if st.button("Mostrar sets"):
        try:
            headers = {"Content-Type": "application/json"}
            with st.spinner(f"Obteniendo sets de {tema}..."):
                r = requests.post(LAMBDA_SEARCH_FILTER, json={"tema": tema}, headers=headers, timeout=40)
                if r.status_code == 200:
                    data = r.json()
                    body = data.get("body")
                    if isinstance(body, str):
                        data = json.loads(body)
                    resultados = data.get("resultados", [])

                    if not resultados:
                        st.info(f"No hay sets registrados en el tema {tema}.")
                    else:
                        for set_data in resultados:
                            thumb = set_data.get("thumb_url", set_data.get("image_url", ""))
                            set_number = set_data.get("set_number", "")
                            name = set_data.get("name", "")
                            year = set_data.get("year", "")
                            piezas = set_data.get("pieces", "")
                            condicion = set_data.get("condition", "")
                            resumen = f"{year} · 🧩 {piezas} piezas · 🎁 {condicion}"

                            # Miniatura visible + Expander con detalle
                            col1, col2 = st.columns([1, 5])
                            with col1:
                                if thumb:
                                    st.image(thumb, width=80)
                                else:
                                    st.markdown("<div style='width:80px;height:80px;background:#ddd;border-radius:8px;'></div>", unsafe_allow_html=True)
                            with col2:
                                st.markdown(f"**{set_number} · {name}**")
                                st.markdown(f"{resumen}")
                                with st.expander("Ver detalles"):
                                    mostrar_detalle_expandido(set_data)
                            st.markdown("---")

                else:
                    st.error(f"Error {r.status_code}: {r.text}")

        except Exception as e:
            st.error(f"Ocurrió un error: {str(e)}")

# ============================================================
# TAB 1 Y 2 SE MANTIENEN IGUAL (sin cambios)
# ============================================================
# ... (mantén las secciones anteriores de Buscar y Administrar tal como las tienes)

# ------------------------------------------------------------
# PIE
# ------------------------------------------------------------
st.markdown("---")
st.caption("Desarrollado por Mike Nava · Firestore + OpenAI + AWS Lambda + Streamlit")

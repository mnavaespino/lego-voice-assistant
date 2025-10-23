import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import base64

# ------------------------------------------------------------
# CONFIGURACIÓN
# ------------------------------------------------------------
st.set_page_config(page_title="LEGO IA", page_icon="🧱", layout="centered")
st.markdown("<h2 style='text-align:center;'>🧱 LEGO IA</h2>", unsafe_allow_html=True)
st.caption("Consulta y administra tu colección LEGO")

LAMBDA_SEARCH = "https://ztpcx6dks9.execute-api.us-east-1.amazonaws.com/default/legoSearch"
LAMBDA_ADMIN = "https://nn41og73w2.execute-api.us-east-1.amazonaws.com/default/legoAdmin"
LAMBDA_SEARCH_FILTER = "https://pzj4u8wwxc.execute-api.us-east-1.amazonaws.com/default/legoSearchFilter"


# ------------------------------------------------------------
# FUNCIONES
# ------------------------------------------------------------
def convertir_a_base64(archivo):
    if archivo is None:
        return None
    contenido = archivo.read()
    b64 = base64.b64encode(contenido).decode("utf-8")
    return f"data:{archivo.type};base64,{b64}"


def mostrar_resultados(resultados):
    """Muestra los sets encontrados en formato minimalista."""
    for r in resultados:
        col1, col2 = st.columns([1, 3])
        with col1:
            if r.get("thumb_url"):
                st.image(r["thumb_url"], use_container_width=True)
            else:
                st.empty()
        with col2:
            st.markdown(f"**{r.get('set_number','')} · {r.get('name','')}**")
            st.caption(f"{r.get('theme','')} · {r.get('year','')} · 🧩 {r.get('pieces','')} piezas")
            st.write(f"🎁 {r.get('condition','')} · 🏠 {r.get('storage','')} · Caja {r.get('storage_box','')}")
        st.divider()


# ------------------------------------------------------------
# PESTAÑAS
# ------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🔍 Buscar", "📦 Listado", "⚙️ Administrar"])

# ============================================================
# TAB 1: BUSCAR
# ============================================================
with tab1:
    pregunta = st.text_input("Escribe tu pregunta:", placeholder="Ejemplo: ¿Qué sets de Star Wars tengo?")
    if st.button("Buscar"):
        if not pregunta.strip():
            st.warning("Escribe una pregunta antes de buscar.")
        else:
            with st.spinner("Buscando en tu colección..."):
                try:
                    resp = requests.post(LAMBDA_SEARCH, json={"pregunta": pregunta}, timeout=40)
                    if resp.status_code == 200:
                        data = resp.json()
                        body = data.get("body")
                        if isinstance(body, str):
                            data = json.loads(body)
                        st.success(data.get("respuesta", ""))
                        resultados = data.get("resultados", [])
                        if resultados:
                            mostrar_resultados(resultados)
                        else:
                            st.info("No se encontraron resultados.")
                    else:
                        st.error(f"Error {resp.status_code}: {resp.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# ============================================================
# TAB 2: LISTADO
# ============================================================
with tab2:
    tema = st.selectbox("Selecciona un tema:", ["Star Wars", "Technic", "Ideas", "F1"])
    if st.button("Mostrar"):
        with st.spinner(f"Obteniendo sets de {tema}..."):
            try:
                resp = requests.post(LAMBDA_SEARCH_FILTER, json={"tema": tema}, timeout=40)
                if resp.status_code == 200:
                    data = resp.json()
                    body = data.get("body")
                    if isinstance(body, str):
                        data = json.loads(body)
                    resultados = data.get("resultados", [])
                    if resultados:
                        mostrar_resultados(resultados)
                    else:
                        st.info("No hay sets registrados en ese tema.")
                else:
                    st.error(f"Error {resp.status_code}: {resp.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# ============================================================
# TAB 3: ADMINISTRAR
# ============================================================
with tab3:
    accion = st.radio("Acción", ["Alta", "Baja", "Actualización"], horizontal=True)
    st.divider()

    set_number = st.text_input("Número de set")
    name = st.text_input("Nombre")
    theme = st.text_input("Tema (ej. Star Wars)")
    year = st.number_input("Año", 1970, 2030, step=1)
    pieces = st.number_input("Piezas", 0, step=10)
    storage = st.text_input("Ubicación (ej. Cobalto)")
    storage_box = st.text_input("Caja")
    condition = st.text_input("Condición (ej. In Lego Box)")
    image = st.file_uploader("Imagen del set", type=["jpg", "jpeg", "png", "webp"])
    lego_web_url = st.text_input("URL LEGO", placeholder="https://www.lego.com/...")
    manuals = st.text_area("Manuales (uno por línea)")
    minifigs = st.text_area("Minifigs (número: nombre por línea)")
    tags = st.text_input("Tags (separados por comas)")

    if st.button("Enviar"):
        try:
            set_number_int = int(set_number)
            imagen_base64 = convertir_a_base64(image) if image else None
            payload = {"accion": accion.lower()}

            if accion == "alta":
                lego = {
                    "set_number": set_number_int,
                    "name": name,
                    "theme": theme,
                    "year": year,
                    "pieces": pieces,
                    "storage": storage,
                    "storage_box": storage_box,
                    "condition": condition,
                    "lego_web_url": lego_web_url,
                    "manuals": [m.strip() for m in manuals.splitlines() if m.strip()],
                    "minifigs_names": [x.split(":")[1].strip() for x in minifigs.splitlines() if ":" in x],
                    "minifigs_numbers": [x.split(":")[0].strip() for x in minifigs.splitlines() if ":" in x],
                    "tags": [t.strip() for t in tags.split(",") if t.strip()],
                    "created_at": datetime.utcnow().isoformat(),
                }
                if imagen_base64:
                    lego["imagen_base64"] = imagen_base64
                payload["lego"] = lego

            elif accion == "baja":
                payload["set_number"] = set_number_int

            else:  # actualización
                campos = {
                    "name": name,
                    "theme": theme,
                    "year": year,
                    "pieces": pieces,
                    "storage": storage,
                    "storage_box": storage_box,
                    "condition": condition,
                    "lego_web_url": lego_web_url,
                    "manuals": [m.strip() for m in manuals.splitlines() if m.strip()],
                    "minifigs_names": [x.split(":")[1].strip() for x in minifigs.splitlines() if ":" in x],
                    "minifigs_numbers": [x.split(":")[0].strip() for x in minifigs.splitlines() if ":" in x],
                    "tags": [t.strip() for t in tags.split(",") if t.strip()],
                    "modified_at": datetime.utcnow().isoformat(),
                }
                if imagen_base64:
                    campos["imagen_base64"] = imagen_base64
                payload["set_number"] = set_number_int
                payload["campos"] = {k: v for k, v in campos.items() if v not in ["", None, [], 0]}

            with st.spinner("Enviando datos..."):
                r = requests.post(LAMBDA_ADMIN, json=payload, timeout=40)
                data = r.json()
                if r.status_code == 200:
                    st.success(data.get("mensaje", "Operación completada."))
                    if data.get("image_url"):
                        st.image(data["image_url"], width=200)
                else:
                    st.error(data.get("error", "Error desconocido."))
        except Exception as e:
            st.error(f"Error: {str(e)}")

# ------------------------------------------------------------
# PIE
# ------------------------------------------------------------
st.markdown("---")
st.caption("Minimal LEGO IA · Desarrollado por Mike Nava")

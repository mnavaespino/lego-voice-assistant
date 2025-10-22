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
# TAB 1: BUSCAR (Expander con título limpio)
# ============================================================
with tab1:
    pregunta = st.text_input("🔍 Pregunta", placeholder="Ejemplo: ¿Qué sets de Star Wars tengo?")
    if st.button("Buscar"):
        if not pregunta.strip():
            st.warning("Escribe una pregunta.")
        else:
            with st.spinner("Buscando..."):
                try:
                    resp = requests.post(LAMBDA_SEARCH, json={"pregunta": pregunta}, timeout=40)
                    if resp.status_code != 200:
                        st.error(f"Error {resp.status_code}: {resp.text}")
                    else:
                        data = resp.json()
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
# TAB 2: ADMINISTRAR CATÁLOGO
# ============================================================
with tab2:
    accion = st.radio("Acción", ["Alta", "Baja", "Actualizacion"], horizontal=True)
    st.divider()

    set_number = st.text_input("Número de set")
    name = st.text_input("Nombre")
    theme = st.selectbox("Tema", ["StarWars", "Technic", "Ideas", "F1"])
    year = st.number_input("Año", min_value=1970, max_value=2030, step=1)
    pieces = st.number_input("Piezas", min_value=0, step=10)
    storage = st.selectbox("Ubicación", ["Cobalto", "San Geronimo"])
    storage_box = st.number_input("Caja", min_value=0, step=1)
    condition = st.selectbox("Condición", ["In Lego Box", "Open"])

    imagen_archivo = None
    if accion in ["Alta", "Actualizacion"]:
        imagen_archivo = st.file_uploader("📸 Selecciona imagen del set", type=["jpg", "jpeg", "webp"])

    lego_web_url = st.text_input("URL página LEGO (opcional)", placeholder="https://www.lego.com/...")
    manuals = st.text_area("Manuales (uno por línea)")
    minifigs = st.text_area("Minifigs (formato: número: nombre por línea, ej. SW1378: Ackbar Trooper)")
    tags = st.text_area("Tags (separados por comas)", placeholder="nave, star wars, exclusivo")

    if st.button("Enviar"):
        try:
            set_number_int = int(set_number)
            manual_list = [m.strip() for m in manuals.splitlines() if m.strip()]

            minifigs_names = []
            minifigs_numbers = []
            for line in minifigs.splitlines():
                p = [x.strip() for x in line.split(":")]
                if len(p) == 2:
                    minifigs_names.append(p[1])
                    minifigs_numbers.append(p[0])

            tags_list = [t.strip() for t in tags.split(",") if t.strip()]
            payload = {"accion": accion.lower()}
            imagen_base64 = convertir_a_base64(imagen_archivo) if imagen_archivo else None

            if accion == "Alta":
                payload["lego"] = {
                    "set_number": set_number_int,
                    "name": name,
                    "theme": theme,
                    "year": year,
                    "pieces": pieces,
                    "storage": storage,
                    "storage_box": storage_box,
                    "condition": condition,
                    "lego_web_url": lego_web_url,
                    "manuals": manual_list,
                    "minifigs_names": minifigs_names,
                    "minifigs_numbers": minifigs_numbers,
                    "tags": tags_list,
                    "created_at": datetime.utcnow().isoformat(),
                }
                if imagen_base64:
                    payload["lego"]["imagen_base64"] = imagen_base64
            elif accion == "Baja":
                payload["set_number"] = set_number_int
            else:
                campos = {
                    "name": name,
                    "theme": theme,
                    "year": year,
                    "pieces": pieces,
                    "storage": storage,
                    "storage_box": storage_box,
                    "condition": condition,
                    "lego_web_url": lego_web_url,
                    "manuals": manual_list,
                    "minifigs_names": minifigs_names,
                    "minifigs_numbers": minifigs_numbers,
                    "tags": tags_list,
                    "modified_at": datetime.utcnow().isoformat(),
                }
                if imagen_base64:
                    campos["imagen_base64"] = imagen_base64
                campos_filtrados = {k: v for k, v in campos.items() if v not in ["", None, [], 0]}
                payload["set_number"] = set_number_int
                payload["campos"] = campos_filtrados

            with st.spinner("Enviando datos a LEGO Admin..."):
                r = requests.post(LAMBDA_ADMIN, json=payload, timeout=40)
                try:
                    respuesta = r.json()
                except:
                    st.error(f"Error {r.status_code}: {r.text}")
                    st.stop()

                if r.status_code == 200:
                    mensaje = respuesta.get("mensaje", "Operación completada.")
                    image_url = respuesta.get("image_url")
                    st.success(mensaje)
                    if image_url:
                        st.image(image_url, caption="Imagen subida a Firebase", width=250)
                else:
                    st.error(f"Error {r.status_code}: {respuesta.get('error', r.text)}")

        except Exception as e:
            st.error(f"Ocurrió un error: {str(e)}")

# ============================================================
# TAB 3: LISTADO (Miniatura visible en título)
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

                            # Miniatura pequeña visible en la línea del expander
                            if thumb:
                                titulo = f"<div style='display:flex;align-items:center;gap:10px;'><img src='{thumb}' width='60'><b>{set_number} · {name}</b></div>"
                            else:
                                titulo = f"**{set_number} · {name}**"

                            with st.expander(resumen):
                                st.markdown(titulo, unsafe_allow_html=True)
                                mostrar_detalle_expandido(set_data)
                else:
                    st.error(f"Error {r.status_code}: {r.text}")
        except Exception as e:
            st.error(f"Ocurrió un error: {str(e)}")

# ------------------------------------------------------------
# PIE
# ------------------------------------------------------------
st.markdown("---")
st.caption("Desarrollado por Mike Nava · Firestore + OpenAI + AWS Lambda + Streamlit")

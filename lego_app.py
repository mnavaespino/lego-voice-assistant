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

def mostrar_detalle_set(set_data):
    """Muestra una vista de detalle del set seleccionado"""
    st.button("← Volver al listado", on_click=lambda: st.session_state.pop("set_seleccionado", None))
    st.markdown(f"## {set_data.get('set_number', '')} · {set_data.get('name', '')}")
    st.caption(f"{set_data.get('theme', '')} · {set_data.get('year', '')}")
    st.image(set_data.get("image_url", ""), width=400)

    st.markdown(
        f"""
        **🧩 Piezas:** {set_data.get('pieces', '')}  
        **🎁 Condición:** {set_data.get('condition', '')}  
        **🏠 Ubicación:** {set_data.get('storage', '')}  
        **📦 Caja:** {set_data.get('storage_box', '')}  
        """
    )

    manuals = set_data.get("manuals", [])
    if manuals:
        links = [f"[Manual {i+1}]({m})" for i, m in enumerate(manuals)]
        st.markdown("**📘 Manuales:** " + " · ".join(links))

    minifigs = set_data.get("minifigs_names", [])
    numbers = set_data.get("minifigs_numbers", [])
    if minifigs:
        figs = ", ".join([f"{n} ({num})" for n, num in zip(minifigs, numbers)])
        st.markdown(f"**🧍 Minifigs:** {figs}")

    lego_web = set_data.get("lego_web_url", "")
    if lego_web:
        st.markdown(f"[🌐 Página oficial LEGO]({lego_web})")

    st.markdown("---")

# ------------------------------------------------------------
# PESTAÑAS
# ------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🔍 Buscar", "⚙️ Administrar", "📦 Listado"])

# ============================================================
# TAB 1: BUSCAR
# ============================================================
with tab1:
    if "set_seleccionado" not in st.session_state:
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

                            respuesta = re.sub(r"!\[.*?\]\(\s*\)", "", data.get("respuesta", ""))
                            st.markdown(f"### 💬 {respuesta}")

                            resultados = data.get("resultados", [])
                            if not resultados:
                                st.info("No se encontraron resultados.")
                            else:
                                for i, set_data in enumerate(resultados):
                                    thumb = set_data.get("thumb_url", set_data.get("image_url", ""))
                                    st.image(thumb, width=180)
                                    st.markdown(f"**{set_data.get('set_number', '')} · {set_data.get('name', '')}**")
                                    st.caption(f"{set_data.get('theme', '')} · {set_data.get('year', '')} · 🧩 {set_data.get('pieces', '')} piezas")
                                    st.caption(f"🎁 {set_data.get('condition', '')} · 🏠 {set_data.get('storage', '')}")
                                    if st.button(f"Ver detalles {i}", key=f"detalle_{i}"):
                                        st.session_state["set_seleccionado"] = set_data
                                        st.experimental_rerun()
                                    st.markdown("---")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    else:
        mostrar_detalle_set(st.session_state["set_seleccionado"])

# ============================================================
# TAB 2: ADMINISTRAR
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
            minifigs_names, minifigs_numbers = [], []
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
                    "set_number": set_number_int, "name": name, "theme": theme, "year": year,
                    "pieces": pieces, "storage": storage, "storage_box": storage_box,
                    "condition": condition, "lego_web_url": lego_web_url, "manuals": manual_list,
                    "minifigs_names": minifigs_names, "minifigs_numbers": minifigs_numbers,
                    "tags": tags_list, "created_at": datetime.utcnow().isoformat(),
                }
                if imagen_base64:
                    payload["lego"]["imagen_base64"] = imagen_base64
            elif accion == "Baja":
                payload["set_number"] = set_number_int
            else:
                campos = {
                    "name": name, "theme": theme, "year": year, "pieces": pieces,
                    "storage": storage, "storage_box": storage_box, "condition": condition,
                    "lego_web_url": lego_web_url, "manuals": manual_list,
                    "minifigs_names": minifigs_names, "minifigs_numbers": minifigs_numbers,
                    "tags": tags_list, "modified_at": datetime.utcnow().isoformat(),
                }
                if imagen_base64:
                    campos["imagen_base64"] = imagen_base64
                payload["set_number"] = set_number_int
                payload["campos"] = {k: v for k, v in campos.items() if v not in ["", None, [], 0]}

            with st.spinner("Enviando datos a LEGO Admin..."):
                r = requests.post(LAMBDA_ADMIN, json=payload, timeout=40)
                if r.status_code == 200:
                    respuesta = r.json()
                    st.success(respuesta.get("mensaje", "Operación completada."))
                    if "image_url" in respuesta:
                        st.image(respuesta["image_url"], caption="Imagen subida a Firebase", width=250)
                else:
                    st.error(f"Error {r.status_code}: {r.text}")
        except Exception as e:
            st.error(f"Ocurrió un error: {str(e)}")

# ============================================================
# TAB 3: LISTADO POR TEMA
# ============================================================
with tab3:
    if "set_seleccionado_tab3" not in st.session_state:
        st.subheader("📦 Listado de sets por tema")
        tema = st.selectbox("Selecciona el tema a mostrar:", ["Star Wars", "Technic", "Ideas", "F1"])

        if st.button("Mostrar sets"):
            try:
                with st.spinner(f"Obteniendo sets de {tema}..."):
                    r = requests.post(LAMBDA_SEARCH_FILTER, json={"tema": tema}, timeout=40)
                    if r.status_code == 200:
                        data = r.json()
                        body = data.get("body")
                        if isinstance(body, str):
                            data = json.loads(body)

                        resultados = data.get("resultados", [])
                        if not resultados:
                            st.info(f"No hay sets registrados en el tema {tema}.")
                        else:
                            for i, set_data in enumerate(resultados):
                                thumb = set_data.get("thumb_url", set_data.get("image_url", ""))
                                st.image(thumb, width=180)
                                st.markdown(f"**{set_data.get('set_number', '')} · {set_data.get('name', '')}**")
                                st.caption(f"{set_data.get('year', '')} · 🧩 {set_data.get('pieces', '')} piezas · 🎁 {set_data.get('condition', '')}")
                                if st.button(f"Ver detalles tab3 {i}", key=f"detalle_tab3_{i}"):
                                    st.session_state["set_seleccionado_tab3"] = set_data
                                    st.experimental_rerun()
                                st.markdown("---")
                    else:
                        st.error(f"Error {r.status_code}: {r.text}")
            except Exception as e:
                st.error(f"Ocurrió un error: {str(e)}")
    else:
        mostrar_detalle_set(st.session_state["set_seleccionado_tab3"])

# ------------------------------------------------------------
# PIE
# ------------------------------------------------------------
st.markdown("---")
st.caption("Desarrollado por Mike Nava · Firestore + OpenAI + AWS Lambda + Streamlit")

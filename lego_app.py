import streamlit as st
import requests
import re
import json
from datetime import datetime
import pandas as pd
import base64

# ------------------------------------------------------------
# CONVERTIR LINKS DE GOOGLE DRIVE
# ------------------------------------------------------------
def convertir_enlace_drive(url):
    if not url or "drive.google.com" not in url:
        return url
    patron = r"/d/([a-zA-Z0-9_-]+)"
    m = re.search(patron, url)
    if m:
        return f"https://drive.google.com/uc?export=view&id={m.group(1)}"
    patron = r"id=([a-zA-Z0-9_-]+)"
    m = re.search(patron, url)
    if m:
        return f"https://drive.google.com/uc?export=view&id={m.group(1)}"
    return url


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
# PESTAÑAS
# ------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🔍 Buscar", "⚙️ Administrar", "📦 Listado"])

# ============================================================
# TAB 1: BUSCAR EN CATÁLOGO
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

                        respuesta = re.sub(r"!\[.*?\]\(\s*\)", "", data.get("respuesta", ""))
                        st.markdown(f"**{respuesta}**")

                        resultados = data.get("resultados", [])
                        for item in resultados:
                            nombre = item.get("name", "Sin nombre")
                            set_number = item.get("set_number", "")
                            year = item.get("year", "")
                            theme = item.get("theme", "")
                            piezas = item.get("pieces", "")
                            storage = item.get("storage", "")
                            storage_box = item.get("storage_box", "")
                            condition = item.get("condition", "")
                            image_url = convertir_enlace_drive(item.get("image_url", ""))
                            manuals = item.get("manuals", [])
                            minifigs_names = item.get("minifigs_names", [])
                            minifigs_numbers = item.get("minifigs_numbers", [])
                            lego_web_url = item.get("lego_web_url", "")

                            with st.container(border=True):
                                st.markdown(f"### {set_number} · {nombre}")
                                st.caption(f"{theme} · {year}")

                                linea_detalle = f"🧩 {piezas} piezas · 🏠 {storage}"
                                if storage_box and int(storage_box) != 0:
                                    linea_detalle += f" · 📦 Caja {storage_box}"
                                linea_detalle += f" · 🎁 {condition}"
                                st.caption(linea_detalle)

                                if image_url:
                                    st.image(image_url, width=250)
                                if lego_web_url:
                                    st.markdown(f"[🌐 Página oficial LEGO]({lego_web_url})")

                                if manuals:
                                    links = [f"[{i+1} · Ver]({m})" for i, m in enumerate(manuals)]
                                    st.markdown("**📘 Manuales:** " + " · ".join(links))

                                if minifigs_names and minifigs_numbers:
                                    figs = ", ".join(
                                        [f"{n} ({num})" for n, num in zip(minifigs_names, minifigs_numbers)]
                                    )
                                    st.markdown(f"**🧍 Minifigs:** {figs}")

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
    theme = st.selectbox("Tema", ["Star Wars", "Technic", "Ideas", "F1"])
    year = st.number_input("Año", min_value=1970, max_value=2030, step=1)
    pieces = st.number_input("Piezas", min_value=0, step=10)
    storage = st.selectbox("Ubicación", ["Cobalto", "San Geronimo"])
    storage_box = st.number_input("Caja", min_value=0, step=1)
    condition = st.selectbox("Condición", ["In Lego Box", "Open"])

    # 👇 NUEVO: carga y vista previa de imagen
    image_file = st.file_uploader("📷 Subir imagen del set (JPG o WebP)", type=["jpg", "jpeg", "webp"])
    if image_file:
        st.image(image_file, caption="Vista previa", width=250)

    image_url = st.text_input("URL imagen (alternativa)", placeholder="https://drive.google.com/...")
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

            # Si hay imagen subida, convertir a base64
            imagen_base64 = None
            if image_file is not None:
                bytes_data = image_file.read()
                mime_type = "image/webp" if image_file.type == "image/webp" else "image/jpeg"
                encoded = base64.b64encode(bytes_data).decode("utf-8")
                imagen_base64 = f"data:{mime_type};base64,{encoded}"

            if accion == "Alta":
                lego_data = {
                    "set_number": set_number_int,
                    "name": name,
                    "theme": theme,
                    "year": year,
                    "pieces": pieces,
                    "storage": storage,
                    "storage_box": storage_box,
                    "condition": condition,
                    "image_url": convertir_enlace_drive(image_url),
                    "lego_web_url": lego_web_url,
                    "manuals": manual_list,
                    "minifigs_names": minifigs_names,
                    "minifigs_numbers": minifigs_numbers,
                    "tags": tags_list,
                    "created_at": datetime.utcnow().isoformat()
                }
                if imagen_base64:
                    lego_data["imagen_base64"] = imagen_base64
                payload["lego"] = lego_data

            elif accion == "Baja":
                payload["set_number"] = set_number_int

            else:  # Actualización
                campos = {
                    "name": name,
                    "theme": theme,
                    "year": year,
                    "pieces": pieces,
                    "storage": storage,
                    "storage_box": storage_box,
                    "condition": condition,
                    "image_url": convertir_enlace_drive(image_url),
                    "lego_web_url": lego_web_url,
                    "manuals": manual_list,
                    "minifigs_names": minifigs_names,
                    "minifigs_numbers": minifigs_numbers,
                    "tags": tags_list,
                    "modified_at": datetime.utcnow().isoformat()
                }
                if imagen_base64:
                    campos["imagen_base64"] = imagen_base64
                campos_filtrados = {k: v for k, v in campos.items() if v not in ["", None, [], 0]}
                payload["set_number"] = set_number_int
                payload["campos"] = campos_filtrados

            r = requests.post(LAMBDA_ADMIN, json=payload, timeout=60)
            if r.status_code == 200:
                try:
                    data = r.json()
                    if isinstance(data.get("body"), str):
                        data = json.loads(data["body"])
                    mensaje = data.get("mensaje", "Operación completada.")
                    image_url_result = data.get("image_url")
                    if image_url_result:
                        st.image(image_url_result, width=300)
                    st.success(mensaje)
                except Exception:
                    st.success("Operación completada.")
            else:
                st.error(f"Error {r.status_code}: {r.text}")
        except Exception as e:
            st.error(f"Ocurrió un error: {str(e)}")

# ============================================================
# TAB 3: LISTADO POR TEMA (usando legoSearchFilter)
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
                        df = pd.DataFrame(resultados)
                        columnas = ["set_number", "name", "year", "pieces", "condition", "storage", "storage_box"]
                        columnas_presentes = [c for c in columnas if c in df.columns]
                        df = df[columnas_presentes]
                        df["set_number"] = df["set_number"].apply(lambda x: f"**{x}**")
                        st.data_editor(df, use_container_width=True, hide_index=True, disabled=True)
                else:
                    st.error(f"Error {r.status_code}: {r.text}")
        except Exception as e:
            st.error(f"Ocurrió un error: {str(e)}")

# ------------------------------------------------------------
# PIE
# ------------------------------------------------------------
st.markdown("---")
st.caption("Desarrollado por Mike Nava · Firestore + OpenAI + AWS Lambda + Streamlit")

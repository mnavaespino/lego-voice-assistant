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
# FUNCIÓN PARA CONVERTIR IMAGEN A BASE64
# ------------------------------------------------------------
def convertir_a_base64(archivo):
    if archivo is None:
        return None
    contenido = archivo.read()
    b64 = base64.b64encode(contenido).decode("utf-8")
    tipo = archivo.type
    return f"data:{tipo};base64,{b64}"

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
                            image_url = item.get("image_url", "")
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
# TAB 3: LISTADO POR TEMA (tabla con miniaturas)
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

                        # Usar thumb_url si existe, si no image_url
                        if "thumb_url" in df.columns:
                            df["imagen"] = df["thumb_url"]
                        else:
                            df["imagen"] = df["image_url"]

                        # Crear tabla HTML renderizada
                        html = """
                        <style>
                            table {
                                width: 100%;
                                border-collapse: collapse;
                                font-size: 14px;
                            }
                            th, td {
                                padding: 8px;
                                text-align: left;
                                border-bottom: 1px solid #eee;
                            }
                            th {
                                background-color: #f0f0f0;
                            }
                            img {
                                border-radius: 6px;
                            }
                        </style>
                        <table>
                            <thead>
                                <tr>
                                    <th>Imagen</th>
                                    <th>Set</th>
                                    <th>Nombre</th>
                                    <th>Año</th>
                                    <th>Piezas</th>
                                    <th>Condición</th>
                                    <th>Ubicación</th>
                                    <th>Caja</th>
                                </tr>
                            </thead>
                            <tbody>
                        """

                        for _, row in df.iterrows():
                            imagen = row.get("imagen", "")
                            image_html = (
                                f'<img src="{imagen}" width="80">' if imagen
                                else '<div style="width:80px;height:80px;background:#ddd;border-radius:6px;text-align:center;line-height:80px;">—</div>'
                            )
                            html += f"""
                                <tr>
                                    <td>{image_html}</td>
                                    <td style="font-weight:bold;">{row.get("set_number", "")}</td>
                                    <td>{row.get("name", "")}</td>
                                    <td>{row.get("year", "")}</td>
                                    <td>{row.get("pieces", "")}</td>
                                    <td>{row.get("condition", "")}</td>
                                    <td>{row.get("storage", "")}</td>
                                    <td>{row.get("storage_box", "")}</td>
                                </tr>
                            """

                        html += "</tbody></table>"
                        st.markdown(html, unsafe_allow_html=True)

                else:
                    st.error(f"Error {r.status_code}: {r.text}")
        except Exception as e:
            st.error(f"Ocurrió un error: {str(e)}")

# ------------------------------------------------------------
# PIE
# ------------------------------------------------------------
st.markdown("---")
st.caption("Desarrollado por Mike Nava · Firestore + OpenAI + AWS Lambda + Streamlit")

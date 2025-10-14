import streamlit as st
import requests
import re
import json

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

tab1, tab2 = st.tabs(["🔍 Buscar", "⚙️ Administrar"])

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
                            minifig_names = item.get("minifig_names", [])
                            minifigs_numbers = item.get("minifigs_numbers", [])
                            lego_web_url = item.get("lego_web_url", "")

                            with st.container(border=True):
                                # 🔹 Mostrar número de set + nombre
                                st.markdown(f"### {set_number} · {nombre}")
                                st.caption(f"{theme} · {year}")

                                # 🔹 Línea con piezas, storage y caja (si aplica)
                                linea_detalle = f"🧩 {piezas} piezas · 🏠 {storage}"
                                if storage_box and int(storage_box) != 0:
                                    linea_detalle += f" · 📦 Caja {storage_box}"
                                linea_detalle += f" · 🎁 {condition}"
                                st.caption(linea_detalle)

                                # 🔗 Imagen y links
                                if image_url:
                                    st.markdown(f"[🖼️ Imagen del set]({image_url})")
                                if lego_web_url:
                                    st.markdown(f"[🌐 Página oficial LEGO]({lego_web_url})")

                                # 📘 Manuales con índice
                                if manuals:
                                    links = [f"[{i+1} · Ver]({m})" for i, m in enumerate(manuals)]
                                    st.markdown("**📘 Manuales:** " + " · ".join(links))

                                # 🧍 Minifigs
                                if minifig_names and minifigs_numbers:
                                    figs = ", ".join(
                                        [f"{n} ({num})" for n, num in zip(minifig_names, minifigs_numbers)]
                                    )
                                    st.markdown(f"**🧍 Minifigs:** {figs}")

                except Exception as e:
                    st.error(f"Error: {str(e)}")

# ============================================================
# TAB 2: ADMINISTRAR CATÁLOGO
# ============================================================
with tab2:
    accion = st.radio("Acción", ["Alta", "Baja", "Actualización"], horizontal=True)
    st.divider()

    set_number = st.text_input("Número de set")
    name = st.text_input("Nombre")
    theme = st.selectbox("Tema", ["Star Wars", "Technic", "Ideas", "F1"])
    year = st.number_input("Año", min_value=1970, max_value=2030, step=1)
    pieces = st.number_input("Piezas", min_value=0, step=10)
    storage = st.selectbox("Ubicación", ["Cobalto", "San Geronimo"])
    storage_box = st.number_input("Caja", min_value=0, step=1)
    condition = st.selectbox("Condición", ["In Lego Box", "Open"])
    image_url = st.text_input("URL imagen", placeholder="https://drive.google.com/...")
    lego_web_url = st.text_input("URL página LEGO (opcional)", placeholder="https://www.lego.com/...")
    manuals = st.text_area("Manuales (uno por línea)")
    minifigs = st.text_area("Minifigs (formato: nombre|número por línea)")
    tags = st.text_area("Tags (separados por comas)", placeholder="nave, star wars, exclusivo")

    if st.button("Enviar"):
        try:
            set_number_int = int(set_number)
            manual_list = [m.strip() for m in manuals.splitlines() if m.strip()]

            # 🔹 Separar minifigs en dos listas
            minifig_names = []
            minifigs_numbers = []
            for line in minifigs.splitlines():
                p = [x.strip() for x in line.split("|")]
                if len(p) == 2:
                    minifig_names.append(p[0])
                    minifigs_numbers.append(p[1])

            tags_list = [t.strip() for t in tags.split(",") if t.strip()]

            payload = {"accion": accion.lower()}

            # --------------------------------------------------------
            # ALTA
            # --------------------------------------------------------
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
                    "image_url": convertir_enlace_drive(image_url),
                    "lego_web_url": lego_web_url,
                    "manuals": manual_list,
                    "minifig_names": minifig_names,
                    "minifigs_numbers": minifigs_numbers,
                    "tags": tags_list,
                    "created_at": datetime.utcnow().isoformat()
                }

            # --------------------------------------------------------
            # BAJA
            # --------------------------------------------------------
            elif accion == "Baja":
                payload["set_number"] = set_number_int

            # --------------------------------------------------------
            # ACTUALIZACIÓN
            # --------------------------------------------------------
            else:
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
                    "minifig_names": minifig_names,
                    "minifigs_numbers": minifigs_numbers,
                    "tags": tags_list,
                }
                campos_filtrados = {k: v for k, v in campos.items() if v not in ["", None, [], 0]}
                payload["set_number"] = set_number_int
                payload["campos"] = campos_filtrados

            # 🔹 Enviar solicitud a Lambda
            r = requests.post(LAMBDA_ADMIN, json=payload, timeout=30)
            if r.status_code == 200:
                st.success(r.json().get("mensaje", "Operación completada."))
            else:
                st.error(f"Error {r.status_code}: {r.text}")

        except Exception as e:
            st.error(f"Ocurrió un error: {str(e)}")

# ------------------------------------------------------------
# PIE
# ------------------------------------------------------------
st.markdown("---")
st.caption("Desarrollado por Mike Nava · Firestore + OpenAI + AWS Lambda + Streamlit")

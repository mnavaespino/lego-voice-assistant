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

tab1, tab2 = st.tabs(["Buscar", "Administrar"])

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
                            storage_box = item.get("storage_box", "")
                            condition = item.get("condition", "")
                            image_url = convertir_enlace_drive(item.get("image_url", ""))
                            manuals = item.get("manuals", [])
                            minifigs = item.get("minifigs", [])

                            with st.container(border=True):
                                st.markdown(f"### {nombre}")
                                st.caption(f"{set_number} · {theme} · {year}")
                                st.caption(f"🧩 {piezas} piezas · Caja {storage_box} · {condition}")

                                if image_url:
                                    st.markdown(f"[🖼️ Imagen del set]({image_url})")

                                if manuals:
                                    st.markdown("**📘 Manuales:** " + " · ".join(
                                        [f"[Ver]({m})" for m in manuals]
                                    ))

                                if minifigs:
                                    figs = ", ".join([f"{f['minifig_name']} ({f['minifig_number']})" for f in minifigs])
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
    manuals = st.text_area("Manuales (uno por línea)")
    minifigs = st.text_area("Minifigs (nombre|número por línea)")

    if st.button("Enviar"):
        try:
            set_number_int = int(set_number)
            manual_list = [m.strip() for m in manuals.splitlines() if m.strip()]
            minifig_list = []
            for line in minifigs.splitlines():
                p = [x.strip() for x in line.split("|")]
                if len(p) == 2:
                    minifig_list.append({"minifig_name": p[0], "minifig_number": p[1]})

            payload = {"accion": accion.lower()}

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
                    "manuals": manual_list,
                    "minifigs": minifig_list,
                }
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
                    "image_url": convertir_enlace_drive(image_url),
                    "manuals": manual_list,
                    "minifigs": minifig_list,
                }
                payload["set_number"] = set_number_int
                payload["campos"] = {k: v for k, v in campos.items() if v not in ["", None, [], 0]}

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

import streamlit as st
import requests
import re
import json
from datetime import datetime
from bs4 import BeautifulSoup

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
# FUNCIÓN: obtener datos desde LEGO.com
# ------------------------------------------------------------
def obtener_datos_lego(set_number):
    try:
        url = f"https://www.lego.com/es-mx/product/{set_number}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15, verify=False)

        if r.status_code != 200:
            return {"error": f"No se pudo acceder ({r.status_code})"}

        soup = BeautifulSoup(r.text, "html.parser")

        nombre = soup.find("h1").text.strip() if soup.find("h1") else ""
        descripcion = ""
        desc_tag = soup.find("div", {"data-test": "product-details__description"})
        if desc_tag:
            descripcion = desc_tag.text.strip()

        piezas = None
        for li in soup.find_all("li"):
            if "Piezas" in li.text:
                piezas = re.sub(r"\D", "", li.text)
                break

        edad = None
        for li in soup.find_all("li"):
            if "Edad" in li.text:
                edad = li.text.replace("Edad", "").strip()
                break

        precio = None
        for span in soup.find_all("span"):
            if "$" in span.text and "MXN" in span.text:
                precio = span.text.strip()
                break

        tema = None
        breadcrumb = soup.find("nav", {"aria-label": "breadcrumb"})
        if breadcrumb:
            partes = [a.text.strip() for a in breadcrumb.find_all("a")]
            if len(partes) > 1:
                tema = partes[1]

        imagen_tag = soup.find("img", {"class": re.compile("ProductOverviewstyles__ProductImage")})
        imagen = imagen_tag["src"] if imagen_tag else ""

        return {
            "set_number": set_number,
            "name": nombre,
            "theme": tema or "",
            "pieces": int(piezas) if piezas else 0,
            "lego_web_url": url,
            "image_url": imagen,
            "precio": precio or "",
            "edad": edad or "",
            "descripcion": descripcion or ""
        }

    except Exception as e:
        return {"error": str(e)}


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
# (SIN CAMBIOS)
# ============================================================
# ... (todo igual que tu versión actual)
# ============================================================


# ============================================================
# TAB 2: ADMINISTRAR CATÁLOGO
# ============================================================
with tab2:
    accion = st.radio("Acción", ["Alta", "Baja", "Actualizacion"], horizontal=True)
    st.divider()

    # --------------------------------------------------------
    # NUEVO BLOQUE: BUSCAR EN LEGO.COM (solo si es Alta)
    # --------------------------------------------------------
    if accion == "Alta":
        set_number = st.text_input("Número de set")
        if st.button("Buscar en LEGO.com"):
            if not set_number.strip():
                st.warning("Escribe un número de set.")
            else:
                with st.spinner("Buscando en LEGO.com..."):
                    datos = obtener_datos_lego(set_number.strip())
                    if "error" in datos:
                        st.error(datos["error"])
                    else:
                        st.session_state["lego_prefill"] = datos
                        st.success("Datos obtenidos desde LEGO.com")

        datos_previos = st.session_state.get("lego_prefill", {})
    else:
        set_number = st.text_input("Número de set")
        datos_previos = {}

    # --------------------------------------------------------
    # FORMULARIO DE CAMPOS
    # --------------------------------------------------------
    name = st.text_input("Nombre", value=datos_previos.get("name", ""))
    theme = st.selectbox(
        "Tema", 
        ["", "Star Wars", "Technic", "Ideas", "F1", "City", "Friends"], 
        index=0 if not datos_previos.get("theme") else
        ["", "Star Wars", "Technic", "Ideas", "F1", "City", "Friends"].index(datos_previos.get("theme")) 
        if datos_previos.get("theme") in ["Star Wars", "Technic", "Ideas", "F1", "City", "Friends"] else 0
    )
    year = st.number_input("Año", min_value=1970, max_value=2030, step=1)
    pieces = st.number_input("Piezas", min_value=0, step=10, value=datos_previos.get("pieces", 0))
    storage = st.selectbox("Ubicación", ["Cobalto", "San Geronimo"])
    storage_box = st.number_input("Caja", min_value=0, step=1)
    condition = st.selectbox("Condición", ["In Lego Box", "Open"])
    image_url = st.text_input("URL imagen", value=datos_previos.get("image_url", ""), placeholder="https://drive.google.com/...")
    lego_web_url = st.text_input("URL página LEGO", value=datos_previos.get("lego_web_url", ""), placeholder="https://www.lego.com/...")
    manuals = st.text_area("Manuales (uno por línea)")
    minifigs = st.text_area("Minifigs (nombre|número por línea)")
    tags = st.text_area("Tags (separados por comas)", placeholder="nave, star wars, exclusivo")

    # --------------------------------------------------------
    # BOTÓN ENVIAR (misma lógica que antes)
    # --------------------------------------------------------
    if st.button("Enviar"):
        try:
            set_number_int = int(set_number)
            manual_list = [m.strip() for m in manuals.splitlines() if m.strip()]

            minifigs_names = []
            minifigs_numbers = []
            for line in minifigs.splitlines():
                p = [x.strip() for x in line.split("|")]
                if len(p) == 2:
                    minifigs_names.append(p[0])
                    minifigs_numbers.append(p[1])

            tags_list = [t.strip() for t in tags.split(",") if t.strip()]
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
                    "lego_web_url": lego_web_url,
                    "manuals": manual_list,
                    "minifigs_names": minifigs_names,
                    "minifigs_numbers": minifigs_numbers,
                    "tags": tags_list,
                    "created_at": datetime.utcnow().isoformat()
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
                    "lego_web_url": lego_web_url,
                    "manuals": manual_list,
                    "minifigs_names": minifigs_names,
                    "minifigs_numbers": minifigs_numbers,
                    "tags": tags_list,
                    "modified_at": datetime.utcnow().isoformat()
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

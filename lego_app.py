import streamlit as st
import requests
import json
import base64
from datetime import datetime

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
# FUNCIONES DE APOYO
# ------------------------------------------------------------
def convertir_a_base64(archivo):
    """Convierte una imagen a base64"""
    if archivo is None:
        return None
    contenido = archivo.read()
    b64 = base64.b64encode(contenido).decode("utf-8")
    return f"data:{archivo.type};base64,{b64}"


def mostrar_resultados(resultados):
    """Muestra los sets con detalles completos"""
    for r in resultados:
        st.markdown("---")
        cols = st.columns([1, 3])

        # Imagen
        with cols[0]:
            thumb = r.get("thumb_url") or r.get("image_url")
            full = r.get("image_url")
            if thumb:
                if full:
                    st.markdown(f"[![Set]({thumb})]({full})", unsafe_allow_html=True)
                else:
                    st.image(thumb, use_container_width=True)
            else:
                st.image("https://via.placeholder.com/150x100?text=No+Image", use_container_width=True)

        # Detalles
        with cols[1]:
            st.markdown(f"### {r.get('set_number','')} · {r.get('name','')}")
            st.caption(f"{r.get('theme','')} · {r.get('year','')} · 🧩 {r.get('pieces','')} piezas")
            st.write(f"🎁 **Condición:** {r.get('condition','')}")
            st.write(f"🏠 **Ubicación:** {r.get('storage','')} · 📦 Caja {r.get('storage_box','')}")

            if r.get("lego_web_url"):
                st.markdown(f"🔗 [Página oficial de LEGO]({r['lego_web_url']})")

            manuals = r.get("manuals", [])
            if manuals:
                st.markdown("📘 **Manuales:**")
                for m in manuals:
                    st.markdown(f"- [{m}]({m})")

            minifigs = r.get("minifigs_names", [])
            if minifigs:
                st.markdown("🧍‍♂️ **Minifigs:**")
                st.markdown("<br>".join([f"• {m}" for m in minifigs]), unsafe_allow_html=True)

            tags = r.get("tags", [])
            if tags:
                st.markdown(f"🏷️ **Tags:** {', '.join(tags)}")


# ------------------------------------------------------------
# PESTAÑAS
# ------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🔍 Buscar", "📦 Listado", "⚙️ Administrar"])

# ============================================================
# TAB 1: BUSCAR
# ============================================================
with tab1:
    pregunta = st.text_input("Pregunta:", placeholder="Ejemplo: ¿Qué sets de Star Wars tengo?")
    if st.button("Buscar"):
        if not pregunta.strip():
            st.warning("Escribe una pregunta antes de buscar.")
        else:
            with st.spinner("Buscando..."):
                try:
                    r = requests.post(LAMBDA_SEARCH, json={"pregunta": pregunta}, timeout=40)
                    if r.status_code == 200:
                        data = r.json()
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
                        st.error(f"Error {r.status_code}: {r.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# ============================================================
# TAB 2: LISTADO
# ============================================================
with tab2:
    tema = st.selectbox("Selecciona un tema:", ["Star Wars", "Technic", "Ideas", "F1"])
    if st.button("Mostrar sets"):
        with st.spinner(f"Obteniendo sets de {tema}..."):
            try:
                r = requests.post(LAMBDA_SEARCH_FILTER, json={"tema": tema}, timeout=40)
                if r.status_code == 200:
                    data = r.json()
                    body = data.get("body")
                    if isinstance(body, str):
                        data = json.loads(body)
                    resultados = data.get("resultados", [])
                    if resultados:
                        mostrar_resultados(resultados)
                    else:
                        st.info(f"No hay sets de {tema}.")
                else:
                    st.error(f"Error {r.status_code}: {r.text}")
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
    theme = st.selectbox("Tema", ["StarWars", "Technic", "Ideas", "F1"])
    year = st.number_input("Año", 1970, 2030, step=1)
    pieces = st.number_input("Piezas", 0, step=10)
    storage = st.selectbox("Ubicación", ["Cobalto", "San Geronimo"])
    storage_box = st.number_input("Caja", 0, step=1)
    condition = st.selectbox("Condición", ["In Lego Box", "Open"])

    imagen = None
    if accion in ["Alta", "Actualización"]:
        imagen = st.file_uploader("📸 Imagen del set", type=["jpg", "jpeg", "png", "webp"])

    lego_web_url = st.text_input("URL LEGO", placeholder="https://www.lego.com/...")
    manuals = st.text_area("Manuales (uno por línea)")
    minifigs = st.text_area("Minifigs (número: nombre por línea)")
    tags = st.text_input("Tags (separados por comas)")

    if st.button("Enviar"):
        try:
            if not set_number.strip():
                st.warning("Debe indicar el número de set.")
                st.stop()

            set_number_int = int(set_number)
            imagen_base64 = convertir_a_base64(imagen) if imagen else None
            accion_lower = accion.lower()
            payload = {"accion": accion_lower}

            # Campos comunes
            base_campos = {
                "set_number": set_number_int,
                "name": name.strip(),
                "theme": theme,
                "year": int(year),
                "pieces": int(pieces),
                "storage": storage,
                "storage_box": int(storage_box),
                "condition": condition,
                "lego_web_url": lego_web_url.strip(),
                "manuals": [m.strip() for m in manuals.splitlines() if m.strip()],
                "minifigs_names": [x.split(":")[1].strip() for x in minifigs.splitlines() if ":" in x],
                "minifigs_numbers": [x.split(":")[0].strip() for x in minifigs.splitlines() if ":" in x],
                "tags": [t.strip() for t in tags.split(",") if t.strip()],
            }

            if imagen_base64:
                base_campos["imagen_base64"] = imagen_base64

            # Alta
            if accion_lower == "alta":
                base_campos["created_at"] = datetime.utcnow().isoformat()
                payload["lego"] = base_campos

            # Baja
            elif accion_lower == "baja":
                payload["set_number"] = set_number_int

            # Actualización
            else:
                base_campos["modified_at"] = datetime.utcnow().isoformat()
                campos_filtrados = {k: v for k, v in base_campos.items() if v not in ["", None, [], 0]}
                payload["set_number"] = set_number_int
                payload["campos"] = campos_filtrados

            with st.spinner("Enviando datos a LEGO Admin..."):
                r = requests.post(LAMBDA_ADMIN, json=payload, timeout=40)
                try:
                    data = r.json()
                except:
                    st.error(f"Error {r.status_code}: {r.text}")
                    st.stop()

                if r.status_code == 200:
                    st.success(data.get("mensaje", "Operación completada."))
                    if data.get("image_url"):
                        st.image(data["image_url"], caption="Imagen subida a Firebase", width=250)
                else:
                    st.error(data.get("error", "Error desconocido."))

        except Exception as e:
            st.error(f"Ocurrió un error: {str(e)}")

# ------------------------------------------------------------
# PIE
# ------------------------------------------------------------
st.markdown("---")
st.caption("Minimal LEGO IA · Desarrollado por Mike Nava")

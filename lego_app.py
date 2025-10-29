import streamlit as st
import requests
import re
import json
import base64
from datetime import datetime
import pandas as pd
import streamlit.components.v1 as components

# ------------------------------------------------------------
# CONFIGURACIÓN GENERAL
# ------------------------------------------------------------
st.set_page_config(page_title="LEGO IA", page_icon="🧱", layout="centered")

# Encabezado minimalista
st.markdown(
    "<h2 style='text-align:center; margin-bottom:0;'>🧱 LEGO IA</h2>"
    "<p style='text-align:center; color:gray; margin-top:4px;'>Consulta y administra tu colección LEGO</p>",
    unsafe_allow_html=True
)

# ------------------------------------------------------------
# CONFIGURACIÓN DE ENDPOINTS
# ------------------------------------------------------------
LAMBDA_SEARCH = "https://ztpcx6dks9.execute-api.us-east-1.amazonaws.com/default/legoSearch"
LAMBDA_ADMIN = "https://nn41og73w2.execute-api.us-east-1.amazonaws.com/default/legoAdmin"
LAMBDA_SEARCH_FILTER = "https://pzj4u8wwxc.execute-api.us-east-1.amazonaws.com/default/legoSearchFilter"

# ------------------------------------------------------------
# ESTADOS GLOBALES
# ------------------------------------------------------------
if "editar_set" not in st.session_state:
    st.session_state["editar_set"] = None
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "Buscar"

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

def cargar_set_desde_lambda(set_number):
    """Consulta datos reales del set desde Lambda."""
    try:
        resp = requests.post(
            LAMBDA_ADMIN, json={"accion": "consulta", "set_number": int(set_number)}, timeout=40
        )
        if resp.status_code == 200:
            data = resp.json()
            body = data.get("body")
            if isinstance(body, str):
                data = json.loads(body)
            return data.get("lego", {})
        else:
            st.error(f"Error {resp.status_code}: {resp.text}")
            return None
    except Exception as e:
        st.error(f"Error al obtener set: {str(e)}")
        return None

def mostrar_sets(df, origen):
    """Renderiza cada set con botón Editar."""
    for _, row in df.iterrows():
        col1, col2 = st.columns([1, 3])
        with col1:
            img = row.get("thumb_url") or row.get("image_url")
            if img:
                st.image(img, width=100)
            else:
                st.markdown("🧱")
        with col2:
            st.markdown(f"**{row.get('set_number','')} · {row.get('name','')}**")
            st.caption(
                f"{row.get('theme','')} · {row.get('year','')} · 🧩 {row.get('pieces','')} piezas"
            )
            st.caption(
                f"🎁 {row.get('condition','')} · 🏠 {row.get('storage','')} · 📦 Caja {row.get('storage_box','')}"
            )
            if st.button("✏️ Editar", key=f"edit_{origen}_{row.get('set_number')}"):
                st.session_state["editar_set"] = row.get("set_number")
                st.session_state["active_tab"] = "Editar"
                st.experimental_rerun()
        st.divider()

# ------------------------------------------------------------
# PESTAÑAS
# ------------------------------------------------------------
tab_labels = ["Buscar", "Administrar", "Listado", "Editar"]
tabs = st.tabs(["🔍 Buscar", "⚙️ Administrar", "📦 Listado", "🛠️ Editar"])
tab_dict = dict(zip(tab_labels, tabs))

# ============================================================
# TAB 1: BUSCAR
# ============================================================
with tab_dict["Buscar"]:
    st.session_state["active_tab"] = "Buscar"
    pregunta = st.text_input("Pregunta", placeholder="Ejemplo: ¿Qué sets de Star Wars tengo?")
    if st.button("Buscar", use_container_width=True):
        if not pregunta.strip():
            st.warning("Escribe una pregunta.")
        else:
            with st.spinner("Buscando..."):
                try:
                    resp = requests.post(LAMBDA_SEARCH, json={"pregunta": pregunta}, timeout=40)
                    if resp.status_code == 200:
                        data = resp.json()
                        body = data.get("body")
                        if isinstance(body, str):
                            data = json.loads(body)
                        respuesta = re.sub(r"!\[.*?\]\(\s*\)", "", data.get("respuesta", ""))
                        st.markdown(f"#### 💬 {respuesta}")
                        resultados = data.get("resultados", [])
                        if resultados:
                            df = pd.DataFrame(resultados)
                            mostrar_sets(df, "busqueda")
                        else:
                            st.info("No se encontraron resultados.")
                    else:
                        st.error(f"Error {resp.status_code}: {resp.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# ============================================================
# TAB 2: ADMINISTRAR (Alta y Baja)
# ============================================================
with tab_dict["Administrar"]:
    st.session_state["active_tab"] = "Administrar"
    accion = st.radio("Acción", ["Alta", "Baja"], horizontal=True)
    st.divider()
    set_number = st.text_input("Número de set")
    name = st.text_input("Nombre")
    theme = st.selectbox("Tema", ["Star Wars", "Technic", "Ideas", "F1"])
    year = st.number_input("Año", min_value=1970, max_value=2030, step=1)
    pieces = st.number_input("Piezas", min_value=0, step=10)
    storage = st.selectbox("Ubicación", ["Cobalto", "San Geronimo"])
    storage_box = st.number_input("Caja", min_value=0, step=1)
    condition = st.selectbox("Condición", ["In Lego Box", "Open"])
    imagen_archivo = None
    if accion == "Alta":
        imagen_archivo = st.file_uploader("📸 Imagen del set", type=["jpg", "jpeg", "webp"])
    lego_web_url = st.text_input("URL página LEGO (opcional)")
    manuals = st.text_area("Manuales (uno por línea)")
    minifigs = st.text_area("Minifigs (número: nombre por línea)")
    tags = st.text_area("Tags (separados por comas)", placeholder="nave, star wars, exclusivo")

    if st.button("Enviar", use_container_width=True):
        try:
            set_number_int = int(set_number)
            manual_list = [m.strip() for m in manuals.splitlines() if m.strip()]
            minifigs_names, minifigs_numbers = [], []
            for line in minifigs.splitlines():
                p = [x.strip() for x in line.split(":")]
                if len(p) == 2:
                    minifigs_numbers.append(p[0])
                    minifigs_names.append(p[1])
            tags_list = [t.strip() for t in tags.split(",") if t.strip()]
            payload = {"accion": accion.lower()}
            if accion == "Alta":
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
                    "manuals": manual_list,
                    "minifigs_names": minifigs_names,
                    "minifigs_numbers": minifigs_numbers,
                    "tags": tags_list,
                    "created_at": datetime.utcnow().isoformat(),
                }
                if imagen_archivo:
                    lego["imagen_base64"] = convertir_a_base64(imagen_archivo)
                payload["lego"] = lego
            else:
                payload["set_number"] = set_number_int

            with st.spinner("Ejecutando operación..."):
                r = requests.post(LAMBDA_ADMIN, json=payload, timeout=40)
                if r.status_code == 200:
                    st.success(r.json().get("mensaje", "Operación completada."))
                else:
                    st.error(f"Error {r.status_code}: {r.text}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# ============================================================
# TAB 3: LISTADO
# ============================================================
with tab_dict["Listado"]:
    st.session_state["active_tab"] = "Listado"
    tema = st.selectbox("Selecciona el tema:", ["Star Wars", "Technic", "Ideas", "F1"])
    if st.button("Mostrar sets", use_container_width=True):
        with st.spinner("Cargando..."):
            r = requests.post(LAMBDA_SEARCH_FILTER, json={"tema": tema}, timeout=40)
            if r.status_code == 200:
                data = r.json()
                body = data.get("body")
                if isinstance(body, str):
                    data = json.loads(body)
                resultados = data.get("resultados", [])
                if resultados:
                    df = pd.DataFrame(resultados)
                    mostrar_sets(df, "listado")
                else:
                    st.info("No hay sets registrados en este tema.")
            else:
                st.error(f"Error {r.status_code}: {r.text}")

# ============================================================
# TAB 4: EDITAR
# ============================================================
with tab_dict["Editar"]:
    if st.session_state["editar_set"] is None:
        st.info("Selecciona un set desde la búsqueda o el listado para editarlo.")
    else:
        set_num = st.session_state["editar_set"]
        st.subheader(f"🛠️ Editar set {set_num}")
        lego_data = cargar_set_desde_lambda(set_num)
        if lego_data:
            with st.form("form_editar"):
                name = st.text_input("Nombre", lego_data.get("name",""))
                theme = st.text_input("Tema", lego_data.get("theme",""))
                year = st.number_input("Año", value=int(lego_data.get("year",2020)))
                pieces = st.number_input("Piezas", value=int(lego_data.get("pieces",0)))
                storage = st.text_input("Ubicación", lego_data.get("storage",""))
                storage_box = st.number_input("Caja", value=int(lego_data.get("storage_box",0)))
                condition = st.text_input("Condición", lego_data.get("condition",""))
                lego_web_url = st.text_input("URL LEGO", lego_data.get("lego_web_url",""))
                manuals = st.text_area("Manuales", "\n".join(lego_data.get("manuals",[])))
                minifigs = st.text_area(
                    "Minifigs (número: nombre)",
                    "\n".join([f"{n}:{m}" for n,m in zip(
                        lego_data.get("minifigs_numbers",[]),
                        lego_data.get("minifigs_names",[])
                    )])
                )
                tags = st.text_input("Tags (coma)", ", ".join(lego_data.get("tags",[])))
                imagen_archivo = st.file_uploader("📸 Nueva imagen (opcional)", type=["jpg","jpeg","webp"])
                enviar = st.form_submit_button("💾 Guardar cambios")
                if enviar:
                    payload = {
                        "accion": "actualizacion",
                        "set_number": int(set_num),
                        "campos": {
                            "name": name,
                            "theme": theme,
                            "year": year,
                            "pieces": pieces,
                            "storage": storage,
                            "storage_box": storage_box,
                            "condition": condition,
                            "lego_web_url": lego_web_url,
                            "manuals": [m.strip() for m in manuals.splitlines() if m.strip()],
                            "tags": [t.strip() for t in tags.split(",") if t.strip()],
                            "modified_at": datetime.utcnow().isoformat(),
                        }
                    }
                    if minifigs:
                        nums, names = [], []
                        for line in minifigs.splitlines():
                            p = [x.strip() for x in line.split(":")]
                            if len(p)==2:
                                nums.append(p[0]); names.append(p[1])
                        payload["campos"]["minifigs_numbers"]=nums
                        payload["campos"]["minifigs_names"]=names
                    if imagen_archivo:
                        payload["campos"]["imagen_base64"] = convertir_a_base64(imagen_archivo)
                    with st.spinner("Actualizando..."):
                        r = requests.post(LAMBDA_ADMIN, json=payload, timeout=40)
                        if r.status_code==200:
                            st.success("✅ Cambios guardados correctamente.")
                            st.session_state["editar_set"]=None
                            st.session_state["active_tab"]="Listado"
                            st.experimental_rerun()
                        else:
                            st.error(f"Error {r.status_code}: {r.text}")

# ------------------------------------------------------------
# PIE
# ------------------------------------------------------------
st.markdown("<hr style='margin-top:25px;'>", unsafe_allow_html=True)
st.caption("Minimal LEGO IA · Desarrollado por Mike Nava")

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
if "listado_resultados" not in st.session_state:
    st.session_state["listado_resultados"] = []
if "listado_tema" not in st.session_state:
    st.session_state["listado_tema"] = None

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

def render_listado_html(df, origen):
    """Renderiza resultados con botón Editar que activa edición."""
    html = f"""
    <html><head><style>
      body {{ font-family:'Inter',Roboto,sans-serif;color:#333;margin:0;padding:0;background:#fff;}}
      .set-card{{display:flex;align-items:center;gap:16px;padding:10px 14px;border-radius:10px;border:1px solid #eee;margin-bottom:10px;background:#fafafa;opacity:0;transition:opacity .3s ease;}}
      .set-card.visible{{opacity:1;}}
      .set-img{{width:100px;height:auto;border-radius:6px;object-fit:contain;background:#fff;border:1px solid #ddd;}}
      .set-title{{font-weight:600;font-size:15px;color:#222;margin-bottom:3px;}}
      .set-sub{{color:#777;font-size:13px;margin-bottom:4px;}}
      .set-detail{{font-size:12.5px;color:#555;}}
      .edit-link{{font-size:12px;color:#007bff;text-decoration:none;margin-top:3px;display:inline-block;}}
    </style></head><body>
    """
    for _, row in df.iterrows():
        thumb = row.get("thumb", "")
        full = row.get("image_full", "")
        image_html = (
            f'<a href="{full}" target="_blank"><img src="{thumb}" class="set-img"></a>'
            if thumb or full else
            '<div style="width:100px;height:70px;background:#ddd;border-radius:6px;text-align:center;line-height:70px;">—</div>'
        )
        minifigs_total = row.get("minifigs_total", 0)
        minifigs_text = f" · 🧍‍♂️ {int(minifigs_total)} minifigs" if int(minifigs_total) > 0 else ""
        set_num = row.get("set_number","")

        html += f"""
        <div class="set-card">
            {image_html}
            <div class="set-info">
                <div class="set-title">{set_num} · {row.get("name","")}</div>
                <div class="set-sub">{row.get("year","")} · 🧩 {row.get("pieces","")} piezas{minifigs_text}</div>
                <div class="set-detail">🎁 {row.get("condition","")} · 🏠 {row.get("storage","")} · 📦 Caja {row.get("storage_box","")}</div>
                <a class="edit-link" href="#" onclick="window.parent.postMessage({{type:'editarSet', origen:'{origen}', setNumber:'{set_num}'}}, '*');return false;">✏️ Editar</a>
            </div>
        </div>"""
    html += """
    <script>
      window.addEventListener("load",()=>{
        document.querySelectorAll('.set-card').forEach((c,i)=>setTimeout(()=>c.classList.add('visible'),i*60));
      });
    </script></body></html>
    """
    components.html(html, height=1000, scrolling=False)

def cargar_set_desde_lambda(set_number):
    """Consulta datos reales del set desde Lambda."""
    try:
        resp = requests.post(LAMBDA_ADMIN, json={"accion": "consulta", "set_number": int(set_number)}, timeout=40)
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

# ------------------------------------------------------------
# ESCUCHAR EVENTOS DE EDICIÓN DESDE HTML (NUEVA API)
# ------------------------------------------------------------
components.html("""
<script>
window.addEventListener("message", (event)=>{
  if(event.data && event.data.type==="editarSet"){
    const params = new URLSearchParams(window.location.search);
    params.set("editar", event.data.setNumber);
    window.parent.location.search = params.toString();
  }
});
</script>
""", height=0, scrolling=False)

query_params = st.query_params  # ✅ Nueva API sin advertencias
if "editar" in query_params:
    st.session_state["editar_set"] = query_params["editar"][0]

# ------------------------------------------------------------
# PESTAÑAS
# ------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Buscar", "⚙️ Administrar", "📦 Listado", "🛠️ Editar"])

# ============================================================
# TAB 1: BUSCAR
# ============================================================
with tab1:
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
                            df["thumb"] = df.get("thumb_url", df.get("image_url", ""))
                            df["image_full"] = df.get("image_url", "")
                            df["minifigs_total"] = df.get("minifigs_names", []).apply(lambda x: len(x) if isinstance(x, list) else 0)
                            render_listado_html(df, "busqueda")
                        else:
                            st.info("No se encontraron resultados.")
                    else:
                        st.error(f"Error {resp.status_code}: {resp.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# ============================================================
# TAB 2: ADMINISTRAR (Solo Alta y Baja)
# ============================================================
with tab2:
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
                    "set_number": set_number_int, "name": name, "theme": theme,
                    "year": year, "pieces": pieces, "storage": storage,
                    "storage_box": storage_box, "condition": condition,
                    "lego_web_url": lego_web_url, "manuals": manual_list,
                    "minifigs_names": minifigs_names, "minifigs_numbers": minifigs_numbers,
                    "tags": tags_list, "created_at": datetime.utcnow().isoformat(),
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
with tab3:
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
                    df["thumb"] = df.get("thumb_url", df.get("image_url", ""))
                    df["image_full"] = df.get("image_url", "")
                    df["minifigs_total"] = df.get("minifigs_names", []).apply(lambda x: len(x) if isinstance(x, list) else 0)
                    render_listado_html(df, "listado")
                else:
                    st.info("No hay sets registrados en este tema.")
            else:
                st.error(f"Error {r.status_code}: {r.text}")

# ============================================================
# TAB 4: EDITAR
# ============================================================
with tab4:
    if not st.session_state["editar_set"]:
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
                manuals = st.text_area("Manuales (uno por línea)", "\n".join(lego_data.get("manuals",[])))
                minifigs = st.text_area("Minifigs (número: nombre)", "\n".join([f"{n}:{m}" for n,m in zip(lego_data.get("minifigs_numbers",[]), lego_data.get("minifigs_names",[]))]))
                tags = st.text_input("Tags (coma)", ", ".join(lego_data.get("tags",[])))
                imagen_archivo = st.file_uploader("📸 Nueva imagen (opcional)", type=["jpg","jpeg","webp"])
                enviar = st.form_submit_button("💾 Guardar cambios")
                if enviar:
                    try:
                        payload = {
                            "accion": "actualizacion",
                            "set_number": int(set_num),
                            "campos": {
                                "name": name, "theme": theme, "year": year, "pieces": pieces,
                                "storage": storage, "storage_box": storage_box,
                                "condition": condition, "lego_web_url": lego_web_url,
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
                            else:
                                st.error(f"Error {r.status_code}: {r.text}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

# ------------------------------------------------------------
# PIE
# ------------------------------------------------------------
st.markdown("<hr style='margin-top:25px;'>", unsafe_allow_html=True)
st.caption("Minimal LEGO IA · Desarrollado por Mike Nava")

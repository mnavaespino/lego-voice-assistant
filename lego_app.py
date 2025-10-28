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
    pregunta = st.text_input("Pregunta", placeholder="Ejemplo: ¿Qué sets de Star Wars tengo?")
    if st.button("Buscar", use_container_width=True):
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
                        st.markdown(f"#### 💬 {respuesta}")
                        resultados = data.get("resultados", [])

                        if not resultados:
                            st.info("No se encontraron resultados.")
                        else:
                            df = pd.DataFrame(resultados)
                            df["thumb"] = df.get("thumb_url", df.get("image_url", ""))
                            df["image_full"] = df.get("image_url", "")

                            html = """
                            <html><head><style>
                                body { font-family:'Inter', Roboto, sans-serif; color:#333; background:#fff; margin:0; padding:0; }
                                .set-card { display:flex; align-items:center; gap:16px;
                                    padding:10px 14px; border-radius:10px; border:1px solid #eee;
                                    margin-bottom:10px; background:#fafafa;
                                    transition:transform .15s ease, opacity .3s ease; opacity:0; }
                                .set-card.visible { opacity:1; transform:translateY(0); }
                                .set-img { width:100px; height:auto; border-radius:6px;
                                    object-fit:contain; border:1px solid #ddd; background:#fff; }
                                .set-info { flex-grow:1; }
                                .set-title { font-weight:600; font-size:15px; color:#222; margin-bottom:3px; }
                                .set-sub { color:#777; font-size:13px; margin-bottom:4px; }
                                .set-detail { font-size:12.5px; color:#555; }
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

                                minifigs = row.get("minifigs_names", [])
                                total_minifigs = len(minifigs) if isinstance(minifigs, list) else 0
                                minifigs_text = f" · 🧍‍♂️ {total_minifigs} minifigs" if total_minifigs > 0 else ""

                                html += f"""
                                <div class="set-card">
                                    {image_html}
                                    <div class="set-info">
                                        <div class="set-title">{row.get("set_number","")} · {row.get("name","")}</div>
                                        <div class="set-sub">{row.get("theme","")} · {row.get("year","")} · 🧩 {row.get("pieces","")} piezas{minifigs_text}</div>
                                        <div class="set-detail">🎁 {row.get("condition","")} · 🏠 {row.get("storage","")} · 📦 Caja {row.get("storage_box","")}</div>
                                    </div>
                                </div>"""
                            html += """
                            <script>
                              let h=0;
                              function resize(extra=120){
                                const n=Math.max(document.body.scrollHeight,document.documentElement.scrollHeight);
                                if(Math.abs(n-h)>10){window.parent.postMessage({streamlitResize:n+extra},"*");h=n;}
                              }
                              new ResizeObserver(()=>resize()).observe(document.body);
                              window.addEventListener("load",()=>{setTimeout(()=>resize(150),300);
                                document.querySelectorAll('.set-card').forEach((c,i)=>setTimeout(()=>c.classList.add('visible'),i*60));
                              });
                            </script></body></html>
                            """
                            components.html(html, height=1000, scrolling=False)
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# ============================================================
# TAB 2: ADMINISTRAR
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

    imagen_archivo = None
    if accion in ["Alta", "Actualizacion"]:
        imagen_archivo = st.file_uploader("📸 Imagen del set", type=["jpg", "jpeg", "webp"])

    lego_web_url = st.text_input("URL página LEGO (opcional)", placeholder="https://www.lego.com/...")
    manuals = st.text_area("Manuales (uno por línea)")
    minifigs = st.text_area("Minifigs (número: nombre por línea)")
    tags = st.text_area("Tags (separados por comas)", placeholder="nave, star wars, exclusivo")

    if st.button("Enviar", use_container_width=True):
        try:
            set_number_int = int(set_number)
            manual_list = [m.strip() for m in manuals.splitlines() if m.strip()]
            minifigs_names, minifigs_numbers = [], []
            minifigsTotal = 0
            for line in minifigs.splitlines():
                p = [x.strip() for x in line.split(":")]
                if len(p) == 2:
                    minifigs_numbers.append(p[0])
                    minifigs_names.append(p[1])
                minifigsTotal += 1
            tags_list = [t.strip() for t in tags.split(",") if t.strip()]
            payload = {"accion": accion.lower()}
            imagen_base64 = convertir_a_base64(imagen_archivo) if imagen_archivo else None

            if accion == "Alta":
                payload["lego"] = {
                    "set_number": set_number_int, "name": name, "theme": theme,
                    "year": year, "pieces": pieces, "storage": storage,
                    "storage_box": storage_box, "condition": condition,
                    "lego_web_url": lego_web_url, "manuals": manual_list,
                    "minifigs_names": minifigs_names, "minifigs_numbers": minifigs_numbers, "minifigs_total": minifigsTotal,
                    "tags": tags_list, "created_at": datetime.utcnow().isoformat(),
                }
                if imagen_base64: payload["lego"]["imagen_base64"] = imagen_base64
            elif accion == "Baja":
                payload["set_number"] = set_number_int
            else:
                campos = {
                    "name": name, "theme": theme, "year": year, "pieces": pieces,
                    "storage": storage, "storage_box": storage_box,
                    "condition": condition, "lego_web_url": lego_web_url,
                    "manuals": manual_list, "minifigs_names": minifigs_names,
                    "minifigs_numbers": minifigs_numbers, "tags": tags_list,
                    "modified_at": datetime.utcnow().isoformat(),
                }
                if imagen_base64: campos["imagen_base64"] = imagen_base64
                campos_filtrados = {k: v for k, v in campos.items() if v not in ["", None, [], 0]}
                payload["set_number"], payload["campos"] = set_number_int, campos_filtrados

            with st.spinner("Guardando cambios..."):
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
# TAB 3: LISTADO POR TEMA (con ordenamiento)
# ============================================================
with tab3:
    tema = st.selectbox("Selecciona el tema a mostrar:", ["Star Wars", "Technic", "Ideas", "F1"])
    if st.button("Mostrar sets", use_container_width=True):
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
                        df = pd.DataFrame(resultados)
                        df["thumb"] = df.get("thumb_url", df.get("image_url", ""))
                        df["image_full"] = df.get("image_url", "")
                        df["minifigs_total"] = df["minifigs_names"].apply(
                            lambda x: len(x) if isinstance(x, list) else 0
                        )

                        # 🔽 Selector de ordenamiento
                        columnas_orden = {
                            "Número de set": "set_number",
                            "Nombre": "name",
                            "Año": "year",
                            "Piezas": "pieces",
                            "Minifigs": "minifigs_total",
                            "Caja": "storage_box"
                        }
                        orden_seleccion = st.selectbox(
                            "Ordenar por:",
                            list(columnas_orden.keys()),
                            index=0
                        )
                        ascendente = st.toggle("Orden ascendente", value=True)

                        columna_orden = columnas_orden[orden_seleccion]
                        df = df.sort_values(by=columna_orden, ascending=ascendente, na_position="last")

                        st.markdown(f"**{len(df)} sets encontrados en {tema}**")

                        html = """
                        <html><head><style>
                            body { font-family:'Inter',Roboto,sans-serif;color:#333;margin:0;padding:0;background:#fff;}
                            .set-card{display:flex;align-items:center;gap:16px;padding:10px 14px;border-radius:10px;border:1px solid #eee;margin-bottom:10px;background:#fafafa;opacity:0;transition:opacity .3s ease;}
                            .set-card.visible{opacity:1;}
                            .set-img{width:100px;height:auto;border-radius:6px;object-fit:contain;background:#fff;border:1px solid #ddd;}
                            .set-title{font-weight:600;font-size:15px;color:#222;margin-bottom:3px;}
                            .set-sub{color:#777;font-size:13px;margin-bottom:4px;}
                            .set-detail{font-size:12.5px;color:#555;}
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

                            minifigs_text = (
                                f" · 🧍‍♂️ {row['minifigs_total']} minifigs"
                                if row["minifigs_total"] > 0 else ""
                            )

                            html += f"""
                            <div class="set-card">
                                {image_html}
                                <div class="set-info">
                                    <div class="set-title">{row.get("set_number","")} · {row.get("name","")}</div>
                                    <div class="set-sub">{row.get("year","")} · 🧩 {row.get("pieces","")} piezas{minifigs_text}</div>
                                    <div class="set-detail">🎁 {row.get("condition","")} · 🏠 {row.get("storage","")} · 📦 Caja {row.get("storage_box","")}</div>
                                </div>
                            </div>"""

                        html += """
                        <script>
                          let h=0;
                          function resize(extra=100){
                            const n=Math.max(document.body.scrollHeight,document.documentElement.scrollHeight);
                            if(Math.abs(n-h)>10){window.parent.postMessage({streamlitResize:n+extra},"*");h=n;}
                          }
                          new ResizeObserver(()=>resize()).observe(document.body);
                          window.addEventListener("load",()=>{setTimeout(()=>resize(150),300);
                            document.querySelectorAll('.set-card').forEach((c,i)=>setTimeout(()=>c.classList.add('visible'),i*60));
                          });
                        </script></body></html>
                        """
                        components.html(html, height=1000, scrolling=False)
                else:
                    st.error(f"Error {r.status_code}: {r.text}")
        except Exception as e:
            st.error(f"Ocurrió un error: {str(e)}")

# ------------------------------------------------------------
# PIE
# ------------------------------------------------------------
st.markdown("<hr style='margin-top:25px;'>", unsafe_allow_html=True)
st.caption("Minimal LEGO IA · Desarrollado por Mike Nava")

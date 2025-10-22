import streamlit as st
import requests
import re
import json
import base64
from datetime import datetime
import pandas as pd
import streamlit.components.v1 as components  # 👈 para renderizar HTML moderno

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
# FUNCIÓN AUXILIAR PARA RENDERIZAR DETALLES COMPLETOS
# ============================================================
def render_detalle(row):
    manuals = row.get("manuals", [])
    minifigs = row.get("minifigs_names", [])
    numbers = row.get("minifigs_numbers", [])
    tags = row.get("tags", [])
    lego_url = row.get("lego_web_url", "")

    manual_links = ""
    if manuals:
        manual_links = " · ".join([f'<a href="{m}" target="_blank">Manual {i+1}</a>' for i, m in enumerate(manuals)])

    minifigs_text = ""
    if minifigs:
        lista = [f"{name} ({num})" for name, num in zip(minifigs, numbers)]
        minifigs_text = ", ".join(lista)

    tags_text = ", ".join(tags) if tags else ""

    detalle_html = "<div class='extra'>"
    if manual_links:
        detalle_html += f"<div>📘 <b>Manuales:</b> {manual_links}</div>"
    if minifigs_text:
        detalle_html += f"<div>🧍 <b>Minifigs:</b> {minifigs_text}</div>"
    if tags_text:
        detalle_html += f"<div>🏷️ <b>Tags:</b> {tags_text}</div>"
    if lego_url:
        detalle_html += f"<div>🌐 <a href='{lego_url}' target='_blank'>Página oficial LEGO</a></div>"
    detalle_html += "</div>"
    return detalle_html

# ============================================================
# TAB 1: BUSCAR EN CATÁLOGO (Diseño moderno tipo galería)
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
                        st.markdown(f"### 💬 {respuesta}")

                        resultados = data.get("resultados", [])
                        if not resultados:
                            st.info("No se encontraron resultados.")
                        else:
                            df = pd.DataFrame(resultados)
                            df["thumb"] = df.get("thumb_url", df.get("image_url", ""))
                            df["image_full"] = df.get("image_url", "")

                            html = """
                            <html><head>
                            <style>
                                body { font-family: 'Segoe UI', Roboto, sans-serif; color: #333; }
                                .set-card {
                                    display: flex;
                                    align-items: flex-start;
                                    gap: 16px;
                                    padding: 12px 16px;
                                    border-radius: 12px;
                                    border: 1px solid #e0e0e0;
                                    margin-bottom: 14px;
                                    background-color: #fafafa;
                                    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
                                    transition: transform 0.1s ease-in-out;
                                }
                                .set-card:hover { transform: scale(1.01); background-color: #fff; }
                                .set-img {
                                    width: 120px;
                                    border-radius: 8px;
                                    object-fit: contain;
                                    background-color: #fff;
                                    border: 1px solid #ddd;
                                }
                                .set-info { flex-grow: 1; font-size: 13px; }
                                .set-title { font-weight: 600; font-size: 16px; margin-bottom: 6px; color: #222; }
                                .set-sub { color: #666; margin-bottom: 4px; }
                                .set-detail { color: #444; margin-bottom: 6px; }
                                .extra { margin-top: 6px; font-size: 13px; }
                                a { color: #0a66c2; text-decoration: none; }
                                a:hover { text-decoration: underline; }
                            </style></head><body>
                            """

                            for _, row in df.iterrows():
                                thumb = row.get("thumb", "")
                                full = row.get("image_full", "")
                                image_html = (
                                    f'<a href="{full}" target="_blank"><img src="{thumb}" class="set-img"></a>'
                                    if thumb or full
                                    else '<div style="width:120px;height:80px;background:#ddd;border-radius:6px;line-height:80px;text-align:center;">—</div>'
                                )

                                detalle_html = render_detalle(row)
                                html += f"""
                                <div class="set-card">
                                    {image_html}
                                    <div class="set-info">
                                        <div class="set-title">{row.get("set_number", "")} · {row.get("name", "")}</div>
                                        <div class="set-sub">{row.get("theme", "")} · {row.get("year", "")} · 🧩 {row.get("pieces", "")} piezas</div>
                                        <div class="set-detail">🎁 {row.get("condition", "")} · 🏠 {row.get("storage", "")} · 📦 Caja {row.get("storage_box", "")}</div>
                                        {detalle_html}
                                    </div>
                                </div>
                                """

                            html += "</body></html>"
                            components.html(html, height=800, scrolling=True)

                except Exception as e:
                    st.error(f"Error: {str(e)}")

# ============================================================
# TAB 2: ADMINISTRAR CATÁLOGO (igual)
# ============================================================
# (Sin cambios, se mantiene tu versión original completa)

# ============================================================
# TAB 3: LISTADO POR TEMA (con todos los campos)
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
                        df["thumb"] = df.get("thumb_url", df.get("image_url", ""))
                        df["image_full"] = df.get("image_url", "")

                        html = """
                        <html><head>
                        <style>
                            body { font-family: 'Segoe UI', Roboto, sans-serif; color: #333; }
                            .set-card {
                                display: flex;
                                align-items: flex-start;
                                gap: 16px;
                                padding: 12px 16px;
                                border-radius: 12px;
                                border: 1px solid #e0e0e0;
                                margin-bottom: 14px;
                                background-color: #fafafa;
                                box-shadow: 0 1px 4px rgba(0,0,0,0.05);
                                transition: transform 0.1s ease-in-out;
                            }
                            .set-card:hover { transform: scale(1.01); background-color: #fff; }
                            .set-img {
                                width: 120px;
                                border-radius: 8px;
                                object-fit: contain;
                                background-color: #fff;
                                border: 1px solid #ddd;
                            }
                            .set-info { flex-grow: 1; font-size: 13px; }
                            .set-title { font-weight: 600; font-size: 16px; margin-bottom: 6px; color: #222; }
                            .set-sub { color: #666; margin-bottom: 4px; }
                            .set-detail { color: #444; margin-bottom: 6px; }
                            .extra { margin-top: 6px; font-size: 13px; }
                            a { color: #0a66c2; text-decoration: none; }
                            a:hover { text-decoration: underline; }
                        </style></head><body>
                        """

                        for _, row in df.iterrows():
                            thumb = row.get("thumb", "")
                            full = row.get("image_full", "")
                            image_html = (
                                f'<a href="{full}" target="_blank"><img src="{thumb}" class="set-img"></a>'
                                if thumb or full
                                else '<div style="width:120px;height:80px;background:#ddd;border-radius:6px;line-height:80px;text-align:center;">—</div>'
                            )
                            detalle_html = render_detalle(row)

                            html += f"""
                            <div class="set-card">
                                {image_html}
                                <div class="set-info">
                                    <div class="set-title">{row.get("set_number", "")} · {row.get("name", "")}</div>
                                    <div class="set-sub">{row.get("year", "")} · 🧩 {row.get("pieces", "")} piezas</div>
                                    <div class="set-detail">🎁 {row.get("condition", "")} · 🏠 {row.get("storage", "")} · 📦 Caja {row.get("storage_box", "")}</div>
                                    {detalle_html}
                                </div>
                            </div>
                            """

                        html += "</body></html>"
                        components.html(html, height=750, scrolling=True)

                else:
                    st.error(f"Error {r.status_code}: {r.text}")
        except Exception as e:
            st.error(f"Ocurrió un error: {str(e)}")

# ------------------------------------------------------------
# PIE
# ------------------------------------------------------------
st.markdown("---")
st.caption("Desarrollado por Mike Nava · Firestore + OpenAI + AWS Lambda + Streamlit")

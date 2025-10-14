import streamlit as st
import requests
import re
import json

# ------------------------------------------------------------
# FUNCIÓN: convertir automáticamente enlaces de Google Drive
# ------------------------------------------------------------
def convertir_enlace_drive(url):
    """
    Si la URL proviene de Google Drive, convierte cualquier formato
    (view, open, file/d/...) en el formato directo que Streamlit puede mostrar.
    """
    if not url or "drive.google.com" not in url:
        return url

    # Detectar formato "/d/ID"
    patron = r"/d/([a-zA-Z0-9_-]+)"
    coincidencia = re.search(patron, url)
    if coincidencia:
        file_id = coincidencia.group(1)
        return f"https://drive.google.com/uc?export=view&id={file_id}"

    # Detectar formato con id=ID
    patron_id = r"id=([a-zA-Z0-9_-]+)"
    coincidencia_id = re.search(patron_id, url)
    if coincidencia_id:
        file_id = coincidencia_id.group(1)
        return f"https://drive.google.com/uc?export=view&id={file_id}"

    return url


# ------------------------------------------------------------
# CONFIGURACIÓN GENERAL
# ------------------------------------------------------------
st.set_page_config(page_title="Asistente LEGO IA", page_icon="🧱", layout="centered")

st.title("🧱 Administrador y Buscador LEGO IA")
st.caption("Consulta o administra tu colección LEGO (con dictado nativo en iPhone 🗣️)")

# URLs de tus funciones Lambda
LAMBDA_SEARCH = "https://ztpcx6dks9.execute-api.us-east-1.amazonaws.com/default/legoSearch"
LAMBDA_ADMIN = "https://nn41og73w2.execute-api.us-east-1.amazonaws.com/default/legoAdmin"

# ------------------------------------------------------------
# PESTAÑAS
# ------------------------------------------------------------
tab1, tab2 = st.tabs(["🔍 Buscar en catálogo", "⚙️ Altas, Bajas y Cambios"])

# ============================================================
# TAB 1: BUSCAR EN CATÁLOGO
# ============================================================
with tab1:
    st.markdown("""
    ### Ejemplos de preguntas
    - ¿Tengo el set Justifier?
    - ¿Qué sets de LEGO son entre el año 2020 y 2021?
    - ¿Cuántos sets de Star Wars tengo?
    - ¿Qué sets tengo guardados en la caja 12?
    """)

    pregunta = st.text_input(
        "🗣️ Escribe o dicta tu pregunta:",
        placeholder="Ejemplo: ¿Qué sets de LEGO tengo en la caja 12?"
    )

    if st.button("Preguntar 🧱"):
        if not pregunta.strip():
            st.warning("Por favor, escribe una pregunta.")
        else:
            with st.spinner("Consultando tu colección LEGO... 🧱"):
                try:
                    payload = {"pregunta": pregunta}
                    response = requests.post(LAMBDA_SEARCH, json=payload, timeout=40)

                    if response.status_code == 200:
                        data = response.json()
                        body = data.get("body")

                        # 🔹 Algunos endpoints regresan doble JSON (string dentro de "body")
                        if isinstance(body, str):
                            try:
                                data = json.loads(body)
                            except Exception:
                                pass

                        # Texto de respuesta principal
                        respuesta = data.get("respuesta", "Sin respuesta.")
                        respuesta = re.sub(r"!\[.*?\]\(\s*\)", "", respuesta)  # Limpieza Markdown roto

                        st.success("Respuesta:")
                        st.markdown(respuesta)

                        # --------------------------------------------------------
                        # Mostrar resultados como tarjetas visuales
                        # --------------------------------------------------------
                        resultados = data.get("resultados", [])

                        if resultados and isinstance(resultados, list):
                            st.markdown("### 🧱 Resultados encontrados:")

                            for item in resultados:
                                nombre = item.get("name", "Sin nombre")
                                set_number = item.get("set_number", "")
                                year = item.get("year", "")
                                theme = item.get("theme", "")
                                pieces = item.get("pieces", "")
                                storage_box = item.get("storage_box", "")
                                condition = item.get("condition", "")
                                image_url = convertir_enlace_drive(item.get("image_url", ""))

                                # Crear diseño de tarjeta con dos columnas
                                cols = st.columns([1, 2])
                                with cols[0]:
                                    if image_url:
                                        st.image(image_url, width=130)
                                    else:
                                        st.text("🖼️ Sin imagen")

                                with cols[1]:
                                    st.markdown(f"**{nombre}** ({set_number})")
                                    st.caption(f"📅 {year} | 🏷️ {theme} | 🧩 {pieces} piezas")
                                    st.caption(f"📦 Caja {storage_box} | 🎁 {condition}")

                                st.divider()

                        else:
                            st.info("No se encontraron sets que coincidan con tu búsqueda.")

                    else:
                        st.error(f"Error {response.status_code}: {response.text}")

                except requests.exceptions.RequestException as e:
                    st.error(f"Error de conexión: {str(e)}")
                except Exception as e:
                    st.error(f"Ocurrió un error inesperado: {str(e)}")


# ============================================================
# TAB 2: ALTAS, BAJAS Y CAMBIOS
# ============================================================
with tab2:
    st.subheader("⚙️ Gestión del catálogo LEGO")

    st.markdown("### 🔧 Tipo de operación")
    operacion = st.selectbox(
        "Selecciona una operación:",
        ["Alta de nuevo set", "Baja de set existente", "Cambio / Edición de set"]
    )

    mapa_acciones = {
        "Alta de nuevo set": "alta",
        "Baja de set existente": "baja",
        "Cambio / Edición de set": "actualizacion"
    }
    accion = mapa_acciones[operacion]

    st.divider()
    st.markdown("### 📋 Datos del set")

    # Campos básicos
    set_number = st.text_input("🔢 Número de set (ej. 75301)")
    name = st.text_input("📦 Nombre del set (ej. The Justifier)")
    theme = st.selectbox("🏷️ Tema o serie", ["Star Wars", "Technic", "Ideas", "F1"])
    year = st.number_input("📅 Año de lanzamiento", min_value=1970, max_value=2030, step=1)
    pieces = st.number_input("🧩 Número de piezas", min_value=0, step=10)
    storage = st.selectbox("📦 Ubicación (storage)", ["Cobalto", "San Geronimo"])
    storage_box = st.number_input("📦 Número de caja", min_value=0, step=1)
    condition = st.selectbox("🎁 Condición del set", ["In Lego Box", "Open"])

    # --------------------------------------------------------
    # Imagen y campos adicionales
    # --------------------------------------------------------
    st.divider()
    st.markdown("### 🧱 Información adicional (opcional)")
    image_url = st.text_input("🖼️ URL de imagen")
    image_url = convertir_enlace_drive(image_url)

    manuals = st.text_area("📘 URLs de manuales (una por línea)", placeholder="https://...")
    minifigs = st.text_area("🧍 Minifigs (formato: nombre|número por línea)", placeholder="Luke Skywalker|SW0123")

    st.divider()

    if st.button("Enviar operación ⚙️"):
        if not set_number.strip():
            st.warning("Debes especificar al menos el número de set.")
        else:
            with st.spinner("Procesando operación..."):
                try:
                    # Validar que el número de set sea entero
                    try:
                        set_number_int = int(set_number)
                    except ValueError:
                        st.error("El número de set debe ser un número entero.")
                        st.stop()

                    manual_list = [m.strip() for m in manuals.splitlines() if m.strip()]
                    minifig_list = []
                    for line in minifigs.splitlines():
                        parts = [p.strip() for p in line.split("|")]
                        if len(parts) == 2:
                            minifig_list.append({
                                "minifig_name": parts[0],
                                "minifig_number": parts[1]
                            })

                    # Armar payload según acción
                    if accion == "alta":
                        payload = {
                            "accion": "alta",
                            "lego": {
                                "set_number": set_number_int,
                                "name": name,
                                "theme": theme,
                                "year": year,
                                "pieces": pieces,
                                "storage": storage,
                                "storage_box": storage_box,
                                "condition": condition,
                                "image_url": image_url,
                                "manuals": manual_list,
                                "minifigs": minifig_list
                            }
                        }

                    elif accion == "baja":
                        payload = {"accion": "baja", "set_number": set_number_int}

                    elif accion == "actualizacion":
                        campos = {
                            "name": name,
                            "theme": theme,
                            "year": year,
                            "pieces": pieces,
                            "storage": storage,
                            "storage_box": storage_box,
                            "condition": condition,
                            "image_url": image_url,
                            "manuals": manual_list,
                            "minifigs": minifig_list
                        }
                        campos_filtrados = {k: v for k, v in campos.items() if v not in ["", None, [], 0]}
                        payload = {
                            "accion": "actualizacion",
                            "set_number": set_number_int,
                            "campos": campos_filtrados
                        }

                    # Enviar a Lambda
                    response = requests.post(LAMBDA_ADMIN, json=payload, timeout=30)

                    if response.status_code == 200:
                        data = response.json()
                        mensaje = data.get("mensaje", "Operación completada correctamente.")
                        st.success(mensaje)
                    else:
                        st.error(f"Error {response.status_code}: {response.text}")

                except requests.exceptions.RequestException as e:
                    st.error(f"Error de conexión: {str(e)}")
                except Exception as e:
                    st.error(f"Ocurrió un error inesperado: {str(e)}")


# ------------------------------------------------------------
# PIE DE PÁGINA
# ------------------------------------------------------------
st.markdown("---")
st.caption("Desarrollado por Mike Nava ⚙️ · Firestore + OpenAI + AWS Lambda + Streamlit")

import streamlit as st
import requests

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
                    response = requests.post(LAMBDA_SEARCH, json=payload, timeout=30)

                    if response.status_code == 200:
                        data = response.json()
                        respuesta = data.get("respuesta", "Sin respuesta.")
                        st.success("Respuesta:")
                        st.write(respuesta)
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

    st.divider()
    st.markdown("### 🧱 Información adicional (opcional)")
    image_url = st.text_input("🖼️ URL de imagen")
    manuals = st.text_area("📘 URLs de manuales (una por línea)", placeholder="https://...")
    minifigs = st.text_area("🧍 Minifigs (formato: nombre|número por línea)", placeholder="Luke Skywalker|SW0123")

    st.divider()

    if st.button("Enviar operación ⚙️"):
        if not set_number.strip():
            st.warning("Debes especificar al menos el número de set.")
        else:
            with st.spinner("Procesando operación..."):
                try:
                    # 👇 Conversión a número entero (nuevo)
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

                    # Armar el cuerpo según la acción
                    if accion == "alta":
                        payload = {
                            "accion": "alta",
                            "lego": {
                                "set_number": set_number_int,  # 👈 Enviar como número
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
                        payload = {
                            "accion": "baja",
                            "set_number": set_number_int  # 👈 Enviar como número
                        }

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
                            "set_number": set_number_int,  # 👈 Enviar como número
                            "campos": campos_filtrados
                        }

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

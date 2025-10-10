import streamlit as st
import requests

# ------------------------------------------------------------
# CONFIGURACIÓN GENERAL
# ------------------------------------------------------------
st.set_page_config(page_title="Asistente LEGO IA", page_icon="🧱", layout="centered")

st.title("🧱 Asistente LEGO con IA + Firestore (vía AWS Lambda)")
st.caption("Consulta tu colección LEGO por voz o texto (funciona con dictado nativo en iPhone 🗣️)")

# 👉 Reemplaza con tu endpoint real de Lambda (API Gateway)
LAMBDA_URL = "https://ztpcx6dks9.execute-api.us-east-1.amazonaws.com/default/legoSearch"

# ------------------------------------------------------------
# INTERFAZ DE USUARIO
# ------------------------------------------------------------
st.markdown("""
### Ejemplos de preguntas
- ¿Tengo el set Justifier?
- ¿Qué sets de LEGO son entre el año 2020 y 2021?
- ¿Cuántos sets de Star Wars tengo?
- ¿Qué sets tengo guardados en la caja 12?
""")

# Campo de texto estándar (ya soporta dictado nativo en iPhone)
pregunta = st.text_input(
    "🗣️ Escribe o dicta tu pregunta:",
    placeholder="Ejemplo: ¿Qué sets de LEGO tengo en la caja 12?"
)

# Botón para enviar
if st.button("Preguntar 🧱"):
    if not pregunta.strip():
        st.warning("Por favor, escribe una pregunta.")
    else:
        with st.spinner("Consultando tu colección LEGO... 🧱"):
            try:
                payload = {"pregunta": pregunta}
                response = requests.post(LAMBDA_URL, json=payload, timeout=30)

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

# ------------------------------------------------------------
# PIE DE PÁGINA
# ------------------------------------------------------------
st.markdown("---")
st.caption("Desarrollado por Mike Nava ⚙️ · Firestore + OpenAI + AWS Lambda + Streamlit")

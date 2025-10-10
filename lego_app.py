import streamlit as st
import requests
import streamlit.components.v1 as components

# ------------------------------------------------------------
# CONFIGURACIÓN GENERAL
# ------------------------------------------------------------
st.set_page_config(page_title="Asistente LEGO IA", page_icon="🧱", layout="centered")

st.title("🧱 Asistente LEGO con IA + Firestore (vía AWS Lambda)")
st.caption("Consulta tu colección LEGO por voz o texto. Compatible con dictado nativo en iPhone 🗣️")

# 👉 Reemplaza con tu endpoint de Lambda (API Gateway)
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

# ------------------------------------------------------------
# CAMPO DE TEXTO CON DICTADO NATIVO (iPhone / Safari)
# ------------------------------------------------------------
st.markdown("### 🎙️ Habla o escribe tu pregunta:")

components.html(
    """
    <div style="text-align: center;">
        <input id="voiceInput" 
               type="text"
               placeholder="Toca el micrófono del teclado para dictar tu pregunta..."
               x-webkit-speech speech
               style="width: 95%; font-size: 18px; padding: 10px;
                      border-radius: 8px; border: 1px solid #ccc; outline: none;">
    </div>
    """,
    height=70,
)

st.info("💡 En iPhone puedes tocar el micrófono del teclado para dictar tu pregunta por voz.")

# ------------------------------------------------------------
# CAMPO DE ESCRITURA MANUAL OPCIONAL
# ------------------------------------------------------------
pregunta_manual = st.text_input("O escríbela manualmente:", placeholder="¿Qué sets de LEGO son entre el año 2020 y 2021?")

# ------------------------------------------------------------
# ENVÍO DE LA PREGUNTA
# ------------------------------------------------------------
if st.button("Preguntar"):
    pregunta = pregunta_manual.strip()

    if not pregunta:
        st.warning("Por favor, escribe o dicta una pregunta.")
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

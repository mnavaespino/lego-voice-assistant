import streamlit as st
import requests
import streamlit.components.v1 as components

# ------------------------------------------------------------
# CONFIGURACIÓN GENERAL
# ------------------------------------------------------------
st.set_page_config(page_title="Asistente LEGO IA", page_icon="🧱", layout="centered")

st.title("🧱 Asistente LEGO con IA + Firestore (vía AWS Lambda)")
st.caption("Habla o escribe tu pregunta. Compatible con dictado nativo en iPhone 🗣️")

# 👉 Reemplaza con tu endpoint de Lambda (API Gateway)
LAMBDA_URL = "https://tu-api-id.execute-api.us-east-1.amazonaws.com/prod/"

# ------------------------------------------------------------
# ESTILOS
# ------------------------------------------------------------
st.markdown("""
<style>
    .main {
        text-align: center;
    }
    input[type=text] {
        width: 95%;
        font-size: 18px;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #ccc;
        outline: none;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# CAMPO ÚNICO DE ENTRADA (dictado + Enter)
# ------------------------------------------------------------
st.markdown("### 🎙️ Habla o escribe tu pregunta:")

components.html(
    """
    <div style="text-align: center;">
        <form onsubmit="enviarPregunta(); return false;">
            <input id="voiceInput"
                   type="text"
                   placeholder="Toca el micrófono del teclado o escribe tu pregunta..."
                   x-webkit-speech speech
                   autofocus>
        </form>
    </div>
    <script>
        const input = document.getElementById('voiceInput');
        function enviarPregunta() {
            const pregunta = input.value;
            if (pregunta && window.parent) {
                window.parent.postMessage({ type: 'streamlit:setComponentValue', value: pregunta }, '*');
            }
        }
        // Ejecutar también al presionar Enter directamente
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                enviarPregunta();
            }
        });
    </script>
    """,
    height=80,
)

st.info("💡 En iPhone puedes tocar el micrófono del teclado para dictar tu pregunta por voz.")

# ------------------------------------------------------------
# CAPTURAR VALOR DEL INPUT
# ------------------------------------------------------------
# Streamlit guarda el valor del componente HTML a través de la sesión
# Necesitamos leerlo dinámicamente con st.session_state para mantener persistencia
if "pregunta" not in st.session_state:
    st.session_state["pregunta"] = ""

# Pequeño truco para recibir el valor del postMessage del componente HTML
pregunta = st.session_state.get("pregunta", "")

# ------------------------------------------------------------
# BOTÓN INVISIBLE (por compatibilidad)
# ------------------------------------------------------------
# Si el usuario presiona Enter o dictado finaliza, se ejecuta el procesamiento
if pregunta:
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

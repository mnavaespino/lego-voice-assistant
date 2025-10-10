import streamlit as st
import requests
import streamlit.components.v1 as components

# ------------------------------------------------------------
# CONFIGURACIÓN GENERAL
# ------------------------------------------------------------
st.set_page_config(page_title="Asistente LEGO IA", page_icon="🧱", layout="centered")

st.title("🧱 Asistente LEGO con IA + Firestore (vía AWS Lambda)")
st.caption("Habla o escribe tu pregunta. Compatible con dictado nativo en iPhone 🗣️")

# 👉 Reemplaza con tu endpoint real de Lambda
LAMBDA_URL = "https://ztpcx6dks9.execute-api.us-east-1.amazonaws.com/default/legoSearch"

# ------------------------------------------------------------
# ESTILOS GLOBALES
# ------------------------------------------------------------
st.markdown("""
<style>
    .input-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 20px;
        margin-bottom: 10px;
    }

    input[type=text] {
        width: 90%;
        font-size: 22px;
        padding: 14px 18px;
        border-radius: 12px;
        border: 1px solid #bbb;
        outline: none;
        text-align: center;
    }

    input[type=text]:focus {
        border: 1px solid #ff5555;
        box-shadow: 0 0 6px rgba(255, 85, 85, 0.4);
    }

    button {
        margin-top: 10px;
        background-color: #ff5555;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 22px;
        font-size: 18px;
        cursor: pointer;
    }

    button:hover {
        background-color: #ff3333;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# INPUT DE TEXTO (compatible con dictado + Enter)
# ------------------------------------------------------------
components.html(
    """
    <div class="input-container">
        <form onsubmit="enviarPregunta(); return false;">
            <input id="voiceInput"
                   type="text"
                   placeholder="Toca el micrófono del teclado o escribe tu pregunta..."
                   x-webkit-speech speech autofocus />
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
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                enviarPregunta();
            }
        });
    </script>
    """,
    height=100,
)

st.info("💡 En iPhone puedes tocar el micrófono del teclado para dictar tu pregunta por voz.")

# ------------------------------------------------------------
# CAPTURA DEL VALOR DEL INPUT
# ------------------------------------------------------------
if "pregunta" not in st.session_state:
    st.session_state["pregunta"] = ""

pregunta = st.session_state.get("pregunta", "").strip()

# ------------------------------------------------------------
# BOTÓN MANUAL (por compatibilidad)
# ------------------------------------------------------------
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    enviar = st.button("Preguntar 🧱")

# Ejecutar tanto con Enter como con botón
if pregunta or enviar:
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

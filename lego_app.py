import os, io, json, requests, streamlit as st, soundfile as sf
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
LEGO_API_URL = os.getenv("LEGO_API_URL")

# --- función que llama tu Lambda ---
def buscar_lego(q):
    r = requests.get(LEGO_API_URL, params={"q": q})
    try:
        d = r.json()
        if "body" in d and isinstance(d["body"], str):
            d["body"] = json.loads(d["body"])
        return d
    except Exception:
        return {"error": r.text}

# --- configuraciones ---
st.set_page_config(page_title="LEGO Assistant", page_icon="🧱")
st.title("🧱 Mi Asistente LEGO por Voz")

# --- grabar audio (usa el componente de Streamlit) ---
audio_file = st.audio_input("Habla para buscar un set o minifigura")

if audio_file is not None:
    with st.spinner("Transcribiendo tu voz..."):
        transcription = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=audio_file
        )
        pregunta = transcription.text.strip()
        st.write(f"**🗣️ Pregunta:** {pregunta}")

        # --- GPT decide si usa la herramienta ---
        tools = [{
            "type": "function",
            "function": {
                "name": "buscar_lego",
                "description": "Busca sets o minifigs en la colección LEGO personal",
                "parameters": {
                    "type": "object",
                    "properties": {"q": {"type": "string"}},
                    "required": ["q"]
                }
            }
        }]

        messages = [
        {
            "role": "system",
            "content": (
                "Eres un asistente especializado en colecciones LEGO en español. "
                "Tu base de conocimiento principal son los datos reales del usuario, accesibles mediante la función 'buscar_lego'. "
                "Si el usuario hace una pregunta sobre cualquier set, minifigura o detalle de su colección (nombre, caja, tema, condición, año, tienda, etc.), "
                "usa siempre 'buscar_lego' para obtener la información precisa. "
                "Nunca inventes datos ni hagas suposiciones sin consultar esa fuente. "
                "Después de consultar, resume los resultados de forma clara y natural en forma de resumen"
            )
        },
        {
            "role": "user",
            "content": pregunta
        }
    ]

        first = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        msg = first.choices[0].message
        calls = msg.tool_calls or []

        if calls:
            for c in calls:
                if c.function.name == "buscar_lego":
                    q = json.loads(c.function.arguments).get("q", "")
                    data = buscar_lego(q)
                    messages.append(msg)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": c.id,
                        "name": "buscar_lego",
                        "content": json.dumps(data, ensure_ascii=False)
                    })

        # --- segunda llamada GPT ---
        final = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        respuesta = final.choices[0].message.content
        st.markdown(f"### 🧱 Respuesta\n{respuesta}")

        # --- voz ---
        tts = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=respuesta
        )
        audio_bytes = tts.read()
        st.audio(audio_bytes, format="audio/mp3")



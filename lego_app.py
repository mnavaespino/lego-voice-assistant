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
                "Eres un asistente LEGO en español especializado en colecciones personales. "
                "Tu conocimiento proviene exclusivamente de la base de datos del usuario, "
                "accesible mediante la función 'buscar_lego'. "
                "Esa función puede devolver información de sets o minifiguras en formato JSON.\n\n"
    
                "📦 **Para sets**, el JSON tiene esta estructura:\n"
                "{\n"
                "  'results': [\n"
                "    {\n"
                "      'set_number': número del set LEGO,\n"
                "      'name': nombre oficial del set,\n"
                "      'theme': tema o colección (Star Wars, City, Technic, etc.),\n"
                "      'year': año de lanzamiento,\n"
                "      'pieces': número de piezas,\n"
                "      'storage_box': número de caja o ubicación física,\n"
                "      'tags': palabras clave asociadas,\n"
                "      'image_url': URL de imagen,\n"
                "      'manuals': lista de manuales (cada uno con 'manual_number' y 'file_url'),\n"
                "      'condition': estado del set (nuevo, usado, en caja, etc.)\n"
                "    }\n"
                "  ]\n"
                "}\n\n"
    
                "🧱 **Para minifigs**, el JSON tiene esta estructura:\n"
                "{\n"
                "  'results': [\n"
                "    {\n"
                "      'minifig_number': código de la figura,\n"
                "      'name': nombre del personaje,\n"
                "      'theme': tema o saga (Star Wars, City, Ninjago, etc.),\n"
                "      'appearances': lista con los números de set donde aparece,\n"
                "      'image_url': imagen de la figura,\n"
                "      'search_tokens': texto de búsqueda para coincidencias parciales\n"
                "    }\n"
                "  ]\n"
                "}\n\n"
    
                "Tu tarea es interpretar preguntas naturales del usuario sobre su colección LEGO "
                "(por ejemplo ubicación, tema, año, número de piezas o relaciones entre sets y minifigs). "
                "Si la pregunta se refiere a un set, minifigura o tema, debes usar 'buscar_lego' con las palabras clave relevantes "
                "y luego responder de manera clara, conversacional y precisa usando los datos del JSON, por ejemplo:\n\n"
                "'El set Republic Gunship está en la caja 8, tiene 3292 piezas y pertenece a la serie Star Wars (2021)'. "
    
                "Cuando respondas:\n"
                "- Resume la información más relevante (nombre, número, ubicación, tema, año, piezas, etc.)\n"
                "- Si hay varias coincidencias, menciona las más parecidas.\n"
                "- Si no hay resultados, dilo amablemente y sugiere cómo podría buscarlo.\n"
                "- Nunca inventes información que no esté en los datos devueltos.\n"
                "- Si un minifig aparece en varios sets, descríbelos brevemente.\n"
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



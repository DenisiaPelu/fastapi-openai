from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import AsyncOpenAI
import pandas as pd
import dateparser
import re
from datetime import datetime
import uuid
import os



app = FastAPI()
client = AsyncOpenAI()

# ✅ Historial de sesiones en memoria
chat_history = {}

# ✅ Cargar base de datos de actividades
csv_path = os.path.join(os.path.dirname(__file__), "complete_db_05_06_2025.csv")
df = pd.read_csv(csv_path)

# ✅ Estructura de datos de entrada
class Prompt(BaseModel):
    prompt: str
    session_id: str = None  # opcional; se genera si no se pasa

# ✅ Funciones auxiliares
def extraer_edad(texto):
    match = re.search(r"(\d{1,2})\s*(años|año)", texto)
    if match:
        edad = int(match.group(1))
        if edad < 14:
            return edad
    return None

def extraer_ciudad(texto):
    ciudades = df["city"].unique()
    for ciudad in ciudades:
        if ciudad.lower() in texto.lower():
            return ciudad.lower()
    return None

def extraer_fecha(texto):
    today = datetime.now()
    fecha = dateparser.parse(
        texto,
        settings={
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": today
        }
    )
    if fecha:
        return fecha.date().isoformat()
    return None


def obtener_clima(fecha, ciudad):
    # Simulación de clima simple
    return "nublado" if datetime.fromisoformat(fecha).day % 2 == 0 else "soleado"

# ✅ Ruta principal del asistente
@app.post("/generate")
async def generate(data: Prompt):
    prompt = data.prompt.lower()
    session_id = data.session_id or str(uuid.uuid4())

    edad = extraer_edad(prompt)
    ciudad = extraer_ciudad(prompt)
    fecha = extraer_fecha(prompt)

    actividades = pd.DataFrame()
    clima = None

    if (ciudad and edad) or (ciudad and edad and fecha):
        try:
            actividades = df[
                (df["min_age"] <= edad) &
                (df["max_age"] >= edad) &
                (df["city"] == ciudad) &
                (df["start_date"] == fecha)
            ]
            clima = obtener_clima(fecha, ciudad)
        except Exception as e:
            print("❌ Error filtrando actividades:", e)

    # ✅ Si hay actividades disponibles, las recomendamos directamente
    if not actividades.empty:
        preferidas = actividades[actividades["interior"] == (clima == "nublado")]
        if preferidas.empty:
            preferidas = actividades

        lista_actividades = "\n".join(f"- {a}" for a in preferidas["name"].tolist())

        respuesta = (
            f"¡Hola! 😊 He encontrado estas ideas para el {fecha} en {ciudad.title()}, "
            f"ideales para peques de {edad} años. Como se espera un día {clima}, "
            f"estas actividades {'en interior' if clima == 'nublado' else 'al aire libre'} pueden ser perfectas:\n\n"
            f"{lista_actividades}.\n\n"
            f"¿Te gustaría que te recomiende otras opciones o más detalles?"
        )

        chat_history.setdefault(session_id, [])
        chat_history[session_id].append({"role": "user", "content": data.prompt})
        chat_history[session_id].append({"role": "assistant", "content": respuesta})

        return {"response": respuesta, "session_id": session_id}

    # ✅ Si no hay datos suficientes o no hay coincidencias, usamos el modelo de OpenAI
    chat_history.setdefault(session_id, [])
    chat_history[session_id].append({"role": "user", "content": data.prompt})
    history_limit = chat_history[session_id][-10:]

    # ➕ Crear resumen de las actividades disponibles
    resumen_actividades = "\n".join(
        f"- {row['name']} (edades {row['min_age']}-{row['max_age']}, en {row['city']}, el {row['start_date']}, {'interior' if row['interior'] else 'exterior'})"
        for _, row in df.iterrows()
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": (
                    "Eres un asistente amable, natural y cercano, que recomienda actividades para padres con niños menores de 14 años. "
                    "Improvisa si no tienes toda la información, basándote en este catálogo:\n"
                    f"{resumen_actividades}\n"
                    "Ten en cuenta el tiempo (soleado o nublado) según el día."
                )},
                *history_limit
            ],
            max_tokens=200
        )
        respuesta_ai = response.choices[0].message.content
        chat_history[session_id].append({"role": "assistant", "content": respuesta_ai})

        return {"response": respuesta_ai, "session_id": session_id}
    except Exception as e:
        print(f"❌ Error OpenAI: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# {
#     "prompt": "me llamo Marta y quiero ir mañana a madrid con mi hijo de 6 años , que me recomiendas? "
# }

# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from openai import OpenAI
# import os

# # ✅ Cliente de OpenAI usando variable de entorno automáticamente
# client = OpenAI()

# # ✅ App de FastAPI
# app = FastAPI()

# # ✅ Modelo de entrada
# class Prompt(BaseModel):
#     prompt: str

# # ✅ Ruta POST
# @app.post("/generate")
# def generate(data: Prompt):
#     print(f"📥 Recibido prompt: {data.prompt}")
#     try:
#         response = client.chat.completions.create(
#             model="gpt-3.5-turbo",
#             messages=[{"role": "user", "content": data.prompt}],
#             max_tokens=150
#         )
#         return {"response": response.choices[0].message.content}
#     except Exception as e:
#         print(f"❌ Error OpenAI: {e}")
#         raise HTTPException(status_code=400, detail=str(e))





from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from openai import OpenAI
import pandas as pd
import dateparser
import re
from datetime import datetime
import uuid

app = FastAPI()
client = OpenAI()

# ✅ Memoria temporal en memoria
chat_history = {}

# ✅ Base de datos simulada
data = [
    {"actividad": "Títeres en el parque", "edad_min": 3, "edad_max": 7, "ciudad": "madrid", "fecha": "2025-05-06", "interior": False},
    {"actividad": "Museo de Ciencia", "edad_min": 5, "edad_max": 12, "ciudad": "madrid", "fecha": "2025-05-06", "interior": True},
    {"actividad": "Cuentacuentos", "edad_min": 4, "edad_max": 10, "ciudad": "madrid", "fecha": "2025-05-07", "interior": True},
    {"actividad": "Parque aventuras", "edad_min": 6, "edad_max": 13, "ciudad": "madrid", "fecha": "2025-05-06", "interior": False},
    {"actividad": "Taller arte infantil", "edad_min": 5, "edad_max": 9, "ciudad": "madrid", "fecha": "2025-05-08", "interior": True},
]
df = pd.DataFrame(data)

class Prompt(BaseModel):
    prompt: str
    session_id: str = None  # opcional; se genera si no se pasa

# ✅ Utilidades para extraer edad, ciudad y fecha

def extraer_edad(texto):
    match = re.search(r"(\d{1,2})\s*(años|año)", texto)
    if match:
        edad = int(match.group(1))
        if edad < 14:
            return edad
    return None

def extraer_ciudad(texto):
    ciudades = ["madrid"]
    for ciudad in ciudades:
        if ciudad.lower() in texto.lower():
            return ciudad.lower()
    return None

def extraer_fecha(texto):
    fecha = dateparser.parse(texto, settings={"PREFER_DATES_FROM": "future"})
    if fecha:
        return fecha.date().isoformat()
    return None

def obtener_clima(fecha, ciudad):
    return "nublado" if datetime.fromisoformat(fecha).day % 2 == 0 else "soleado"

# ✅ Ruta principal con historial

@app.post("/generate")
def generate(data: Prompt):
    prompt = data.prompt.lower()
    session_id = data.session_id or str(uuid.uuid4())

    edad = extraer_edad(prompt)
    ciudad = extraer_ciudad(prompt)
    fecha = extraer_fecha(prompt)

    actividades = pd.DataFrame()
    clima = None

    if ciudad and edad and (fecha is not None):
        actividades = df[
            (df["edad_min"] <= edad) &
            (df["edad_max"] >= edad) &
            (df["ciudad"] == ciudad) &
            (df["fecha"] == fecha)
        ]
        clima = obtener_clima(fecha, ciudad)

    # ✅ Generar mensaje propio si tenemos datos
    if not actividades.empty:
        preferidas = actividades[actividades["interior"] == (clima == "nublado")]
        if preferidas.empty:
            preferidas = actividades

        lista_actividades = "\n".join(f"- {a}" for a in preferidas["actividad"].tolist())
        respuesta = (
            f"¡Hola! 😊 Para el {fecha} en {ciudad.title()} con tu peque de {edad} años, "
            f"te recomiendo estas actividades:\n{lista_actividades}.\n"
            f"El día estará {clima}, así que ¡estas opciones son geniales!"
        )

        # ✅ Guardar en historial
        chat_history.setdefault(session_id, [])
        chat_history[session_id].append({"role": "user", "content": data.prompt})
        chat_history[session_id].append({"role": "assistant", "content": respuesta})

        return {"response": respuesta, "session_id": session_id}

    # ✅ Usar historial para completar con OpenAI
    chat_history.setdefault(session_id, [])
    chat_history[session_id].append({"role": "user", "content": data.prompt})

    history_limit = chat_history[session_id][-10:]  # últimas 5 interacciones
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": (
                    "Eres un asistente amable, familiar y útil para padres con niños menores de 14 años. "
                    "Solo das información relevante para actividades infantiles. No opinas sobre temas ajenos a ese objetivo."
                )},
                *history_limit
            ],
            max_tokens=150
        )
        respuesta_ai = response.choices[0].message.content
        chat_history[session_id].append({"role": "assistant", "content": respuesta_ai})

        return {"response": respuesta_ai, "session_id": session_id}
    except Exception as e:
        print(f"❌ Error OpenAI: {e}")
        raise HTTPException(status_code=400, detail=str(e))

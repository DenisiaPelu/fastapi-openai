from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import os

# ✅ Cliente de OpenAI usando variable de entorno automáticamente
client = OpenAI()

# ✅ App de FastAPI
app = FastAPI()

# ✅ Modelo de entrada
class Prompt(BaseModel):
    prompt: str

# ✅ Ruta POST
@app.post("/generate/")
def generate(data: Prompt):
    print(f"📥 Recibido prompt: {data.prompt}")
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": data.prompt}],
            max_tokens=150
        )
        return {"response": response.choices[0].message.content}
    except Exception as e:
        print(f"❌ Error OpenAI: {e}")
        raise HTTPException(status_code=400, detail=str(e))


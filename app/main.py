from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
from openai import OpenAI
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI()  # Usa la clave desde la variable de entorno OPENAI_API_KEY automáticamente

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

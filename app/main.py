from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

print(f"🔑 OPENAI_API_KEY empieza con: {openai.api_key[:5]}...")

app = FastAPI()

class Prompt(BaseModel):
    prompt: str

@app.post("/generate/")
def generate(data: Prompt):
    try:
        print(f"📥 Recibido prompt: {data.prompt}") 
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # modelo accesible
            messages=[{"role": "user", "content": data.prompt}],
            max_tokens=150
        )
        return {"response": response.choices[0].message["content"]}
    except Exception as e:
        print(f"❌ Error OpenAI: {e}")  # Esto aparecerá en los logs de Render
        raise HTTPException(status_code=400, detail=str(e))

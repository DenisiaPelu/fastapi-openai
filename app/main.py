from fastapi import FastAPI
from pydantic import BaseModel
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

class Prompt(BaseModel):
    prompt: str

@app.post("/generate/")
def generate(data: Prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": data.prompt}]
        max_tokens=150
    )
    return {"response": response.choices[0].message["content"]}
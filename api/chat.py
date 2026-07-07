from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_URL = "https://api.overchat.ai/v1/chat/completions"

class ChatRequest(BaseModel):
    prompt: str
    history: list = []

@app.post("/")
def chat_endpoint(req: ChatRequest):
    device_uuid = str(uuid.uuid4())
    chat_id = str(uuid.uuid4())
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Origin": "https://overchat.ai",
        "Referer": "https://overchat.ai/",
        "X-Device-Platform": "web",
        "X-Device-Language": "en-US",
        "X-Device-Uuid": device_uuid,
        "X-Device-Version": "1.0.44",
    }

    messages = [{"id": str(uuid.uuid4()), "role": "system", "content": ""}]
    
    for msg in req.history:
        messages.append({
            "id": str(uuid.uuid4()),
            "role": msg.get("role"),
            "content": msg.get("content")
        })
        
    messages.append({
        "id": str(uuid.uuid4()),
        "role": "user",
        "content": req.prompt
    })

    payload = {
        "chatId": chat_id,
        "model": "openai/gpt-4o",
        "messages": messages,
        "personaId": "free-gpt-chat-landing",
        "frequency_penalty": 0,
        "max_tokens": 4000,
        "presence_penalty": 0,
        "stream": False,
        "temperature": 0.5,
        "top_p": 0.95
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=15)
        
        if response.status_code != 200:
            return {"error": "Upstream API error", "details": response.text}

        data = response.json()
        ai_message = data['choices'][0]['message']['content']
        
        return {"response": ai_message}

    except Exception as e:
        return {"error": str(e)}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import uuid
import json

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

@app.post("/api/chat")
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
        # We must use stream=True here because Overchat forces streaming anyway
        response = requests.post(API_URL, headers=headers, json=payload, stream=True, timeout=30)
        
        if response.status_code != 200:
            return {"error": "Upstream API error", "details": response.text}

        full_response = ""
        
        # Read the stream and stitch the chunks together
        for line in response.iter_lines():
            if line:
                decoded = line.decode("utf-8")
                if decoded.startswith("data:"):
                    data_str = decoded[5:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        token = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if token:
                            full_response += token
                    except:
                        pass
        
        return {"response": full_response}

    except Exception as e:
        return {"error": str(e)}

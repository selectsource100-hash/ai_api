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
        "stream": True,
        "temperature": 0.5,
        "top_p": 0.95
    }

    try:
        # EXACT same logic as your working python script
        with requests.post(API_URL, headers=headers, json=payload, stream=True, timeout=60) as response:
            
            # The API might return 200 or 201, so we accept both
            if response.status_code not in (200, 201):
                return {"error": "Upstream API error", "status": response.status_code, "details": response.text}

            full_response = ""
            
            # Read the stream chunk by chunk
            for line in response.iter_lines():
                if not line:
                    continue
                    
                decoded = line.decode("utf-8")
                
                if not decoded.startswith("data:"):
                    continue
                    
                data_str = decoded[5:].strip()
                
                if data_str == "[DONE]":
                    break
                    
                try:
                    chunk = json.loads(data_str)
                    token = (
                        chunk
                        .get("choices", [{}])[0]
                        .get("delta", {})
                        .get("content", "")
                    )
                    
                    if token:
                        full_response += token
                except json.JSONDecodeError:
                    pass
            
            return {"response": full_response}

    except Exception as e:
        return {"error": str(e)}

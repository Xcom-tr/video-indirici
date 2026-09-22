from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import os
import base64

app = FastAPI(title="Yapay Zeka Seslendirme Fabrikası")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Senin gerçek API anahtarın
ELEVEN_API_KEY = "sk_34d6ccb20fd2701710e8a77db641ddd1308a4f1f6d573b86"

class TTSRequest(BaseModel):
    text: str

@app.get("/", response_class=HTMLResponse)
def read_root():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h3>index.html dosyasi bulunamadi!</h3>"

@app.post("/api/tts")
def text_to_speech(request: TTSRequest):
    if not ELEVEN_API_KEY:
        raise HTTPException(status_code=500, detail="API Key eksik!")

    # ADRESİ BURADA TAMAMEN DÜZ METİN OLARAK SABİTLEDİK (Python artık hata yapamaz)
    url = "https://elevenlabs.io"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVEN_API_KEY
    }
    
    data = {
        "text": request.text,
        "model_id": "eleven_multilingual_v2", 
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"ElevenLabs Hatasi: {response.text}")
        
        if len(response.content) == 0:
            raise HTTPException(status_code=500, detail="Sunucudan bos ses verisi dondu.")
            
        audio_base64 = base64.b64encode(response.content).decode('utf-8')
        
        return {
            "success": True,
            "audio_data": audio_base64
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Sistem Hatasi: {str(e)}")

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

# API Anahtarın buraya kusursuz bir şekilde eklendi, başka hiçbir yere dokunmana gerek yok!
ELEVEN_API_KEY = "sk_fd839d43f72167fe979334d70f42ce168cfa3ca379f7a079"

class TTSRequest(BaseModel):
    text: str
    # En güncel ve Türkçe destekleyen standart erkek sesi (Drew Kimliği)
    voice_id: str = "N2lVS1wndvVkZsaEw56I" 

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

    # ElevenLabs güncel seslendirme uç noktası
    url = f"https://elevenlabs.io{request.voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVEN_API_KEY
    }
    
    data = {
        "text": request.text,
        # En yeni ve hatasız çalışan Türkçe destekli çok dilli yapay zeka modeli
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
            raise HTTPException(status_code=500, detail="Sunucudan boş ses verisi döndü.")
            
        audio_base64 = base64.b64encode(response.content).decode('utf-8')
        
        return {
            "success": True,
            "audio_data": audio_base64
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Sistem Hatası: {str(e)}")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import requests
import io
import os

app = FastAPI(title="Yapay Zeka Seslendirme Fabrikası")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Senin çalışan tam yetkili anahtarın
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

    # Her hesapta varsayılan açık olan Rachel sesi
    url = "https://elevenlabs.io"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVEN_API_KEY,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
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
        # Akış modunda (stream=True) istek atıyoruz
        response = requests.post(url, json=data, headers=headers, timeout=30, stream=True)
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"ElevenLabs Hatasi: {response.text}")
        
        # Tarayıcının süreyi tanıyabilmesi için veriyi bellek üzerinden canlı akış olarak fırlatıyoruz
        return StreamingResponse(
            io.BytesIO(response.content), 
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=speech.mp3"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Sistem Hatasi: {str(e)}")

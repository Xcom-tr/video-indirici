from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import yt_dlp
import os

app = FastAPI(title="Video Downloader API")

# Sunucunun dış dünyaya açılması için CORS köprüsü
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    url: str

# Ana sayfaya girildiğinde index.html'i internet sayfası gibi açar
@app.get("/", response_class=HTMLResponse)
def read_root():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h3>index.html dosyasi bulunamadi!</h3>"

@app.post("/api/analyze")
def analyze_video(request: VideoRequest):
    video_url = request.url
    
    # Canlı sunucu için en kararlı YouTube çözücü ayarları
    ydl_opts = {
        'skip_download': True,
        'format': 'best',
        'noplaylist': True,
        'extract_flat': False,
        'socket_timeout': 30,
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            
            if 'entries' in info_dict:
                info_dict = info_dict['entries']
                
            title = info_dict.get('title', 'Bilinmeyen Video')
            thumbnail = info_dict.get('thumbnail', '')
            duration = info_dict.get('duration', 0)
            
            formats_list = []
            for f in info_dict.get('formats', []):
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('url'):
                    quality = f.get('height')
                    quality_str = f"{quality}p" if quality else f.get('format_note', 'Hazir Kalite')
                    
                    formats_list.append({
                        'quality': quality_str,
                        'ext': f.get('ext', 'mp4'),
                        'download_url': f.get('url'),
                    })
            
            if not formats_list and info_dict.get('url'):
                formats_list.append({
                    'quality': 'Standart Kalite',
                    'ext': info_dict.get('ext', 'mp4'),
                    'download_url': info_dict.get('url')
                })
            
            formats_list.reverse()
            return {
                "success": True,
                "title": title,
                "thumbnail": thumbnail,
                "duration": f"{duration // 60}:{duration % 60:02d}",
                "links": formats_list
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Hata: {str(e)}")

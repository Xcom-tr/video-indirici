from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import yt_dlp
import os

app = FastAPI(title="Video Downloader API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    url: str

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
    
    # YouTube ve Instagram bot algılama duvarlarını aşmak için en kararlı istemci ayarları
    ydl_opts = {
        'skip_download': True,
        'format': 'best',
        'noplaylist': True,
        'extract_flat': False,
        'socket_timeout': 25, 
        'ignoreerrors': True,
        'no_warnings': True,
        # YouTube'un yeni bot engellerini aşmak için istemciyi "web_embedded" (gömülü oynatıcı) olarak taklit ediyoruz
        'extractor_args': {
            'youtube': {
                'player_client': ['web_embedded'],
            }
        },
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            
            if not info_dict:
                raise HTTPException(status_code=400, detail="Video bilgileri sökülemedi. Lütfen linki kontrol edin.")
                
            if 'entries' in info_dict:
                info_dict = info_dict['entries'][0] if info_dict['entries'] else info_dict
                
            title = info_dict.get('title', 'Bilinmeyen Video')
            thumbnail = info_dict.get('thumbnail', '')
            duration = info_dict.get('duration', 0)
            
            formats_list = []
            
            for f in info_dict.get('formats', []):
                if f.get('url') and f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    quality = f.get('height')
                    quality_str = f"{quality}p" if quality else f.get('format_note', 'Hazır Kalite')
                    
                    if not any(x['download_url'] == f.get('url') for x in formats_list):
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
                "duration": f"{duration // 60}:{duration % 60:02d}" if duration else "N/A",
                "links": formats_list[:4]
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Sunucu Hatası: {str(e)}")

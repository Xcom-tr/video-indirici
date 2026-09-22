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
    
    # Instagram ve YouTube engellerini aşmak için genişletilmiş sunucu ayarları
    ydl_opts = {
        'skip_download': True,
        'format': 'best/bestvideo+bestaudio', # Instagram için en iyi kaliteleri zorla
        'noplaylist': True,
        'extract_flat': False,
        'socket_timeout': 15, # Sunucu kilitlenmesin diye timeout süresini 15 saniye yaptık
        'ignoreerrors': True,
        'no_warnings': True,
        'headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://instagram.com',
            'Referer': 'https://instagram.com/',
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            
            if not info_dict:
                raise HTTPException(status_code=400, detail="Video bilgileri alınamadı. Link gizli veya hatalı olabilir.")
                
            if 'entries' in info_dict:
                info_dict = info_dict['entries'][0] if info_dict['entries'] else info_dict
                
            title = info_dict.get('title', 'Instagram Videosu' if 'instagram' in video_url else 'Bilinmeyen Video')
            thumbnail = info_dict.get('thumbnail', '')
            duration = info_dict.get('duration', 0)
            
            formats_list = []
            
            # Instagram genellikle doğrudan tek link verir, önce onu kontrol et
            if 'instagram.com' in video_url and info_dict.get('url'):
                formats_list.append({
                    'quality': 'Yüksek Kalite (HD)',
                    'ext': info_dict.get('ext', 'mp4'),
                    'download_url': info_dict.get('url')
                })
            
            # Diğer format alternatiflerini tara
            for f in info_dict.get('formats', []):
                if f.get('url') and (f.get('vcodec') != 'none' or 'instagram' in video_url):
                    quality = f.get('height')
                    quality_str = f"{quality}p" if quality else f.get('format_note', 'Hazır Format')
                    
                    # Tekrarlanan linkleri eklememek için kontrol yap
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
                "links": formats_list[:4] # Ekranda kalabalık yapmaması için en iyi 4 linki ver
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Sistem Hatası: {str(e)}")

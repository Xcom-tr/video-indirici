FROM python:3.10-slim

# İnternet sunucusuna video birleştirme motoru olan FFmpeg'i kuruyoruz
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Sitemizi Render sunucusunun istediği 10000 portundan yayına alıyoruz
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import yt_dlp
import os
import requests

app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

YOUTUBE_API_KEY = "AIzaSyCPwlgw_CQuTHmjUkfeXutcnf54Wl9nNs8"  # <--- put your key here

@app.get("/search")
def search_music(query: str):
    # 1. Search on YouTube
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&maxResults=1&q={query}&key={YOUTUBE_API_KEY}"
    r = requests.get(url)
    results = r.json()

    if "items" not in results or not results["items"]:
        return JSONResponse({"error": "No results found"}, status_code=404)

    video_id = results["items"][0]["id"]["videoId"]
    title = results["items"][0]["snippet"]["title"]

    # 2. Download audio
    output_dir = "static/audio"
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_dir}/{video_id}.mp3',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'noplaylist': True,
        'quiet': True,
    }

    filepath = f'{output_dir}/{video_id}.mp3'
    
    if not os.path.exists(filepath):  # Download only if not already downloaded
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])

    # 3. Return audio file URL
    return {
        "title": title,
        "audio_url": f"/static/audio/{video_id}.mp3"
    }

# Run with: uvicorn main:app --reload

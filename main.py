from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import requests
import time
import threading
from pytube import YouTube  # 🚀 Use pytube now
import ffmpeg  # 🔥 New import


# 🔥 Create folders if missing
os.makedirs("static/audio", exist_ok=True)

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Background file cleaner
def clean_old_audio_files():
    while True:
        folder = "static/audio"
        now = time.time()

        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)

            if os.path.isfile(file_path):
                file_age = now - os.path.getmtime(file_path)
                if file_age > 600:  # 10 minutes
                    try:
                        os.remove(file_path)
                        print(f"Deleted old file: {file_path}")
                    except Exception as e:
                        print(f"Error deleting file {file_path}: {e}")

        time.sleep(60)  # Run every 1 minute

# Start cleaner
threading.Thread(target=clean_old_audio_files, daemon=True).start()

YOUTUBE_API_KEY = "YOUR_API_KEY_HERE"  # <--- put your key here

# 🎵 Function to download audio using pytube
def download_audio(video_url, video_id):
    yt = YouTube(video_url)
    audio_stream = yt.streams.filter(only_audio=True).first()
    temp_path = f"static/audio/{video_id}.mp4"  # First save as mp4
    final_path = f"static/audio/{video_id}.mp3"  # Will convert to mp3

    if not os.path.exists(final_path):  # If already converted, no need
        if not os.path.exists(temp_path):
            audio_stream.download(output_path="static/audio", filename=f"{video_id}.mp4")

        # Convert to mp3 using ffmpeg
        stream = ffmpeg.input(temp_path)
        stream = ffmpeg.output(stream, final_path, format='mp3', acodec='libmp3lame')
        ffmpeg.run(stream, overwrite_output=True)

        # After conversion, delete the .mp4 temp file
        os.remove(temp_path)

    return final_path

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

    video_url = f"https://www.youtube.com/watch?v={video_id}"

    # 2. Download audio
    download_audio(video_url, video_id)

    # 3. Return audio file URL
    return {
    "title": title,
    "audio_url": f"/static/audio/{video_id}.mp3"  # Now it’s truly .mp3!
}


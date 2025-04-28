from flask import Flask, Response, request, send_file
import yt_dlp
import os
import threading
import time
import uuid
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow requests from anywhere

TMP_FOLDER = '/tmp'

def download_audio(query):
    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(TMP_FOLDER, filename)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': filepath,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'default_search': 'ytsearch1',
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([query])

    return filepath

def schedule_file_deletion(filepath, delay_seconds=600):
    def delete_file():
        time.sleep(delay_seconds)
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"Deleted {filepath}")
    threading.Thread(target=delete_file, daemon=True).start()

@app.route('/stream')
def stream():
    query = request.args.get('query')
    if not query:
        return {"error": "Missing query"}, 400

    try:
        filepath = download_audio(query)
        schedule_file_deletion(filepath, delay_seconds=600)  # Delete after 10 min
        return send_file(filepath, mimetype='audio/mpeg')
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/')
def home():
    return "YouTube MP3 Streamer is running!"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)

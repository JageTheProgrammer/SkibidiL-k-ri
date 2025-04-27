import os
import time
import threading
from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS  # ✅ Correct
from pytube import Search, YouTube
from pydub import AudioSegment

app = Flask(__name__)
CORS(app)
DOWNLOAD_FOLDER = "downloads"

# Create download folder if not exists
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def delete_file_later(filepath, delay=480):
    time.sleep(delay)
    if os.path.exists(filepath):
        os.remove(filepath)

@app.route("/search", methods=["GET"])
def search_song():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    # Search on YouTube
    try:
        s = Search(query)
        video = s.results[0]
        yt = YouTube(video.watch_url)
    except Exception as e:
        return jsonify({"error": "Failed to fetch video: " + str(e)}), 500

    try:
        audio_stream = yt.streams.filter(only_audio=True).first()
        output_path = os.path.join(DOWNLOAD_FOLDER, f"{yt.video_id}.mp4")
        final_mp3 = os.path.join(DOWNLOAD_FOLDER, f"{yt.video_id}.mp3")

        # Download
        audio_stream.download(filename=output_path)

        # Convert to MP3
        audio = AudioSegment.from_file(output_path)
        audio.export(final_mp3, format="mp3")

        # Delete original mp4
        os.remove(output_path)

        # Auto delete after 8 minutes
        threading.Thread(target=delete_file_later, args=(final_mp3,)).start()

        return jsonify({"audio_url": f"/stream/{yt.video_id}.mp3"})
    except Exception as e:
        return jsonify({"error": "Download failed: " + str(e)}), 500

@app.route("/stream/<filename>")
def stream_audio(filename):
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        return send_file(filepath)
    else:
        abort(404)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

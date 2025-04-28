from flask import Flask, request, send_file, jsonify
from pytube import YouTube, Search
import os
import threading
import time
import uuid

app = Flask(__name__)

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def delete_file_later(filepath, delay=600):
    def delete():
        time.sleep(delay)
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"Deleted: {filepath}")
    threading.Thread(target=delete).start()

@app.route('/download', methods=['POST'])
def download_audio():
    data = request.json
    query = data.get('query')

    if not query:
        return jsonify({'error': 'No query provided.'}), 400

    try:
        # Search and get the first result
        search = Search(query)
        video = search.results[0]

        # Download audio
        yt = YouTube(video.watch_url)
        audio_stream = yt.streams.filter(only_audio=True).first()

        filename = f"{uuid.uuid4()}.mp3"
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)

        audio_stream.download(output_path=DOWNLOAD_FOLDER, filename=filename)

        # Schedule file deletion
        delete_file_later(filepath)

        # Return file URL
        return jsonify({'file_url': f"/file/{filename}"})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/file/<filename>')
def serve_file(filename):
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        return send_file(filepath, mimetype='audio/mp3')
    else:
        return jsonify({'error': 'File not found.'}), 404

@app.route('/')
def home():
    return "Server is running!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

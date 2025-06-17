from flask import Flask, request, jsonify, send_file
import os
import uuid
import openai
from dotenv import load_dotenv
import subprocess

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def transcribe_video(input_path, srt_path):
    audio_path = input_path.replace(".mp4", ".mp3")
    subprocess.run(["ffmpeg", "-i", input_path, audio_path], check=True)

    with open(audio_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file, response_format="srt")

    with open(srt_path, "w") as f:
        f.write(transcript)

    os.remove(audio_path)

def burn_subtitles(video_path, srt_path, output_path):
    subprocess.run([
        "ffmpeg", "-i", video_path,
        "-vf", f"subtitles={srt_path}",
        "-c:a", "copy",
        output_path
    ], check=True)

@app.route('/subtitles', methods=['POST'])
def add_subtitles():
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file uploaded'}), 400

    unique_id = uuid.uuid4().hex
    input_path = os.path.join(OUTPUT_DIR, f"input_{unique_id}.mp4")
    srt_path = os.path.join(OUTPUT_DIR, f"subtitles_{unique_id}.srt")
    output_path = os.path.join(OUTPUT_DIR, f"subbed_{unique_id}.mp4")

    file.save(input_path)

    try:
        transcribe_video(input_path, srt_path)
        burn_subtitles(input_path, srt_path, output_path)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({
        "message": "Subtitles added",
        "download_url": f"/download/{os.path.basename(output_path)}"
    })

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404
    return send_file(path, as_attachment=True)

@app.route('/', methods=['GET'])
def health():
    return jsonify({"status": "Subtitle service running"}), 200

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)

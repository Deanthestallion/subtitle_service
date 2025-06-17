from flask import Flask, request, jsonify, send_file
import os
import uuid
import subprocess
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Only load OpenAI when needed
def transcribe_video(input_path, srt_path):
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")

    audio_path = input_path.replace(".mp4", ".mp3")
    subprocess.run(["ffmpeg", "-i", input_path, audio_path], check=True)

    with open(audio_path, "rb") as audio_file:
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="srt"
        )

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

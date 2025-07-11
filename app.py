import os
import uuid
import subprocess
from flask import Flask, request, send_file, jsonify, render_template, after_this_request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'temp_files'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_video():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in request'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file:
        unique_id = str(uuid.uuid4())
        input_filename = f"{unique_id}.webm"
        output_filename = f"{unique_id}.mp4"
        input_path = os.path.join(UPLOAD_FOLDER, input_filename)
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)

        try:
            file.save(input_path)

            command = [
                'ffmpeg',
                '-i', input_path,
                '-c:v', 'libx264',
                '-crf', '23',
                '-preset', 'veryfast',
                '-c:a', 'aac',
                '-movflags', 'faststart',
                output_path
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)

            @after_this_request
            def cleanup(response):
                try:
                    if os.path.exists(input_path):
                        os.remove(input_path)
                    if os.path.exists(output_path):
                        os.remove(output_path)
                except Exception as e:
                    print(f"Cleanup failed: {e}")
                return response

            return send_file(output_path, as_attachment=True, download_name="converted.mp4")

        except subprocess.CalledProcessError as e:
            print("FFmpeg Error:", e.stderr)
            return jsonify({'error': 'Conversion failed. See server logs.'}), 500
        except Exception as e:
            print("Error:", str(e))
            return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

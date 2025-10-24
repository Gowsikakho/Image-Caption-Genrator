from flask import Flask, render_template, request, jsonify
from flask_cors import CORS  # Import CORS
from generate_caption import generate_caption
import os
import uuid

app = Flask(__name__)

# Configure CORS to allow requests only from the origin 'http://127.0.0.1:5500'
CORS(app, resources={r"/generate_caption": {"origins": "http://127.0.0.1:5500"}})

# Configure the upload folder
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Folder to store uploaded images
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate_caption", methods=["POST"])
def generate():
    # Check if an image file was uploaded
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Generate a unique filename to prevent overwrites
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(file_path)

    # Generate caption using the saved file path
    caption = generate_caption(file_path)
    
    return jsonify({"caption": caption})

if __name__ == "__main__":
    app.run(debug=True)

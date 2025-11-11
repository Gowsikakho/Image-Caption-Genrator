from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from generate_caption import generate_caption
import os
import uuid

app = Flask(__name__)

# === CORS Configuration ===
# Allows your frontend (e.g., running on 127.0.0.1:5500 or Vite/React port) to access this API
CORS(app, resources={r"/generate_caption": {"origins": ["http://127.0.0.1:5500", "http://localhost:3000"]}})

# === Upload Folder Configuration ===
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route("/")
def index():
    """Serve the frontend HTML page."""
    return render_template("index.html")

@app.route("/generate_caption", methods=["POST"])
def generate():
    """Handles image upload and caption generation."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Generate a unique filename
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    
    # Save file locally
    file.save(file_path)

    # Generate caption
    caption = generate_caption(file_path)

    # Return caption JSON response
    return jsonify({
        "caption": caption,
        "image_url": f"/{file_path}"  # Optional — can be used in frontend previews
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

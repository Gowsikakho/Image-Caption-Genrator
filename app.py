from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from generate_caption import generate_caption
from config import Config
import os
import uuid
import logging

app = Flask(__name__)
app.config.from_object(Config)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === CORS Configuration ===
CORS(app, resources={r"/generate_caption": {"origins": app.config['CORS_ORIGINS']}})

# === Upload Folder Configuration ===
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route("/")
def index():
    """Serve the frontend HTML page."""
    return render_template("index.html")

@app.route("/generate_caption", methods=["POST"])
def generate():
    """Handles image upload and caption generation."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type. Only images are allowed."}), 400

        # Secure filename and generate unique name
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save file locally
        file.save(file_path)
        logger.info(f"File saved: {unique_filename}")

        # Generate caption
        caption = generate_caption(file_path)

        # Return caption JSON response
        return jsonify({
            "caption": caption,
            "image_url": f"/{file_path}"
        })
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({"error": "An error occurred while processing your request"}), 500

if __name__ == "__main__":
    app.run(debug=app.config['DEBUG'], host=app.config['HOST'], port=app.config['PORT'])

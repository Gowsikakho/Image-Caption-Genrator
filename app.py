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
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

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

@app.errorhandler(413)
def too_large(error):
    """Handle file too large error."""
    return jsonify({"error": "File too large. Maximum size is 16MB."}), 413

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
        if not filename:
            filename = "uploaded_image"
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save file locally
        file.save(file_path)
        logger.info("File saved: %s", unique_filename)

        # Generate caption
        caption = generate_caption(file_path)
        
        # Clean up uploaded file after processing
        try:
            os.remove(file_path)
            logger.info("File cleaned up: %s", unique_filename)
        except OSError as cleanup_error:
            logger.warning("Could not remove file %s: %s", unique_filename, cleanup_error)

        # Return caption JSON response
        return jsonify({
            "caption": caption
        })
    
    except Exception as error:
        logger.error("Error processing request: %s", str(error))
        return jsonify({"error": "An error occurred while processing your request"}), 500

if __name__ == "__main__":
    app.run(debug=app.config['DEBUG'], host=app.config['HOST'], port=app.config['PORT'])

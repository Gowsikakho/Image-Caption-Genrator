from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from generate_caption import CAPTION_MODELS, SUPPORTED_LANGUAGES, generate_caption
from config import Config
import os
import uuid
import logging
import traceback

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
    return render_template(
        "index.html",
        supported_languages=SUPPORTED_LANGUAGES,
        caption_models=CAPTION_MODELS,
    )

@app.errorhandler(413)
def too_large(error):
    """Handle file too large error."""
    return jsonify({"error": "File too large. Maximum size is 16MB."}), 413


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    """Handle unhandled exceptions and log full traceback."""
    logger.error("Unhandled exception: %s", error)
    logger.error(traceback.format_exc())

    if request.path == "/generate_caption":
        return jsonify({"error": "Unexpected server error while generating caption."}), 500

    return (
        "Unexpected server error. Please restart the server and try again.",
        500,
    )

@app.route("/generate_caption", methods=["POST"])
def generate():
    """Handles image upload and caption generation."""
    file_path = None
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

        language = request.form.get("language", "en").strip().lower()
        if language not in SUPPORTED_LANGUAGES:
            return jsonify({"error": "Unsupported language selected."}), 400

        model_quality = request.form.get("model_quality", "fast").strip().lower()
        if model_quality not in CAPTION_MODELS:
            return jsonify({"error": "Unsupported model quality selected."}), 400

        # Generate caption
        caption, error_message = generate_caption(
            file_path,
            language=language,
            model_quality=model_quality,
        )

        if error_message:
            return jsonify({"error": error_message}), 400

        # Return caption JSON response
        return jsonify({
            "caption": caption,
            "language": language,
            "model_quality": model_quality,
        })
    
    except Exception as error:
        logger.error("Error processing request: %s", str(error))
        logger.error(traceback.format_exc())
        return jsonify({"error": "An error occurred while processing your request"}), 500
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info("File cleaned up: %s", os.path.basename(file_path))
            except OSError as cleanup_error:
                logger.warning("Could not remove file %s: %s", file_path, cleanup_error)

if __name__ == "__main__":
    app.run(debug=app.config['DEBUG'], host=app.config['HOST'], port=app.config['PORT'])

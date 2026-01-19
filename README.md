# Image Caption Generator

An AI-powered web application that generates descriptive captions for uploaded images using the BLIP (Bootstrapping Language-Image Pre-training) model from Salesforce.

## Features

- **AI-Powered Captions**: Uses Salesforce's BLIP model for accurate image captioning
- **Drag & Drop Interface**: Intuitive file upload with drag-and-drop support
- **Caption History**: Keeps track of previously generated captions
- **File Validation**: Supports multiple image formats with size limits
- **Responsive Design**: Modern, elegant UI with golden theme
- **Security**: Path traversal protection and secure file handling
- **Error Handling**: Comprehensive error handling and user feedback

## Project Structure

```
Image-Caption-Generator/
├── app.py                    # Main Flask application
├── config.py                 # Configuration settings
├── generate_caption.py       # AI caption generation logic
├── run.py                    # Application startup script
├── test_app.py              # Unit tests
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
├── .eslintrc.json           # ESLint configuration
├── static/                  # Static assets
│   ├── uploads/             # Temporary file uploads
│   ├── background.jpg       # Background image
│   ├── IMAGE-CAPTION-GENERATOR.jpg
│   ├── script.js            # Frontend JavaScript
│   └── styles.css           # CSS styling
└── templates/
    └── index.html           # Main HTML template
```

## Technology Stack

### Backend
- **Flask**: Web framework
- **Transformers**: Hugging Face library for BLIP model
- **PIL (Pillow)**: Image processing
- **Flask-CORS**: Cross-origin resource sharing

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with animations
- **JavaScript (ES6+)**: Interactive functionality
- **Font Awesome**: Icons

### AI Model
- **BLIP**: Salesforce's image captioning model
- **Model**: `Salesforce/blip-image-captioning-base`

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Image-Caption-Generator
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install flask flask-cors transformers torch pillow
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings
   ```

## Configuration

The application can be configured through environment variables or the `config.py` file:

- **FLASK_DEBUG**: Enable/disable debug mode (default: false)
- **FLASK_HOST**: Server host (default: 127.0.0.1)
- **FLASK_PORT**: Server port (default: 5000)
- **SECRET_KEY**: Flask secret key for sessions
- **CORS_ORIGINS**: Allowed CORS origins
- **MAX_CONTENT_LENGTH**: Maximum file upload size (16MB)

## Usage

### Running the Application

**Option 1: Using the startup script**
```bash
python run.py
```

**Option 2: Direct Flask execution**
```bash
python app.py
```

**Option 3: Flask CLI**
```bash
flask run
```

### Using the Web Interface

1. Open your browser and navigate to `http://127.0.0.1:5000`
2. Upload an image by:
   - Clicking the upload zone and selecting a file
   - Dragging and dropping an image onto the upload zone
3. Click "Generate Caption" to process the image
4. View the generated caption and access history via the clock icon

### Supported Image Formats

- PNG (.png)
- JPEG (.jpg, .jpeg)
- GIF (.gif)
- WebP (.webp)

### File Size Limits

- Maximum file size: 16MB
- Files are automatically cleaned up after processing

## API Endpoints

### GET /
Returns the main HTML interface.

### POST /generate_caption
Generates a caption for an uploaded image.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: Image file in 'file' field

**Response:**
```json
{
  "caption": "Generated caption text"
}
```

**Error Response:**
```json
{
  "error": "Error message"
}
```

## Testing

Run the unit tests:
```bash
python -m unittest test_app.py
```

The test suite includes:
- Route testing
- File upload validation
- Configuration validation
- Error handling

## Security Features

- **Secure filename handling**: Uses Werkzeug's secure_filename
- **Path traversal protection**: Validates file paths
- **File type validation**: Only allows image files
- **File size limits**: Prevents large file uploads
- **Temporary file cleanup**: Removes uploaded files after processing

## Development

### Code Structure

- **app.py**: Main Flask application with routes and error handling
- **generate_caption.py**: AI model integration and caption generation
- **config.py**: Centralized configuration management
- **static/script.js**: Frontend interactivity and AJAX calls
- **templates/index.html**: HTML template with modern UI

### Adding Features

1. Model improvements: Modify `generate_caption.py`
2. UI enhancements: Update `static/` files
3. API extensions: Add routes to `app.py`
4. Configuration: Update `config.py`

## Troubleshooting

### Common Issues

1. **Model loading errors**: Ensure internet connection for first-time model download
2. **File upload failures**: Check file size and format restrictions
3. **CORS errors**: Verify CORS_ORIGINS configuration
4. **Memory issues**: Monitor system resources during model loading

### Logs

The application uses Python's logging module. Check console output for detailed error information.

## License

This project is open source. Please check the license file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Acknowledgments

- Salesforce for the BLIP model
- Hugging Face for the Transformers library
- Flask community for the web framework
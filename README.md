# AI Image Caption Generator

A web application that generates descriptive captions for uploaded images using the BLIP (Bootstrapping Language-Image Pre-training) model.

## Features

- Drag & drop image upload interface
- AI-powered caption generation using Salesforce BLIP model
- Caption history tracking
- Responsive golden-themed UI
- Support for common image formats (JPEG, PNG, GIF)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Image-Caption-Generator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to `http://localhost:5000`

## Usage

1. Upload an image by clicking the upload zone or dragging an image file
2. Click "Generate Caption" to create an AI-generated description
3. View your caption history by clicking the clock icon
4. Generate new captions for different images

## Technology Stack

- **Backend**: Flask, Python
- **AI Model**: Salesforce BLIP Image Captioning
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Image Processing**: PIL (Python Imaging Library)

## License

MIT License
# API Documentation

## Endpoints

### POST /generate_caption

Generates a caption for an uploaded image.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: Form data with 'file' field containing image

**Response:**
```json
{
  "caption": "A description of the image",
  "image_url": "/static/uploads/filename.jpg"
}
```

**Error Response:**
```json
{
  "error": "Error message"
}
```

**Status Codes:**
- 200: Success
- 400: Bad request (no file, invalid file)
- 500: Server error

### GET /

Serves the main application interface.

**Response:**
- HTML page with the image caption generator interface

## File Upload Requirements

- **Supported formats**: PNG, JPEG, GIF, WebP
- **Maximum file size**: 16MB
- **File validation**: Server-side validation for file type and size
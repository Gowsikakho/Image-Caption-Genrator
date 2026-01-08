from PIL import Image, UnidentifiedImageError
from transformers import BlipProcessor, BlipForConditionalGeneration
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Load the model and processor (public access, no token needed)
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

def generate_caption(image_path):
    """Generates a caption for the given image."""
    try:
        # Validate file exists and is within allowed directory
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return "Image file not found."
        
        # Basic path traversal protection
        if '..' in image_path or not os.path.abspath(image_path).startswith(os.path.abspath('static/uploads')):
            logger.error(f"Invalid file path detected: {image_path}")
            return "Invalid file path."
        
        with Image.open(image_path) as image:
            inputs = processor(images=image, return_tensors="pt")
            output = model.generate(**inputs)
            caption = processor.decode(output[0], skip_special_tokens=True)
        
        logger.info(f"Caption generated for {image_path}")
        return caption

    except UnidentifiedImageError:
        logger.error(f"Invalid image file: {image_path}")
        return "Invalid image file. Please upload a valid image."

    except Exception as e:
        logger.error(f"Error generating caption: {e}")
        return "An error occurred while generating the caption."

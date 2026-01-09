"""Image caption generation module using BLIP model."""

import logging
import os

from PIL import Image, UnidentifiedImageError
from transformers import BlipProcessor, BlipForConditionalGeneration

# Configure logging
logger = logging.getLogger(__name__)

# Load the model and processor (public access, no token needed)
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

def generate_caption(image_path):
    """Generates a caption for the given image.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        str: Generated caption or error message
    """
    try:
        # Validate file exists and is within allowed directory
        if not os.path.exists(image_path):
            logger.error("Image file not found: %s", image_path)
            return "Image file not found."
        
        # Basic path traversal protection
        abs_image_path = os.path.abspath(image_path)
        abs_upload_dir = os.path.abspath('static/uploads')
        
        if '..' in image_path or not abs_image_path.startswith(abs_upload_dir):
            logger.error("Invalid file path detected: %s", image_path)
            return "Invalid file path."
        
        with Image.open(image_path) as image:
            inputs = processor(images=image, return_tensors="pt")
            output = model.generate(**inputs)
            caption = processor.decode(output[0], skip_special_tokens=True)
        
        logger.info("Caption generated for %s", image_path)
        return caption

    except UnidentifiedImageError:
        logger.error("Invalid image file: %s", image_path)
        return "Invalid image file. Please upload a valid image."

    except OSError as os_error:
        logger.error("File system error: %s", os_error)
        return "Error accessing the image file."
        
    except Exception as error:  # pylint: disable=broad-except
        logger.error("Error generating caption: %s", error)
        return "An error occurred while generating the caption."

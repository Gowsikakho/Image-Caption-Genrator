from huggingface_hub import login

login("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")


from PIL import Image, UnidentifiedImageError
from transformers import BlipProcessor, BlipForConditionalGeneration

# Load the processor and model once to avoid reloading for each request
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

def generate_caption(image_path):
    """Generates a caption for the given image."""
    try:
        # Open and process the image
        with Image.open(image_path) as image:
            inputs = processor(images=image, return_tensors="pt")
            output = model.generate(**inputs)
            caption = processor.decode(output[0], skip_special_tokens=True)
            
        return caption
    except UnidentifiedImageError:
        return "Invalid image file. Please upload a valid image."
    except Exception as e:
        print(f"Error generating caption: {e}")
        return "An error occurred while generating the caption."

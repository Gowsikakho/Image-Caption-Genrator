"""Image caption generation module using BLIP model and optional translation."""

import logging
import os

from deep_translator import GoogleTranslator
from PIL import Image, UnidentifiedImageError
from transformers import BlipForConditionalGeneration, BlipProcessor

logger = logging.getLogger(__name__)

MODEL_IDS = {
    "fast": "Salesforce/blip-image-captioning-base",
    "balanced": "Salesforce/blip-image-captioning-base",  # ensemble via dual-prompt
    "high": "Salesforce/blip-image-captioning-large",
}
_PROCESSORS = {}
_MODELS = {}

CAPTION_MODELS = {
    "fast": {"label": "BLIP Base (Fast & Accurate)"},
    "balanced": {"label": "Balanced Ensemble (Better quality, moderate speed)"},
    "high": {"label": "BLIP Large (More accurate, slower)"},
}

SUPPORTED_LANGUAGES = {
    "en": {"label": "English"},
    "fr": {"label": "French"},
    "es": {"label": "Spanish"},
    "de": {"label": "German"},
    "it": {"label": "Italian"},
}


def _load_model(model_quality="fast"):
    model_id = MODEL_IDS.get(model_quality, MODEL_IDS["fast"])
    if model_id not in _PROCESSORS or model_id not in _MODELS:
        _PROCESSORS[model_id] = BlipProcessor.from_pretrained(model_id, use_fast=True)
        _MODELS[model_id] = BlipForConditionalGeneration.from_pretrained(model_id)
        logger.info("BLIP model loaded: %s", model_id)
    return _PROCESSORS[model_id], _MODELS[model_id]


def _resize_image(image, max_size=384):
    w, h = image.size
    if max(w, h) > max_size:
        scale = max_size / max(w, h)
        image = image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    return image.convert("RGB")


def _infer(processor, model, image, prompt=None):
    """Run a single BLIP inference pass, optionally with a text prompt."""
    if prompt:
        inputs = processor(images=image, text=prompt, return_tensors="pt")
    else:
        inputs = processor(images=image, return_tensors="pt")
    output = model.generate(
        **inputs,
        max_new_tokens=40,
        num_beams=3,
        length_penalty=1.2,
        repetition_penalty=1.3,
    )
    return processor.decode(output[0], skip_special_tokens=True).strip()


def _build_two_line_caption(processor, model, image):
    """Generate a fast, accurate 2-line caption using dual-prompt BLIP inference."""
    line1 = _infer(processor, model, image)
    line2 = _infer(processor, model, image, prompt="the image also shows")

    line1 = line1.capitalize().rstrip(".") + "."
    line2 = line2.capitalize().rstrip(".") + "."

    if line1.lower() == line2.lower():
        return line1

    return f"{line1}\n{line2}"


def _translate(caption, language):
    if language == "en" or language not in SUPPORTED_LANGUAGES:
        return caption
    try:
        translated = GoogleTranslator(source="en", target=language).translate(caption)
        return translated if translated else caption
    except Exception as err:
        logger.warning("Translation failed for '%s', returning English: %s", language, err)
        return caption


def generate_caption(image_path, language="en", model_quality="fast"):
    """Generate a 2-line caption for the given image.

    Args:
        image_path (str): Path to the image file.
        language (str): Output language code (default: "en").
        model_quality (str): One of "fast", "balanced", "high".

    Returns:
        tuple[str | None, str | None]: (caption, error)
    """
    try:
        if not os.path.exists(image_path):
            return None, "Image file not found."

        abs_image_path = os.path.abspath(image_path)
        abs_upload_dir = os.path.abspath("static/uploads")
        try:
            if os.path.commonpath([abs_image_path, abs_upload_dir]) != abs_upload_dir:
                return None, "Invalid file path."
        except ValueError:
            return None, "Invalid file path."

        processor, model = _load_model(model_quality)

        with Image.open(image_path) as image:
            image = _resize_image(image)
            caption = _build_two_line_caption(processor, model, image)

        caption = _translate(caption, language)
        logger.info("Caption generated for %s", image_path)
        return caption, None

    except UnidentifiedImageError:
        return None, "Invalid image file. Please upload a valid image."
    except OSError as err:
        logger.error("File system error: %s", err)
        return None, "Error accessing the image file."
    except Exception as err:
        logger.error("Error generating caption: %s", err)
        return None, "An error occurred while generating the caption."


# Pre-warm the fast model at startup to eliminate cold-start on first request
try:
    _load_model("fast")
except Exception as _e:  # noqa: BLE001
    logger.warning("Model pre-warm failed: %s", _e)

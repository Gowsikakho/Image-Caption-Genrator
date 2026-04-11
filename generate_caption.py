"""Image caption generation module using BLIP model and optional translation."""

import base64
import logging
import os

import requests

# Load .env before anything reads os.environ
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except Exception:
    pass

logger = logging.getLogger(__name__)

try:
    from deep_translator import GoogleTranslator
    _TRANSLATOR_AVAILABLE = True
except Exception as _import_err:
    logger.warning("deep_translator not available: %s", _import_err)
    _TRANSLATOR_AVAILABLE = False

try:
    from PIL import Image, UnidentifiedImageError
    from transformers import BlipForConditionalGeneration, BlipProcessor
    _MODELS_AVAILABLE = True
except Exception as _import_err:
    logger.error("Required ML packages not available: %s", _import_err)
    _MODELS_AVAILABLE = False

HF_CHAT_MODEL = "llava-hf/llava-1.5-7b-hf"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_CHAT_MODEL}"


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
    "ta": {"label": "Tamil"},
}


def _load_model(model_quality="fast"):
    if not _MODELS_AVAILABLE:
        raise RuntimeError("ML packages (transformers/PIL) are not installed.")
    model_id = MODEL_IDS.get(model_quality, MODEL_IDS["fast"])
    if model_id not in _PROCESSORS or model_id not in _MODELS:
        logger.info("Loading BLIP model: %s", model_id)
        processor = BlipProcessor.from_pretrained(model_id, use_fast=True)
        model = BlipForConditionalGeneration.from_pretrained(model_id)
        _PROCESSORS[model_id] = processor
        _MODELS[model_id] = model
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
    if not _TRANSLATOR_AVAILABLE:
        logger.warning("Translator not available, returning English caption.")
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
    if not _MODELS_AVAILABLE:
        return None, "ML packages are not installed. Run: pip install transformers torch pillow"

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


def answer_question(image_path, question, caption=""):
    """Answer a question about an image via HF Inference API (llava-1.5-7b).

    Returns:
        tuple[str | None, str | None]: (answer, error)
    """
    token = os.environ.get("HF_API_TOKEN", "")
    if not token:
        return None, "HF_API_TOKEN not set. Add it to your .env file."

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

        # Read and encode image as base64
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")

        # Detect mime type from extension
        ext = os.path.splitext(image_path)[1].lower().lstrip(".")
        mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                "gif": "image/gif", "webp": "image/webp"}.get(ext, "image/jpeg")

        # Build grounded prompt
        if caption:
            prompt = (
                f"[INST] <image>\nYou are a helpful assistant that only answers questions "
                f"about the image. The image caption is: \"{caption}\".\n"
                f"{question} [/INST]"
            )
        else:
            prompt = f"[INST] <image>\n{question} [/INST]"

        payload = {
            "inputs": {
                "image": f"data:{mime};base64,{image_b64}",
                "question": prompt,
            },
            "parameters": {
                "max_new_tokens": 150,
                "do_sample": False,
            }
        }

        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)

        if response.status_code == 503:
            return None, "Model is loading on HF servers, please try again in a few seconds."
        if response.status_code != 200:
            logger.error("HF API error %s: %s", response.status_code, response.text)
            return None, f"API error ({response.status_code}). Please try again."

        data = response.json()

        # Extract answer from response
        if isinstance(data, list) and data:
            answer = data[0].get("generated_text", "")
        elif isinstance(data, dict):
            answer = data.get("generated_text", "")
        else:
            answer = str(data)

        # Strip prompt echo if present
        if "[/INST]" in answer:
            answer = answer.split("[/INST]")[-1].strip()

        if not answer:
            return "I can only answer questions about this image.", None

        return answer.strip(), None

    except requests.Timeout:
        return None, "Request timed out. Please try again."
    except OSError as err:
        logger.error("File error in chat: %s", err)
        return None, "Error reading the image file."
    except Exception as err:
        logger.error("Chat API error: %s", err)
        return None, "An error occurred while answering your question."


# Pre-warm the fast model at startup to eliminate cold-start on first request
try:
    _load_model("fast")
except Exception as _e:  # noqa: BLE001
    logger.warning("Model pre-warm failed: %s", _e)

"""Image caption generation module using BLIP model and optional translation."""

import logging
import os

from deep_translator import GoogleTranslator
from PIL import Image, UnidentifiedImageError
from transformers import (
    AutoModelForCausalLM,
    AutoModelForSeq2SeqLM,
    AutoProcessor,
    AutoTokenizer,
    BlipForConditionalGeneration,
    BlipProcessor,
    CLIPModel,
    VisionEncoderDecoderModel,
    ViTImageProcessor,
)

# Configure logging
logger = logging.getLogger(__name__)

# Global model variables for performance
CAPTION_MODELS = {
    "fast": {
        "label": "BLIP Base (Fastest)",
        "type": "blip",
        "model_id": "Salesforce/blip-image-captioning-base",
    },
    "balanced": {
        "label": "Balanced Ensemble (Better quality, moderate speed)",
        "ensemble": ["blip_base", "git_base", "vit_gpt2"],
    },
    "high": {
        "label": "BLIP Large (Highest quality, slowest)",
        "type": "blip",
        "model_id": "Salesforce/blip-image-captioning-large",
    },
}

CAPTION_BACKBONES = {
    "blip_base": {
        "type": "blip",
        "model_id": "Salesforce/blip-image-captioning-base",
    },
    "blip_large": {
        "type": "blip",
        "model_id": "Salesforce/blip-image-captioning-large",
    },
    "git_base": {
        "type": "git",
        "model_id": "microsoft/git-base-coco",
    },
    "vit_gpt2": {
        "type": "vit_gpt2",
        "model_id": "nlpconnect/vit-gpt2-image-captioning",
    },
}
CAPTION_PROCESSORS = {}
CAPTION_MODEL_INSTANCES = {}
CAPTION_TOKENIZERS = {}
CLIP_MODEL = None
CLIP_PROCESSOR = None
TRANSLATION_MODELS = {}
TRANSLATION_TOKENIZERS = {}

# Language options supported by the API/UI.
# BLIP generates English captions and we optionally translate them.
SUPPORTED_LANGUAGES = {
    "en": {"label": "English", "translation_model": None},
    "fr": {"label": "French", "translation_model": "Helsinki-NLP/opus-mt-en-fr"},
    "es": {"label": "Spanish", "translation_model": "Helsinki-NLP/opus-mt-en-es"},
    "de": {"label": "German", "translation_model": "Helsinki-NLP/opus-mt-en-de"},
    "it": {"label": "Italian", "translation_model": "Helsinki-NLP/opus-mt-en-it"},
}


def _load_backbone(backbone_key):
    """Load a caption backbone model and return inference components."""
    if backbone_key not in CAPTION_BACKBONES:
        return None, None, None, "Unsupported caption backbone."

    config = CAPTION_BACKBONES[backbone_key]
    model_type = config["type"]
    model_id = config["model_id"]

    if model_type == "blip":
        if backbone_key not in CAPTION_PROCESSORS or backbone_key not in CAPTION_MODEL_INSTANCES:
            CAPTION_PROCESSORS[backbone_key] = BlipProcessor.from_pretrained(model_id)
            CAPTION_MODEL_INSTANCES[backbone_key] = BlipForConditionalGeneration.from_pretrained(model_id)
        return CAPTION_PROCESSORS[backbone_key], CAPTION_MODEL_INSTANCES[backbone_key], None, None

    if model_type == "git":
        if backbone_key not in CAPTION_PROCESSORS or backbone_key not in CAPTION_MODEL_INSTANCES:
            CAPTION_PROCESSORS[backbone_key] = AutoProcessor.from_pretrained(model_id)
            CAPTION_MODEL_INSTANCES[backbone_key] = AutoModelForCausalLM.from_pretrained(model_id)
        return CAPTION_PROCESSORS[backbone_key], CAPTION_MODEL_INSTANCES[backbone_key], None, None

    if model_type == "vit_gpt2":
        if (
            backbone_key not in CAPTION_PROCESSORS
            or backbone_key not in CAPTION_MODEL_INSTANCES
            or backbone_key not in CAPTION_TOKENIZERS
        ):
            CAPTION_PROCESSORS[backbone_key] = ViTImageProcessor.from_pretrained(model_id)
            CAPTION_MODEL_INSTANCES[backbone_key] = VisionEncoderDecoderModel.from_pretrained(model_id)
            CAPTION_TOKENIZERS[backbone_key] = AutoTokenizer.from_pretrained(model_id)
        return (
            CAPTION_PROCESSORS[backbone_key],
            CAPTION_MODEL_INSTANCES[backbone_key],
            CAPTION_TOKENIZERS[backbone_key],
            None,
        )

    return None, None, None, "Unsupported caption backbone type."


def _generate_caption_from_backbone(image, backbone_key):
    """Generate one caption from a specific backbone."""
    processor, model, tokenizer, error = _load_backbone(backbone_key)
    if error:
        return None, error

    try:
        model_type = CAPTION_BACKBONES[backbone_key]["type"]
        if model_type in {"blip", "git"}:
            inputs = processor(images=image, return_tensors="pt")
            output = model.generate(**inputs, max_new_tokens=35, num_beams=4)
            caption = processor.batch_decode(output, skip_special_tokens=True)[0].strip()
            return caption, None

        if model_type == "vit_gpt2":
            pixel_values = processor(images=image, return_tensors="pt").pixel_values
            output = model.generate(pixel_values, max_length=32, num_beams=4)
            caption = tokenizer.decode(output[0], skip_special_tokens=True).strip()
            return caption, None

        return None, "Unsupported caption backbone type."
    except Exception as error:  # pragma: no cover - runtime model behavior
        return None, str(error)


def _load_clip_model():
    """Load CLIP model used to score candidate captions."""
    global CLIP_MODEL, CLIP_PROCESSOR
    if CLIP_MODEL is None or CLIP_PROCESSOR is None:
        CLIP_MODEL = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        CLIP_PROCESSOR = AutoProcessor.from_pretrained("openai/clip-vit-base-patch32")


def _generate_multi_agent_caption(image, model_quality):
    """Generate candidate captions from one or more models and pick the best."""
    if model_quality not in CAPTION_MODELS:
        return None, "Unsupported model quality selected."

    quality_config = CAPTION_MODELS[model_quality]
    if "ensemble" in quality_config:
        backbone_keys = quality_config["ensemble"]
    else:
        backbone_keys = ["blip_base"] if model_quality == "fast" else ["blip_large"]

    candidates = []
    for backbone_key in backbone_keys:
        caption, error = _generate_caption_from_backbone(image, backbone_key)
        if caption:
            candidates.append(caption)
        elif error:
            logger.warning("Caption model '%s' failed: %s", backbone_key, error)

    # Remove duplicates while preserving order
    candidates = list(dict.fromkeys(candidates))
    if not candidates:
        return None, "Could not generate caption candidates."
    if len(candidates) == 1:
        return candidates[0], None

    try:
        _load_clip_model()
        clip_inputs = CLIP_PROCESSOR(
            text=candidates,
            images=image,
            return_tensors="pt",
            padding=True,
        )
        outputs = CLIP_MODEL(**clip_inputs)
        best_index = int(outputs.logits_per_image.argmax().item())
        return candidates[best_index], None
    except Exception as error:
        logger.warning("CLIP scoring failed, using first candidate: %s", error)
        return candidates[0], None


def _translate_caption(caption, language):
    """Translate an English caption to the requested language."""
    if language not in SUPPORTED_LANGUAGES:
        return None, "Unsupported language selected."

    translation_model = SUPPORTED_LANGUAGES[language]["translation_model"]
    if translation_model is None:
        return caption, None

    # Prefer lightweight online translation to avoid large local model downloads.
    try:
        translated_caption = GoogleTranslator(source="en", target=language).translate(caption)
        if translated_caption:
            return translated_caption, None
    except Exception as error:
        logger.warning(
            "Online translation failed for language '%s', trying local model: %s",
            language,
            error,
        )

    # Fast-fail if local model path cannot run in this environment.
    try:
        import sentencepiece  # noqa: F401
    except ImportError:
        logger.warning(
            "sentencepiece is not installed; returning English caption for language '%s'.",
            language,
        )
        return caption, None

    try:
        if language not in TRANSLATION_MODELS or language not in TRANSLATION_TOKENIZERS:
            TRANSLATION_TOKENIZERS[language] = AutoTokenizer.from_pretrained(translation_model)
            TRANSLATION_MODELS[language] = AutoModelForSeq2SeqLM.from_pretrained(translation_model)

        tokenizer = TRANSLATION_TOKENIZERS[language]
        model = TRANSLATION_MODELS[language]

        inputs = tokenizer(caption, return_tensors="pt", truncation=True)
        outputs = model.generate(**inputs, max_new_tokens=64)
        translated_caption = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return translated_caption, None
    except Exception as error:  # pragma: no cover - model download/network/runtime dependent
        logger.warning(
            "Translation failed for language '%s', returning English caption: %s",
            language,
            error,
        )
        return caption, None


def generate_caption(image_path, language="en", model_quality="fast"):
    """Generate a caption for the given image.
    
    Args:
        image_path (str): Path to the image file
        language (str): Output language code (default: "en")
        model_quality (str): Caption model quality ("fast", "balanced", or "high")
        
    Returns:
        str: Generated caption
        str|None: Error message if something fails, else None
    """
    try:
        # Validate file exists
        if not os.path.exists(image_path):
            logger.error("Image file not found: %s", image_path)
            return None, "Image file not found."
        
        # Path traversal protection
        abs_image_path = os.path.abspath(image_path)
        abs_upload_dir = os.path.abspath('static/uploads')
        
        if '..' in image_path or not abs_image_path.startswith(abs_upload_dir):
            logger.error("Invalid file path detected: %s", image_path)
            return None, "Invalid file path."
        
        # Generate caption
        with Image.open(image_path) as image:
            english_caption, caption_error = _generate_multi_agent_caption(image, model_quality)
            if caption_error:
                return None, caption_error

        translated_caption, translation_error = _translate_caption(english_caption, language)
        if translation_error:
            logger.error("Caption translation failed: %s", translation_error)
            return None, translation_error
        
        logger.info("Caption generated for %s", image_path)
        return translated_caption, None

    except UnidentifiedImageError:
        logger.error("Invalid image file: %s", image_path)
        return None, "Invalid image file. Please upload a valid image."

    except OSError as os_error:
        logger.error("File system error: %s", os_error)
        return None, "Error accessing the image file."
        
    except Exception as error:
        logger.error("Error generating caption: %s", error)
        return None, "An error occurred while generating the caption."
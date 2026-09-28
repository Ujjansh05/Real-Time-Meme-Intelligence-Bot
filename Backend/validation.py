"""Validate and normalize user input before it reaches a model."""

from io import BytesIO
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError


MAX_TEXT_CHARS = 4000
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
ALLOWED_LANGUAGES = {"english", "hindi", "hinglish", "en", "hi"}
ALLOWED_TONES = {"general", "student", "work", "gaming", "wholesome"}


class InputError(ValueError):
    pass


def validate_text(value: object, *, required: bool = False) -> str:
    if not isinstance(value, str):
        raise InputError("Text must be a string.")
    result = value.strip()
    if len(result) > MAX_TEXT_CHARS:
        raise InputError(f"Text must be at most {MAX_TEXT_CHARS} characters.")
    if required and not result:
        raise InputError("Text or an image is required.")
    return result


def validate_option(value: object, allowed: set[str], label: str, default: str) -> str:
    if value is None or value == "":
        return default
    if not isinstance(value, str) or value.lower() not in allowed:
        raise InputError(f"Unsupported {label}.")
    return value.lower()


def normalize_image(data: bytes) -> bytes:
    if not data or len(data) > MAX_UPLOAD_BYTES:
        raise InputError("Image must be between 1 byte and 5 MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as image:
                if image.format not in {"PNG", "JPEG", "WEBP"}:
                    raise InputError("Use a PNG, JPEG, or WebP image.")
                if image.width * image.height > MAX_IMAGE_PIXELS:
                    raise InputError("Image has too many pixels.")
                image = ImageOps.exif_transpose(image)
                image.thumbnail((1024, 1024))
                rgb = image.convert("RGB")
                output = BytesIO()
                rgb.save(output, format="JPEG", quality=85, optimize=True)
                return output.getvalue()
    except InputError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise InputError("Invalid or damaged image.") from exc

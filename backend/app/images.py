"""Validação e armazenamento seguro de fotos (remove EXIF/GPS ao reencodar)."""
import io
import os
import uuid

from PIL import Image, UnidentifiedImageError

ALLOWED = {"JPEG", "PNG", "WEBP"}
MEDIA = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}


class InvalidImage(ValueError):
    pass


def read_image(data: bytes):
    """Valida os bytes e devolve (formato, media_type)."""
    try:
        img = Image.open(io.BytesIO(data))
        img.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise InvalidImage("O arquivo não é uma imagem válida.") from exc
    if img.format not in ALLOWED:
        raise InvalidImage("Use uma foto JPEG, PNG ou WEBP.")
    return img.format, MEDIA[img.format]


def save_photo(data: bytes, upload_dir: str) -> str:
    read_image(data)
    img = Image.open(io.BytesIO(data)).convert("RGB")
    img.thumbnail((1280, 1280))
    name = f"{uuid.uuid4().hex}.jpg"
    img.save(os.path.join(upload_dir, name), "JPEG", quality=85)  # sem EXIF
    return name

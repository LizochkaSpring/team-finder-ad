import hashlib
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont


def build_letter_avatar(letter: str) -> ContentFile:
    """Создаёт PNG-аватар с первой буквой имени на мягком фоне."""
    ch = (letter or "?")[:1].upper()
    size = 200
    h = hashlib.md5(ch.encode("utf-8"), usedforsecurity=False).hexdigest()
    r = 80 + int(h[0:2], 16) % 100
    g = 80 + int(h[2:4], 16) % 100
    b = 80 + int(h[4:6], 16) % 100
    image = Image.new("RGB", (size, size), color=(r, g, b))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 100)
    except OSError:
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", 100)
        except OSError:
            font = ImageFont.load_default()
    if hasattr(font, "getbbox"):
        x0, y0, x1, y1 = font.getbbox(ch)
        tw, th = x1 - x0, y1 - y0
    else:
        tw, th = font.getsize(ch)
    draw.text(
        ((size - tw) / 2, (size - th) / 2 - 6),
        ch,
        fill=(255, 255, 255),
        font=font,
    )
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return ContentFile(buffer.read(), name=f"avatar_{ch}.png")

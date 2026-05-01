import hashlib
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont

from users.constants import (
    AVATAR_BG_CHANNEL_BASE,
    AVATAR_BG_CHANNEL_RANGE,
    AVATAR_FALLBACK_FONT,
    AVATAR_FONT_SIZE_PX,
    AVATAR_PRIMARY_FONT,
    AVATAR_SIZE_PX,
    AVATAR_TEXT_COLOR,
    AVATAR_TEXT_VERTICAL_OFFSET_PX,
)


def _load_font():
    """Пробует основной шрифт, при отсутствии — запасной, иначе встроенный."""
    for font_name in (AVATAR_PRIMARY_FONT, AVATAR_FALLBACK_FONT):
        try:
            return ImageFont.truetype(font_name, AVATAR_FONT_SIZE_PX)
        except OSError:
            continue
    return ImageFont.load_default()


def build_letter_avatar(letter: str) -> ContentFile:
    """Создаёт PNG-аватар с первой буквой имени на мягком фоне."""
    char = (letter or "?")[:1].upper()
    digest = hashlib.md5(char.encode("utf-8"), usedforsecurity=False).hexdigest()
    red = AVATAR_BG_CHANNEL_BASE + int(digest[0:2], 16) % AVATAR_BG_CHANNEL_RANGE
    green = AVATAR_BG_CHANNEL_BASE + int(digest[2:4], 16) % AVATAR_BG_CHANNEL_RANGE
    blue = AVATAR_BG_CHANNEL_BASE + int(digest[4:6], 16) % AVATAR_BG_CHANNEL_RANGE

    image = Image.new("RGB", (AVATAR_SIZE_PX, AVATAR_SIZE_PX), color=(red, green, blue))
    draw = ImageDraw.Draw(image)
    font = _load_font()

    if hasattr(font, "getbbox"):
        x0, y0, x1, y1 = font.getbbox(char)
        text_width, text_height = x1 - x0, y1 - y0
    else:
        text_width, text_height = font.getsize(char)

    draw.text(
        (
            (AVATAR_SIZE_PX - text_width) / 2,
            (AVATAR_SIZE_PX - text_height) / 2 - AVATAR_TEXT_VERTICAL_OFFSET_PX,
        ),
        char,
        fill=AVATAR_TEXT_COLOR,
        font=font,
    )

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return ContentFile(buffer.read(), name=f"avatar_{char}.png")

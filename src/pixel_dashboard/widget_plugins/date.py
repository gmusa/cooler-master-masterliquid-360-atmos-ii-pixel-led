"""Date widget."""
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont


class Date:
    def render(self, data, now, palette=None):
        image = Image.new('RGB', (32, 32))
        draw = ImageDraw.Draw(image)
        text = datetime.fromtimestamp(now).strftime('%d/%m')
        font = ImageFont.load_default(size=9)
        box = draw.textbbox((0, 0), text, font=font)
        draw.text(((32 - (box[2] - box[0])) // 2 - box[0], 11), text,
                  font=font, fill=palette['on_surface'] if palette else 'white')
        return image

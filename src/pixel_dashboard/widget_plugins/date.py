"""Date widget."""
from datetime import datetime

from PIL import Image, ImageDraw


class Date:
    def render(self, data, now, palette=None):
        image = Image.new('RGB', (32, 32))
        ImageDraw.Draw(image).text((1, 11), datetime.fromtimestamp(now).strftime('%d/%m'), fill=palette['on_surface'] if palette else 'white')
        return image

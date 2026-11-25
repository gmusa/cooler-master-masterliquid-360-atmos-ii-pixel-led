"""Digital clock widget."""
from datetime import datetime

from PIL import Image, ImageDraw


class Clock:
    def render(self, data, now):
        image = Image.new('RGB', (32, 32))
        ImageDraw.Draw(image).text((1, 11), datetime.fromtimestamp(now).strftime('%H:%M'), fill='white')
        return image

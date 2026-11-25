"""Date widget."""
from datetime import datetime

from PIL import Image, ImageDraw


class Date:
    def render(self, data, now):
        image = Image.new('RGB', (32, 32))
        ImageDraw.Draw(image).text((1, 11), datetime.fromtimestamp(now).strftime('%d/%m'), fill='white')
        return image

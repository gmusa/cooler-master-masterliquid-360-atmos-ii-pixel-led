"""Moving dot animation widget."""
from PIL import Image, ImageDraw


class Animation:
    def render(self, data, now, palette=None):
        image = Image.new('RGB', (32, 32))
        draw = ImageDraw.Draw(image)
        x = int(now * 8) % 32
        draw.ellipse((x, 12, min(31, x + 4), 16), fill=palette['secondary'] if palette else 'green')
        return image

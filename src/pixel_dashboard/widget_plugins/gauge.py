"""Shared sensor gauge rendering."""
from PIL import Image, ImageDraw, ImageFont


class Gauge:
    color = 'orange'
    label = ''

    def render(self, data, now, palette=None):
        image = Image.new('RGB', (32, 32))
        draw = ImageDraw.Draw(image)
        temperature = data.get('temperature')
        usage = data.get('usage')
        text_color = palette['on_surface'] if palette else 'white'
        font = ImageFont.load_default(size=6)
        for y, text in ((6, self.label),
                        (12, f'{round(temperature)}C' if temperature is not None else '--'),
                        (18, f'{round(usage)}%' if usage is not None else '--')):
            box = draw.textbbox((0, 0), text, font=font)
            draw.text(((32 - (box[2] - box[0])) // 2 - box[0], y), text,
                      font=font, fill=text_color)
        # Prefer actual utilization; otherwise display the available temperature
        # as a 0–100 scale. Empty outline means neither measurement is present.
        value = usage if usage is not None else temperature
        bar_color = palette['primary'] if palette else self.color
        draw.line((10, 24, 21, 24), fill=bar_color)
        draw.point((10, 25), fill=bar_color)
        draw.point((21, 25), fill=bar_color)
        if value is not None:
            width = max(0, min(10, round(float(value) * 10 / 100)))
            if width:
                draw.line((11, 25, 10 + width, 25), fill=bar_color)
        return image

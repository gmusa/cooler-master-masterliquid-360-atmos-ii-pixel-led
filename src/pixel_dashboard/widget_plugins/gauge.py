"""Shared sensor gauge rendering."""
from PIL import Image, ImageDraw


class Gauge:
    color = 'orange'
    label = ''

    def render(self, data, now, palette=None):
        image = Image.new('RGB', (32, 32))
        draw = ImageDraw.Draw(image)
        temperature = data.get('temperature')
        usage = data.get('usage')
        text_color = palette['on_surface'] if palette else 'white'
        draw.text((2, 1), self.label, fill=text_color)
        draw.text((2, 10), f'{round(temperature)}C' if temperature is not None else '--', fill=text_color)
        draw.text((2, 19), f'{round(usage)}%' if usage is not None else '--', fill=text_color)
        # Prefer actual utilization; otherwise display the available temperature
        # as a 0–100 scale. Empty outline means neither measurement is present.
        value = usage if usage is not None else temperature
        draw.rectangle((2, 28, 29, 31), outline=palette['primary'] if palette else self.color)
        if value is not None:
            width = max(0, min(26, round(float(value) * 26 / 100)))
            if width:
                draw.rectangle((3, 29, 2 + width, 30), fill=palette['primary'] if palette else self.color)
        return image

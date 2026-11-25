"""Shared sensor gauge rendering."""
from PIL import Image, ImageDraw, ImageFont


class Gauge:
    color = 'orange'
    label = ''

    def render(self, data, now, palette=None, *, phase=0, duration=1):
        image = Image.new('RGB', (32, 32))
        draw = ImageDraw.Draw(image)
        usage_active = phase >= duration / 2
        value = data.get('usage' if usage_active else 'temperature')
        text = ('--' if value is None else
                f'{round(value)}{"%" if usage_active else "C"}')
        identity = palette['on_surface'] if palette else 'white'
        text_color = (palette['secondary' if usage_active else 'primary'] if palette else self.color)
        label_font = ImageFont.load_default(size=7)
        label_box = draw.textbbox((0, 0), self.label, font=label_font)
        draw.text(((32 - (label_box[2] - label_box[0])) // 2 - label_box[0], 5),
                  self.label, font=label_font, fill=identity)
        # Keep large readings inside the central square, even at extreme values.
        font = ImageFont.load_default(size=7)
        box = draw.textbbox((0, 0), text, font=font)
        for size in range(13, 6, -1):
            font = ImageFont.load_default(size=size)
            box = draw.textbbox((0, 0), text, font=font)
            if box[2] - box[0] <= 24 and box[3] - box[1] <= 14:
                break
        draw.text(((32 - (box[2] - box[0])) // 2 - box[0],
                   17 - (box[3] - box[1]) // 2 - box[1]), text,
                  font=font, fill=text_color)
        return image

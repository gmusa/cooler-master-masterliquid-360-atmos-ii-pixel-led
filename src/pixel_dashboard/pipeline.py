"""Deterministic playlist timing and 32×32 image option pipeline."""
from PIL import Image, ImageDraw

from .led_mask import ROW_BOUNDS


class Sequencer:
    def __init__(self, playlist):
        self.playlist = playlist
        self.period = sum(entry.options.duration for entry in playlist.widgets)

    def at(self, seconds):
        if seconds < 0:
            raise ValueError('time must be nonnegative')
        position = seconds % self.period
        for entry in self.playlist.widgets:
            if position < entry.options.duration:
                return entry
            position -= entry.options.duration
        return self.playlist.widgets[-1]


def render_frame(image, options):
    """Apply rotation, brightness and the indexed cm-pixel LED mask."""
    if image.size != (32, 32):
        raise ValueError('widget must render a 32x32 frame')
    result = image.convert('RGB').rotate(options.rotation)
    if options.brightness != 100:
        result = result.point(lambda value: round(value * options.brightness / 100))
    if options.mask:
        mask = Image.new('L', (32, 32))
        draw = ImageDraw.Draw(mask)
        for y, (start, end) in enumerate(ROW_BOUNDS):
            if end > start:
                draw.line((start, y, end - 1, y), fill=255)
        black = Image.new('RGB', (32, 32))
        result = Image.composite(result, black, mask)
    return result

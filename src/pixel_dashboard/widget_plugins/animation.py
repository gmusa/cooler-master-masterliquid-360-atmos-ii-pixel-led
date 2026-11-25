"""Moving dot and named cm-pixel animation widgets."""
from PIL import Image, ImageDraw


class Animation:
    def __init__(self):
        self.generator = None
        self.selection = None

    def render(self, data, now, palette=None, animation=None):
        if animation is not None:
            if self.generator is None or self.selection != animation:
                from cmpixel.animations import ANIMATIONS
                self.generator = ANIMATIONS[animation]()
                self.selection = animation
            return Image.fromarray(next(self.generator), 'RGB')

        image = Image.new('RGB', (32, 32))
        draw = ImageDraw.Draw(image)
        x = int(now * 8) % 32
        draw.ellipse((x, 12, min(31, x + 4), 16), fill=palette['secondary'] if palette else 'green')
        return image


class AnimationPlayback:
    """Keep an effect alive only within its active playlist visit."""
    def __init__(self):
        self.widget = None
        self.config = None
        self.entry = None
        self.epoch = None
        self.phase = None

    def render(self, config, entry, phase, epoch, data, now, palette):
        if (config is not self.config or entry is not self.entry or epoch != self.epoch
                or (self.phase is not None and phase < self.phase)):
            self.widget = Animation() if entry.animation else None
        self.config, self.entry, self.epoch, self.phase = config, entry, epoch, phase
        if entry.name != 'animation':
            return None
        if entry.animation:
            assert self.widget is not None
            return self.widget.render(data, now, palette, animation=entry.animation)
        return None

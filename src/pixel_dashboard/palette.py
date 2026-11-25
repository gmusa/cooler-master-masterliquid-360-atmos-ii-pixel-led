import re
import tomllib
from pathlib import Path

ROLES = ('primary', 'on_surface', 'secondary')
HEX = re.compile(r'#[0-9a-fA-F]{6}\Z')


class PaletteStore:
    def __init__(self, path):
        self.path = Path(path)
        self.current = None
        if self.path.exists():
            self.current = self._load()

    def _load(self):
        try:
            document = tomllib.loads(self.path.read_text())
            colors = document['colors']
            if set(document) != {'colors'} or set(colors) != set(ROLES):
                raise ValueError('palette requires exactly three color roles')
            if any(not isinstance(colors[role], str) or not HEX.fullmatch(colors[role]) for role in ROLES):
                raise ValueError('invalid palette hex color')
            return colors
        except (OSError, tomllib.TOMLDecodeError, KeyError, TypeError) as exc:
            raise ValueError(f'invalid palette: {exc}') from exc

    def poll(self):
        try:
            self.current = self._load()
        except ValueError:
            return self.current
        return self.current

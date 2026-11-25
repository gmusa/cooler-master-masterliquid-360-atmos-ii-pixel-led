"""Strict dashboard configuration and atomic last-good reload."""
import tomllib
from dataclasses import dataclass
from pathlib import Path


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Options:
    duration: float = 4
    brightness: int = 50
    rotation: int = 0
    fps: int = 10
    mask: bool = True


@dataclass(frozen=True)
class Entry:
    name: str
    options: Options


@dataclass(frozen=True)
class Playlist:
    widgets: tuple[Entry, ...]


@dataclass(frozen=True)
class Config:
    normal: Playlist
    locked: Playlist


FIELDS = {'duration', 'brightness', 'rotation', 'fps', 'mask'}
NAMES = {'clock', 'date', 'cpu', 'gpu', 'animation'}


def _options(data, base):
    if not isinstance(data, dict) or set(data) - FIELDS:
        raise ConfigError('unknown option')
    values = {key: getattr(base, key) for key in FIELDS}
    values.update(data)
    for key in ('duration', 'fps'):
        value = values[key]
        maximum = 100 if key == 'fps' else 3600
        minimum = 0.01 if key == 'fps' else 0
        if type(value) not in (int, float) or not minimum <= value <= maximum or value == 0:
            raise ConfigError(f'invalid {key}')
    value = values['brightness']
    if type(value) is not int or not 0 <= value <= 100:
        raise ConfigError('invalid brightness')
    if type(values['rotation']) is not int or values['rotation'] not in (0, 90, 180, 270):
        raise ConfigError('invalid rotation')
    if type(values['mask']) is not bool:
        raise ConfigError('invalid mask')
    return Options(**values)


def parse_config(text):
    try:
        raw = tomllib.loads(text)
    except (tomllib.TOMLDecodeError, TypeError) as exc:
        raise ConfigError(str(exc)) from exc
    if set(raw) - {'defaults', 'normal', 'locked'} or not {'normal', 'locked'} <= set(raw):
        raise ConfigError('normal and locked playlists required; unknown root key')
    defaults = _options(raw.get('defaults', {}), Options())

    def playlist(name):
        section = raw[name]
        if not isinstance(section, dict) or set(section) - FIELDS - {'widgets'}:
            raise ConfigError(f'invalid {name} section')
        widgets = section.get('widgets')
        if not isinstance(widgets, list) or not widgets:
            raise ConfigError(f'{name} needs widgets')
        options = _options({k: v for k, v in section.items() if k != 'widgets'}, defaults)
        entries = []
        for widget in widgets:
            if not isinstance(widget, dict) or widget.get('name') not in NAMES:
                raise ConfigError('unknown widget')
            entries.append(Entry(widget['name'], _options({k: v for k, v in widget.items() if k != 'name'}, options)))
        return Playlist(tuple(entries))

    return Config(playlist('normal'), playlist('locked'))


class ConfigStore:
    def __init__(self, path):
        self.path = Path(path)
        self.current = None
        self.error = None
        self._seen = None
        self.failed_revision = None
        if not self.reload():
            raise ConfigError(self.error)

    def reload(self):
        try:
            # Read the candidate once, then store its signature after validation.
            # A subsequent poll retries if the file changes again.
            before = self.path.stat()
            candidate = parse_config(self.path.read_text())
            after = self.path.stat()
            if (before.st_mtime_ns, before.st_size) != (after.st_mtime_ns, after.st_size):
                raise ConfigError('configuration changed while reading')
            signature = (after.st_mtime_ns, after.st_size)
        except (OSError, ValueError) as exc:
            self.error = str(exc)
            try:
                stat = self.path.stat()
                self.failed_revision = (stat.st_mtime_ns, stat.st_size)
            except OSError:
                self.failed_revision = ('missing', self.error)
            return False
        self.failed_revision = None
        self.current = candidate
        self._seen = signature
        self.error = None
        return True

    def poll(self):
        """Check for changes synchronously; keep last good state on failure."""
        try:
            stat = self.path.stat()
            signature = (stat.st_mtime_ns, stat.st_size)
        except OSError as exc:
            self.error = str(exc)
            self.failed_revision = ('missing', self.error)
            return False
        if signature == self._seen:
            return False
        return self.reload()

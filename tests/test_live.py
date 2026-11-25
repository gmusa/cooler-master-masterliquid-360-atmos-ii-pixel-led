import pytest

from pixel_dashboard import backend, live
from pixel_dashboard.__main__ import main
from pixel_dashboard.sensors import Sample
from test_config_sensors import CONFIG


class Clock:
    def __init__(self):
        self.now = 0
        self.sleeps = []

    def monotonic(self):
        return self.now

    def time(self):
        return 1_700_000_000 + self.now

    def sleep(self, delay):
        self.sleeps.append(delay)
        self.now += delay


class Display:
    def __init__(self):
        self.opened = 0
        self.closed = 0
        self.frames = []

    def open(self):
        self.opened += 1

    def send_image(self, image):
        self.frames.append(image.copy())

    def close(self):
        self.closed += 1


def test_live_public_cli_frames_and_ownership(tmp_path, monkeypatch, capsys):
    config = tmp_path / 'config.toml'
    config.write_text(CONFIG.replace('name = "clock"', 'name = "cpu"'))
    clock, display = Clock(), Display()
    monkeypatch.setattr(live, 'make_display', lambda: display)
    monkeypatch.setattr(live, 'clock', clock)
    monkeypatch.setattr(live, 'sample_cpu', lambda: lambda: Sample(54, 50))
    monkeypatch.setattr(live, 'sample_gpu', lambda: Sample(60, 20))
    assert main(['live', '--config', str(config), '--duration', '.25']) == 0
    assert (display.opened, display.closed, len(display.frames)) == (1, 1, 3)
    assert len(clock.sleeps) == 3 and abs(sum(clock.sleeps) - .25) < 1e-9
    assert capsys.readouterr().err == ''


def test_live_clock_and_date_use_wall_time_public_cli(tmp_path, monkeypatch):
    config = tmp_path / 'config.toml'
    clock, display, seen = Clock(), Display(), []

    class Spy:
        def render(self, data, now):
            from PIL import Image
            seen.append(now)
            return Image.new('RGB', (32, 32))

    monkeypatch.setattr(live, 'make_display', lambda: display)
    monkeypatch.setattr(live, 'clock', clock)
    monkeypatch.setitem(live.registry, 'clock', Spy)
    # Both date and clock must receive wall timestamps, not monotonic elapsed time.
    config.write_text(CONFIG.replace('name = "cpu"', 'name = "date"')
                      .replace('duration = 3', 'duration = 0.1')
                      .replace('duration = 5', 'duration = 0.1'))
    monkeypatch.setitem(live.registry, 'date', Spy)
    assert main(['live', '--config', str(config), '--duration', '.2']) == 0
    assert seen == [1_700_000_000, 1_700_000_000.1]
    assert (display.opened, display.closed, len(display.frames)) == (1, 1, 2)


def test_live_rejections_no_output(tmp_path, monkeypatch, capsys):
    config = tmp_path / 'config.toml'
    config.write_text(CONFIG)
    display = Display()
    def denied():
        display.opened += 1
        raise PermissionError('access denied')
    display.open = denied
    monkeypatch.setattr(live, 'make_display', lambda: display)
    with pytest.raises(SystemExit) as rejected:
        main(['live', '--config', str(config), '--duration', '0'])
    assert rejected.value.code == 2
    invalid_output = capsys.readouterr()
    assert invalid_output.out == '' and 'duration' in invalid_output.err
    assert display.opened == 0
    assert main(['live', '--config', str(config), '--duration', '1']) == 1
    assert display.frames == [] and display.closed == 1
    output = capsys.readouterr()
    assert output.out == '' and 'access denied' in output.err


def test_live_reconciles_lock_and_resets_epoch(tmp_path, monkeypatch):
    config = tmp_path / 'config.toml'
    config.write_text(CONFIG)
    tick, display = Clock(), Display()
    monkeypatch.setattr(live, 'clock', tick)
    monkeypatch.setattr(live, 'make_display', lambda: display)
    seen = []
    def status():
        state = None if tick.now < .2 else not (tick.now < .5)
        seen.append((tick.now, state))
        return state
    monkeypatch.setattr(live, 'locked_status', status)
    rendered = []
    def spy(name):
        class Spy:
            def render(self, data, now, palette=None):
                from PIL import Image
                rendered.append((tick.now, name))
                return Image.new('RGB', (32, 32))
        return Spy
    for name in live.registry:
        monkeypatch.setitem(live.registry, name, spy(name))
    assert main(['live', '--config', str(config), '--duration', '.8']) == 0
    assert [state for _, state in seen] == [None, False, True, True]
    assert rendered[0][1] == 'date'
    assert any(name == 'clock' for t, name in rendered if .25 <= t < .5)
    assert any(name == 'date' for t, name in rendered if .5 <= t < .8)
    assert len(display.frames) > 0 and display.closed == 1


def test_live_ipc_outage_fails_closed_then_recovers(tmp_path, monkeypatch):
    config = tmp_path / 'config.toml'
    config.write_text(CONFIG.replace('fps = 10', 'fps = 1'))
    tick, display = Clock(), Display()
    monkeypatch.setattr(live, 'clock', tick)
    monkeypatch.setattr(live, 'make_display', lambda: display)
    replies = iter((False, None, False, False))
    monkeypatch.setattr(live, 'locked_status', lambda: next(replies))
    rendered = []

    def spy(name):
        class Spy:
            def render(self, data, now, palette=None):
                from PIL import Image
                rendered.append((tick.now, name))
                return Image.new('RGB', (32, 32))
        return Spy

    for name in live.registry:
        monkeypatch.setitem(live.registry, name, spy(name))
    assert main(['live', '--config', str(config), '--duration', '.8']) == 0
    assert rendered == [(0, 'clock'), (.25, 'date'), (.5, 'clock')]
    assert (display.opened, display.closed, len(display.frames)) == (1, 1, 3)


def test_live_invalid_palette_never_opens_usb(tmp_path, monkeypatch):
    config = tmp_path / 'config.toml'
    palette = tmp_path / 'palette.toml'
    config.write_text(CONFIG)
    palette.write_text('[colors]\nprimary = "red"\n')
    display = Display()
    monkeypatch.setattr(live, 'make_display', lambda: display)
    with pytest.raises(SystemExit) as rejected:
        main(['live', '--config', str(config), '--palette', str(palette), '--duration', '.2'])
    assert rejected.value.code == 2
    assert display.opened == 0


def test_backend_selects_hidraw_before_open(monkeypatch):
    class Module:
        PixelDisplay = Display
    module = Module()
    marker = object()
    monkeypatch.setattr(backend, 'open_hidraw_backend', lambda: marker)
    monkeypatch.setattr(backend.importlib, 'import_module', lambda name: module)
    display = backend.create_display()
    assert module.__dict__['hid'] is marker and isinstance(display, Display)


def test_preview_public_cli_unchanged(tmp_path, capsys):
    config, output = tmp_path / 'config.toml', tmp_path / 'preview.gif'
    config.write_text(CONFIG)
    assert main(['preview', '--config', str(config), '--frames', '1', '--output', str(output)]) == 0
    assert output.exists()
    assert capsys.readouterr().out == '1 frames rendered\n'

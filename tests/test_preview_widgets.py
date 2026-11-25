import subprocess
import sys
from dataclasses import replace
from pathlib import Path

from PIL import Image, ImageSequence

from pixel_dashboard.config import parse_config
from pixel_dashboard.pipeline import Sequencer, render_frame
from pixel_dashboard.widgets import registry


CONFIG = '''
[defaults]
duration = 2
brightness = 40
rotation = 0
fps = 10
mask = true
[normal]
duration = 3
[[normal.widgets]]
name = "clock"
[[normal.widgets]]
name = "cpu"
duration = 5
[locked]
brightness = 10
[[locked.widgets]]
name = "date"
[[locked.widgets]]
name = "animation"
'''


def test_preview_selected_animation_continues_and_wraps(tmp_path, monkeypatch):
    import cmpixel.animations
    import numpy as np

    from pixel_dashboard.__main__ import main

    starts = []
    def frames():
        starts.append(True)
        for value in (30, 90, 150):
            yield np.full((32, 32, 3), (value, 20, 10), dtype=np.uint8)

    monkeypatch.setitem(cmpixel.animations.ANIMATIONS, 'plasma', frames)
    config = tmp_path / 'config.toml'
    config.write_text('''[defaults]
duration = 0.2
fps = 10
brightness = 100
mask = false
[normal]
[[normal.widgets]]
name = "animation"
animation = "plasma"
[locked]
[[locked.widgets]]
name = "clock"
''')
    output = tmp_path / 'effect.gif'
    assert main(['preview', '--config', str(config), '--frames', '5', '--output', str(output)]) == 0
    with Image.open(output) as gif:
        assert [frame.convert('RGB').getpixel((16, 16)) for frame in ImageSequence.Iterator(gif)] == [
            (30, 20, 10), (90, 20, 10), (30, 20, 10), (90, 20, 10), (30, 20, 10)]
    assert len(starts) == 3


def test_time_selection_and_option_effects():
    cfg = parse_config(CONFIG)
    seq = Sequencer(cfg.normal)
    assert [seq.at(t).name for t in (0, 2.99, 3, 7.99, 8)] == ['clock', 'clock', 'cpu', 'cpu', 'clock']
    assert [(seq.at_phase(t)[0].name, seq.at_phase(t)[1]) for t in (3, 5.5, 7.99, 6)] == [
        ('cpu', 0), ('cpu', 2.5), ('cpu', 4.99), ('cpu', 3)]
    entry = cfg.normal.widgets[1]
    source = Image.new('RGB', (32, 32))
    source.putpixel((0, 16), (200, 100, 0))
    bright = render_frame(source, replace(entry.options, brightness=50, mask=False, rotation=0))
    assert bright.getpixel((0, 16)) == (100, 50, 0)
    rotated = render_frame(source, replace(entry.options, brightness=100, mask=False, rotation=90))
    assert rotated.getpixel((0, 16)) == (0, 0, 0)
    assert rotated.getbbox() is not None
    masked = render_frame(source, replace(entry.options, brightness=100, mask=True, rotation=0))
    assert masked.getpixel((0, 16)) == (0, 0, 0)


def test_cli_frame_timing_and_rejected_config(tmp_path):
    path = tmp_path / 'config.toml'
    path.write_text(CONFIG.replace('duration = 3', 'duration = 0.2').replace('duration = 5', 'duration = 0.2')
                    .replace('fps = 10', 'fps = 5'))
    output = tmp_path / 'trace.gif'
    command = [sys.executable, '-m', 'pixel_dashboard', 'preview', '--config', str(path),
               '--frames', '3', '--output', str(output), '--trace']
    result = subprocess.run(command, capture_output=True, text=True, timeout=10)
    assert (result.returncode, result.stderr) == (0, '')
    assert result.stdout.splitlines() == ['0.000 clock', '0.200 cpu', '0.400 clock', '3 frames rendered']
    with Image.open(output) as gif:
        assert len(list(ImageSequence.Iterator(gif))) == 3
        assert gif.info['duration'] == 200
    output.unlink()
    path.write_text(CONFIG.replace('rotation = 0', 'rotation = 45'))
    rejected = subprocess.run(command, capture_output=True, text=True, timeout=10)
    assert rejected.returncode == 2 and rejected.stdout == ''
    assert rejected.stderr.startswith('usage: pixel-dashboard ')
    assert rejected.stderr.splitlines()[-1] == 'pixel-dashboard: error: invalid rotation'
    assert not output.exists()
    path.write_text(CONFIG)
    locked = subprocess.run(command + ['--locked'], capture_output=True, text=True, timeout=10)
    assert locked.returncode == 0 and locked.stderr == ''
    assert locked.stdout.splitlines()[0] == '0.000 date'


def test_cli_preserves_identical_frames_and_led_pixels(tmp_path):
    path = tmp_path / 'config.toml'
    path.write_text(CONFIG.replace('name = "clock"', 'name = "animation"'))
    output = tmp_path / 'preview.gif'
    result = subprocess.run([sys.executable, '-m', 'pixel_dashboard', 'preview', '--config', str(path),
                             '--frames', '20', '--output', str(output)], capture_output=True, text=True, timeout=10)
    assert (result.returncode, result.stdout, result.stderr) == (0, '20 frames rendered\n', '')
    with Image.open(output) as gif:
        assert len(list(ImageSequence.Iterator(gif))) == 20
        pixels = [frame.convert('RGB').getpixel((14, 2)) for frame in ImageSequence.Iterator(gif)]
        assert len(set(pixels)) == 1


def test_documented_example_writes_requested_frames(tmp_path):
    config = Path(__file__).resolve().parents[1] / 'examples/config.toml'
    output = tmp_path / 'example.gif'
    result = subprocess.run([sys.executable, '-m', 'pixel_dashboard', 'preview', '--config', str(config),
                             '--frames', '20', '--output', str(output)], capture_output=True, text=True, timeout=10)
    assert (result.returncode, result.stdout, result.stderr) == (0, '20 frames rendered\n', '')
    with Image.open(output) as gif:
        assert len(list(ImageSequence.Iterator(gif))) == 20


def test_cli_fps_lower_boundary_and_rejection(tmp_path):
    path = tmp_path / 'config.toml'
    output = tmp_path / 'preview.gif'
    command = [sys.executable, '-m', 'pixel_dashboard', 'preview', '--config', str(path),
               '--frames', '1', '--output', str(output)]
    path.write_text(CONFIG.replace('fps = 10', 'fps = 0.01'))
    valid = subprocess.run(command, capture_output=True, text=True, timeout=10)
    assert (valid.returncode, valid.stdout, valid.stderr) == (0, '1 frames rendered\n', '')
    with Image.open(output) as gif:
        assert len(list(ImageSequence.Iterator(gif))) == 1
        assert gif.info['duration'] == 100000
    output.unlink()
    path.write_text(CONFIG.replace('fps = 10', 'fps = 0.0001'))
    invalid = subprocess.run(command, capture_output=True, text=True, timeout=10)
    assert (invalid.returncode, invalid.stdout) == (2, '')
    assert invalid.stderr.startswith('usage: pixel-dashboard ')
    assert invalid.stderr.splitlines()[-1] == 'pixel-dashboard: error: invalid fps'
    assert not output.exists()


def test_widget_plugins_are_independent_modules():
    from pixel_dashboard.widget_plugins.animation import Animation
    from pixel_dashboard.widget_plugins.clock import Clock
    from pixel_dashboard.widget_plugins.cpu import CPU
    from pixel_dashboard.widget_plugins.date import Date
    from pixel_dashboard.widget_plugins.gpu import GPU
    from pixel_dashboard.widget_plugins.gauge import Gauge
    from pixel_dashboard.widgets import Animation as ExportedAnimation
    from pixel_dashboard.widgets import Clock as ExportedClock
    from pixel_dashboard.widgets import CPU as ExportedCPU
    from pixel_dashboard.widgets import Date as ExportedDate
    from pixel_dashboard.widgets import GPU as ExportedGPU
    from pixel_dashboard.widgets import Gauge as ExportedGauge

    assert registry == dict(clock=Clock, date=Date, cpu=CPU, gpu=GPU, animation=Animation)
    assert (ExportedClock, ExportedDate, ExportedCPU, ExportedGPU, ExportedAnimation, ExportedGauge) == (
        Clock, Date, CPU, GPU, Animation, Gauge)
    assert CPU.__bases__ == (Gauge,) and GPU.__bases__ == (Gauge,)
    assert len({cls.__module__ for cls in registry.values()}) == 5


def test_widgets_visual_and_registry():
    assert {'clock', 'date', 'cpu', 'gpu', 'animation'} <= set(registry)
    for name in ('cpu', 'gpu', 'animation'):
        image = registry[name]().render({'temperature': 60, 'usage': 70}, 0)
        assert image.size == (32, 32)
        assert image.getbbox() is not None


def test_preview_polls_between_frames(tmp_path, monkeypatch, capsys):
    from pixel_dashboard.__main__ import main

    path = tmp_path / 'config.toml'
    path.write_text(CONFIG.replace('name = "clock"', 'name = "animation"'))
    original_render = registry['animation'].render
    calls = []

    def render(self, data, now):
        calls.append(now)
        if len(calls) == 1:
            path.write_text(CONFIG.replace('name = "clock"', 'name = "animation"')
                            .replace('fps = 10', 'fps = 5'))
        return original_render(self, data, now)

    monkeypatch.setattr(registry['animation'], 'render', render)
    assert main(['preview', '--config', str(path), '--frames', '3',
                 '--output', str(tmp_path / 'poll.gif'), '--trace']) == 0
    assert capsys.readouterr().out.splitlines() == [
        '0.000 animation', '0.100 animation', '0.300 animation', '3 frames rendered']


def test_cli_pixels_and_inherited_fps(tmp_path):
    base = CONFIG.replace('name = "clock"', 'name = "animation"').replace('name = "cpu"', 'name = "animation"')
    base = base.replace('fps = 10', 'fps = 5').replace('brightness = 40', 'brightness = 100')
    path = tmp_path / 'config.toml'
    output = tmp_path / 'frame.gif'

    def preview(config):
        path.write_text(config)
        result = subprocess.run([sys.executable, '-m', 'pixel_dashboard', 'preview', '--config', str(path),
                                 '--frames', '2', '--output', str(output)], capture_output=True, text=True, timeout=10)
        assert (result.returncode, result.stderr) == (0, '')
        with Image.open(output) as gif:
            assert gif.info['duration'] == 200
            pixel = gif.convert('RGB').getpixel((0, 14))
            assert isinstance(pixel, tuple)
            return pixel, gif.convert('RGB').getbbox()

    full, _ = preview(base.replace('mask = true', 'mask = false'))
    dim, _ = preview(base.replace('mask = true', 'mask = false').replace('brightness = 100', 'brightness = 50'))
    masked, _ = preview(base)
    assert full[1] > dim[1] > 0
    assert masked == (0, 0, 0)
    rotated, bbox = preview(base.replace('mask = true', 'mask = false').replace('rotation = 0', 'rotation = 90'))
    assert rotated == (0, 0, 0) and bbox is not None


def test_cli_uses_upstream_led_topology(tmp_path, monkeypatch):
    from pixel_dashboard.__main__ import main

    path = tmp_path / 'config.toml'
    output = tmp_path / 'mask.gif'
    base = CONFIG.replace('name = "clock"', 'name = "animation"').replace('brightness = 40', 'brightness = 100')
    path.write_text(base)
    monkeypatch.setattr(registry['animation'], 'render', lambda self, data, now: Image.new('RGB', (32, 32), 'white'))
    assert main(['preview', '--config', str(path), '--frames', '1', '--output', str(output)]) == 0
    with Image.open(output) as gif:
        frame = gif.convert('RGB')
        # Former ellipse lit these two absent LEDs; upstream topology does not.
        assert frame.getpixel((12, 1)) == (0, 0, 0)
        assert frame.getpixel((10, 2)) == (0, 0, 0)
        assert frame.getpixel((14, 2)) != (0, 0, 0)
    path.write_text(base.replace('mask = true', 'mask = false'))
    assert main(['preview', '--config', str(path), '--frames', '1', '--output', str(output)]) == 0
    with Image.open(output) as gif:
        assert gif.convert('RGB').getpixel((0, 0)) != (0, 0, 0)


def test_cli_hex_layout_preserves_widget_pixels(tmp_path):
    path = tmp_path / 'config.toml'
    output = tmp_path / 'layout.gif'
    for name in ('cpu', 'gpu', 'date'):
        for rotation in (0, 90, 180, 270):
            frames = []
            for masked in (False, True):
                config = f'''[defaults]
duration = 1
brightness = 100
rotation = {rotation}
fps = 10
mask = {str(masked).lower()}
[normal]
[[normal.widgets]]
name = "{name}"
[locked]
[[locked.widgets]]
name = "{name}"
'''
                path.write_text(config)
                result = subprocess.run([sys.executable, '-m', 'pixel_dashboard', 'preview',
                                         '--config', str(path), '--frames', '1', '--output', str(output)],
                                        capture_output=True, text=True, timeout=10)
                assert (result.returncode, result.stdout, result.stderr) == (0, '1 frames rendered\n', '')
                with Image.open(output) as gif:
                    frames.append(gif.convert('RGB').copy())
            before, after = ({(x, y) for y in range(32) for x in range(32)
                              if frame.getpixel((x, y)) != (0, 0, 0)} for frame in frames)
            assert before and before == after, (name, rotation, len(before - after))


def test_hex_boundary_metrics_and_palette_survive_all_rotations():
    from datetime import datetime

    palette = {'primary': '#ff8cb3', 'on_surface': '#ffe0eb', 'secondary': '#ffb3cc'}
    options = parse_config(CONFIG).normal.widgets[1].options
    date = registry['date']().render({}, datetime(2026, 12, 31).timestamp(), palette)
    other_date = registry['date']().render({}, datetime(2026, 1, 1).timestamp(), palette)
    assert date.tobytes() != other_date.tobytes()

    cases = [('date', date)]
    for name in ('cpu', 'gpu'):
        widget = registry[name]()
        temperature_images = []
        for temperature in (-99, 999, 1000):
            image = widget.render({'temperature': temperature, 'usage': 100}, 0, palette)
            assert image.crop((4, 10, 28, 25)).getbbox() is not None
            temperature_images.append(image.tobytes())
            cases.append((f'{name} {temperature}C', image))
        assert len(set(temperature_images)) == 3, name
        for data in ({'temperature': None, 'usage': None}, {'temperature': 60, 'usage': 100}):
            for phase in (0, 0.5):
                image = widget.render(data, 0, palette, phase=phase, duration=1)
                assert image.crop((4, 10, 28, 25)).getbbox() is not None
                cases.append((f'{name} {data} {phase}', image))

    for label, image in cases:
        source = {(x, y) for y in range(32) for x in range(32)
                  if image.getpixel((x, y)) != (0, 0, 0)}
        assert source, label
        colors = {image.getpixel((x, y)) for y in range(32) for x in range(32)}
        # Small scaled fonts are antialiased, so their pixels are blends of the
        # on_surface role rather than necessarily its exact RGB value.
        text_pixels = {color for color in colors if color != (0, 0, 0) and
                       color[0] >= color[2] >= color[1] and color[1] > color[0] * 0.8}
        assert text_pixels, label
        if label != 'date':
            assert any(r > b > g and r > 100 for r, g, b in colors)
        for rotation in (0, 90, 180, 270):
            full = render_frame(image, replace(options, rotation=rotation, brightness=100, mask=False))
            masked = render_frame(image, replace(options, rotation=rotation, brightness=100, mask=True))
            before = {(x, y) for y in range(32) for x in range(32)
                      if full.getpixel((x, y)) != (0, 0, 0)}
            after = {(x, y) for y in range(32) for x in range(32)
                     if masked.getpixel((x, y)) != (0, 0, 0)}
            assert before == after and len(before) == len(source), (label, rotation, len(before - after))
            assert {masked.getpixel((x, y)) for x, y in after} == {image.getpixel((x, y)) for x, y in source}


def test_cli_entry_local_sensor_alternation(tmp_path):
    path, output = tmp_path / 'config.toml', tmp_path / 'metrics.gif'
    config = (CONFIG.replace('name = "clock"', 'name = "cpu"')
              .replace('duration = 3', 'duration = 2').replace('name = "cpu"\nduration = 5', 'name = "gpu"\nduration = 3')
              .replace('fps = 10', 'fps = 2'))
    path.write_text(config)
    result = subprocess.run([sys.executable, '-m', 'pixel_dashboard', 'preview', '--config', str(path),
                             '--frames', '20', '--output', str(output), '--trace'],
                            capture_output=True, text=True, timeout=10)
    assert (result.returncode, result.stderr) == (0, '')
    assert result.stdout.splitlines() == [f'{i / 2:.3f} {"cpu" if i % 10 < 4 else "gpu"}' for i in range(20)] + ['20 frames rendered']
    with Image.open(output) as gif:
        frames = [frame.convert('RGB').copy() for frame in ImageSequence.Iterator(gif)]
    assert len(frames) == 20
    for a, b in ((0, 10), (2, 12), (4, 14), (7, 17)):
        assert frames[a].crop((1, 0, 32, 32)).tobytes() == frames[b].crop((1, 0, 32, 32)).tobytes()
    assert frames[0].crop((1, 0, 32, 32)).tobytes() != frames[2].crop((1, 0, 32, 32)).tobytes()
    assert frames[4].crop((1, 0, 32, 32)).tobytes() != frames[7].crop((1, 0, 32, 32)).tobytes()


def test_sensor_palette_roles_change_with_phase():
    palette = {'primary': '#ff8cb3', 'secondary': '#ffb3cc', 'on_surface': '#ffe0eb'}
    for name in ('cpu', 'gpu'):
        widget = registry[name]()
        temperature = widget.render({'temperature': 60, 'usage': 70}, 0, palette, phase=0, duration=2)
        usage = widget.render({'temperature': 60, 'usage': 70}, 0, palette, phase=1, duration=2)
        assert temperature.crop((4, 12, 28, 25)).getbbox() is not None
        assert usage.crop((4, 12, 28, 25)).getbbox() is not None
        assert (255, 140, 179) in set(temperature.crop((4, 12, 28, 25)).getdata())
        assert (255, 179, 204) in set(usage.crop((4, 12, 28, 25)).getdata())
        assert temperature.crop((4, 4, 28, 11)).tobytes() == usage.crop((4, 4, 28, 11)).tobytes()


def test_cli_sensor_metrics_are_visible(tmp_path):
    path = tmp_path / 'config.toml'
    output = tmp_path / 'metrics.gif'
    for name in ('cpu', 'gpu'):
        config = CONFIG.replace('name = "clock"', f'name = "{name}"')
        path.write_text(config.replace('brightness = 40', 'brightness = 100').replace('mask = true', 'mask = false'))
        result = subprocess.run([sys.executable, '-m', 'pixel_dashboard', 'preview', '--config', str(path),
                                 '--frames', '1', '--output', str(output)], capture_output=True, text=True, timeout=10)
        assert (result.returncode, result.stderr) == (0, '')
        with Image.open(output) as gif:
            actual = gif.convert('RGB')
        assert actual.crop((4, 4, 28, 11)).getbbox() is not None  # identity
        assert actual.crop((4, 11, 28, 25)).getbbox() is not None  # one large reading
        assert actual.crop((0, 25, 32, 32)).getbbox() is None


def test_cli_preview_bounded_no_usb(tmp_path):
    path = tmp_path / 'config.toml'
    path.write_text(CONFIG)
    result = subprocess.run([sys.executable, '-m', 'pixel_dashboard', 'preview', '--config', str(path),
                             '--frames', '2', '--output', str(tmp_path / 'preview.gif')],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / 'preview.gif').exists()
    assert '2 frames' in result.stdout

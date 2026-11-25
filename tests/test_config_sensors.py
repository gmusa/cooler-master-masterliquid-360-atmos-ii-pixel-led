import json

import pytest

from pixel_dashboard.config import ConfigError, ConfigStore, parse_config
from pixel_dashboard.sensors import parse_cpu, parse_gpu


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


def test_order_and_inheritance():
    cfg = parse_config(CONFIG)
    assert [w.name for w in cfg.normal.widgets] == ['clock', 'cpu']
    assert [w.name for w in cfg.locked.widgets] == ['date', 'animation']
    assert [w.options.duration for w in cfg.normal.widgets] == [3, 5]
    assert cfg.locked.widgets[0].options.brightness == 10
    assert cfg.normal.widgets[0].options.brightness == 40
    assert cfg.normal.widgets[0].options.rotation == 0
    assert cfg.normal.widgets[0].options.fps == 10
    assert cfg.normal.widgets[0].options.mask is True


@pytest.mark.parametrize('candidate', [
    CONFIG + '\n[unknown]\na=1',
    CONFIG.replace('name = "cpu"', 'name = "oops"'),
    CONFIG.replace('brightness = 40', 'brightness = 101'),
    CONFIG.replace('fps = 10', 'fps = 0'),
    CONFIG.replace('name = "clock"', 'name = "clock"\nextra = 1'),
    CONFIG.replace('mask = true', 'mask = 1'),
    CONFIG.replace('rotation = 0', 'rotation = 45'),
])
def test_strict_invalid(candidate):
    with pytest.raises(ConfigError):
        parse_config(candidate)


@pytest.mark.parametrize('angle', [0, 90, 180, 270])
def test_supported_rotation(angle):
    assert parse_config(CONFIG.replace('rotation = 0', f'rotation = {angle}')).normal.widgets[0].options.rotation == angle


def test_poll_bad_then_good_without_thread(tmp_path):
    path = tmp_path / 'config.toml'
    path.write_text(CONFIG)
    store = ConfigStore(path)
    original = store.current
    assert store.poll() is False
    path.write_text(CONFIG.replace('rotation = 0', 'rotation = 45'))
    assert store.poll() is False
    assert store.current is original and store.error
    path.write_text(CONFIG.replace('duration = 5', 'duration = 7'))
    assert store.poll() is True
    assert store.current is not None
    assert store.current.normal.widgets[1].options.duration == 7
    assert store.error is None


def test_low_fps_reload_keeps_last_good_config(tmp_path):
    path = tmp_path / 'config.toml'
    path.write_text(CONFIG)
    store = ConfigStore(path)
    original = store.current
    path.write_text(CONFIG.replace('fps = 10', 'fps = 0.0001'))
    assert store.poll() is False
    assert store.current is original
    assert store.error == 'invalid fps'


def test_last_good_reload(tmp_path):
    path = tmp_path / 'config.toml'
    path.write_text(CONFIG)
    store = ConfigStore(path)
    original = store.current
    path.write_text(CONFIG + '\n[unexpected]\nfoo=1')
    assert store.reload() is False
    assert store.current is original
    assert store.error
    path.write_text(CONFIG.replace('duration = 5', 'duration = 7'))
    assert store.reload() is True
    assert store.current is not None
    assert store.current.normal.widgets[1].options.duration == 7
    assert store.error is None


def test_sensor_partial_and_unavailable():
    data = {'k10temp-pci-00c3': {'Tctl': {'temp1_input': 54.5, 'temp2_input': 'error'}}}
    assert parse_cpu(json.dumps(data)).temperature == 54.5
    assert parse_cpu('{broken').temperature is None
    assert parse_cpu('{}').usage is None
    gpu = parse_gpu('NVIDIA GeForce RTX 5070, 61, 28, 1120')
    assert (gpu.temperature, gpu.usage, gpu.fan_rpm) == (61, 28, None)
    assert parse_gpu('N/A, N/A, N/A').temperature is None

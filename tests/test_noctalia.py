import pytest

from pixel_dashboard.__main__ import main
from pixel_dashboard.palette import PaletteStore
from pixel_dashboard.widget_plugins.animation import Animation
from pixel_dashboard.widget_plugins.clock import Clock
from pixel_dashboard.widget_plugins.cpu import CPU
from pixel_dashboard.widget_plugins.date import Date
from pixel_dashboard.widget_plugins.gpu import GPU


def test_palette_last_good(tmp_path):
    path = tmp_path / 'palette.toml'
    store = PaletteStore(path)
    assert store.current is None
    path.write_text('[colors]\nprimary = "#123456"\non_surface = "#abcdef"\nsecondary = "#010203"\n')
    store.poll()
    assert store.current is not None and store.current['primary'] == '#123456'
    path.write_text('[colors]\nprimary = "red"\n')
    store.poll()
    assert store.current is not None and store.current['primary'] == '#123456'


def test_palette_rejects_invalid_initial(tmp_path):
    path = tmp_path / 'palette.toml'
    path.write_text('[colors]\nprimary = "red"\n')
    with pytest.raises(ValueError):
        PaletteStore(path)


def test_preview_generated_palette_and_invalid_no_output(tmp_path):
    from test_config_sensors import CONFIG
    config, palette, output = (tmp_path / name for name in ('config.toml', 'palette.toml', 'preview.gif'))
    config.write_text(CONFIG)
    palette.write_text('[colors]\nprimary = "red"\n')
    with pytest.raises(SystemExit):
        main(['preview', '--config', str(config), '--palette', str(palette),
              '--frames', '1', '--output', str(output)])
    assert not output.exists()
    palette.write_text('[colors]\nprimary = "#123456"\non_surface = "#abcdef"\nsecondary = "#010203"\n')
    assert main(['preview', '--config', str(config), '--palette', str(palette),
                 '--frames', '1', '--output', str(output)]) == 0
    assert output.exists()


def test_widget_palette_colors():
    palette = {'primary': '#123456', 'on_surface': '#abcdef', 'secondary': '#010203'}
    for widget in (Clock(), Date(), CPU(), GPU()):
        image = widget.render({'temperature': 60, 'usage': 70}, 1700000000, palette)
        assert image.tobytes() != widget.render({'temperature': 60, 'usage': 70}, 1700000000).tobytes()
        if isinstance(widget, (CPU, GPU)):
            assert (18, 52, 86) in image.getdata()
    assert (1, 2, 3) in Animation().render({}, 0, palette).getdata()

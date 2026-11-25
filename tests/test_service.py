from pixel_dashboard import live
from pixel_dashboard.__main__ import main
from test_config_sensors import CONFIG
from test_live import Clock, Display


def test_serve_display_denied_reports_mode_and_closes(tmp_path, monkeypatch, capsys):
    path = tmp_path / 'config.toml'
    path.write_text(CONFIG)
    display = Display()

    def denied():
        display.opened += 1
        raise PermissionError('access denied')

    display.open = denied
    monkeypatch.setattr(live, 'make_display', lambda: display)
    assert main(['serve', '--config', str(path)]) == 1
    output = capsys.readouterr()
    assert output.out == ''
    assert output.err.startswith('pixel-dashboard serve: access denied')
    assert (display.opened, display.closed) == (1, 1)


def test_serve_reload_diagnostic_recovery_and_stop(tmp_path, monkeypatch, capsys):
    path = tmp_path / 'config.toml'
    path.write_text(CONFIG)
    tick, display = Clock(), Display()
    events = []
    original_sleep = tick.sleep

    def sleep(delay):
        original_sleep(delay)
        if tick.now >= .1 and not events:
            path.write_text('broken = [')
            events.append('invalid')
        elif tick.now >= .35 and events == ['invalid']:
            path.write_text(CONFIG.replace('name = "clock"', 'name = "animation"'))
            events.append('recovered')
        elif tick.now >= .65:
            raise KeyboardInterrupt

    tick.sleep = sleep
    monkeypatch.setattr(live, 'clock', tick)
    monkeypatch.setattr(live, 'make_display', lambda: display)
    monkeypatch.setattr(live, 'locked_status', lambda: False)
    messages = []
    monkeypatch.setattr(live, 'report_invalid', messages.append, raising=False)
    rendered = []

    def spy(name):
        class Widget:
            def render(self, data, now, palette=None):
                from PIL import Image
                rendered.append((tick.now, name))
                return Image.new('RGB', (32, 32))
        return Widget

    for name in live.registry:
        monkeypatch.setitem(live.registry, name, spy(name))
    assert main(['serve', '--config', str(path)]) == 0
    assert events == ['invalid', 'recovered']
    assert (display.opened, display.closed) == (1, 1)
    assert any(.1 <= t < .35 and name == 'clock' for t, name in rendered)
    assert any(t >= .35 and name == 'animation' for t, name in rendered)
    assert len(display.frames) == len(rendered)
    assert len(messages) == 1 and messages[0]
    assert capsys.readouterr().err == ''

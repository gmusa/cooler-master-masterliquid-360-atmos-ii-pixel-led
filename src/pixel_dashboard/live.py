"""Bounded single-owner USB loop. No hardware is opened by import or preview."""
import time

from .backend import create_display
from .diagnostics import report_invalid
from .config import ConfigStore
from .noctalia import locked_status
from .palette import PaletteStore
from .pipeline import Sequencer, render_frame
from .sensors import CpuSampler, sample_gpu
from .widgets import registry

clock = time
sample_cpu = CpuSampler


def make_display():
    return create_display()


def run(path, duration=None, palette_path=None):
    """Return frame count; close the display even if opening or streaming fails."""
    store = ConfigStore(path)
    palette = PaletteStore(palette_path) if palette_path else None
    display = make_display()
    cpu = sample_cpu()
    start = clock.monotonic()
    count = 0
    reported = None
    locked = True
    epoch = start
    next_status = start
    try:
        display.open()
        deadline = start + duration if duration is not None else float('inf')
        next_frame = start
        while True:
            now = clock.monotonic()
            if now >= deadline:
                break
            if now >= next_status:
                state = locked_status()
                next_status = now + .25
                fail_closed = state is not False
                if fail_closed != locked:
                    locked, epoch = fail_closed, now
                    next_frame = now
            if now < next_frame:
                clock.sleep(min(next_frame - now, next_status - now, deadline - now))
                continue
            store.poll()
            if store.error:
                if store.failed_revision != reported:
                    report_invalid(store.error)
                    reported = store.failed_revision
            else:
                reported = None
            config = store.current
            assert config is not None
            entry, phase = Sequencer(config.locked if locked else config.normal).at_phase(now - epoch)
            sample = (cpu() if entry.name == 'cpu' else
                      sample_gpu() if entry.name == 'gpu' else None)
            data = vars(sample) if sample is not None else {}
            render_time = clock.time() if entry.name in ('clock', 'date') else now - start
            colors = palette.poll() if palette else None
            widget = registry[entry.name]()
            if entry.name in ('cpu', 'gpu'):
                image = widget.render(data, render_time, colors, phase=phase, duration=entry.options.duration)
            else:
                image = widget.render(data, render_time, colors) if colors else widget.render(data, render_time)
            display.send_image(render_frame(image, entry.options))
            count += 1
            next_frame = now + 1 / entry.options.fps
        return count
    finally:
        display.close()

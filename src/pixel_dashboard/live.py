"""Bounded single-owner USB loop. No hardware is opened by import or preview."""
import time

from .backend import create_display
from .config import ConfigStore
from .pipeline import Sequencer, render_frame
from .sensors import CpuSampler, sample_gpu
from .widgets import registry

clock = time
sample_cpu = CpuSampler


def make_display():
    return create_display()


def run(path, duration):
    """Return frame count; close the display even if opening or streaming fails."""
    store = ConfigStore(path)
    display = make_display()
    cpu = sample_cpu()
    start = clock.monotonic()
    count = 0
    try:
        display.open()
        deadline = start + duration
        next_frame = start
        while True:
            now = clock.monotonic()
            if now >= deadline:
                break
            if now < next_frame:
                clock.sleep(min(next_frame - now, deadline - now))
                continue
            store.poll()
            config = store.current
            assert config is not None
            entry = Sequencer(config.normal).at(now - start)
            sample = (cpu() if entry.name == 'cpu' else
                      sample_gpu() if entry.name == 'gpu' else None)
            data = vars(sample) if sample is not None else {}
            render_time = clock.time() if entry.name in ('clock', 'date') else now - start
            image = registry[entry.name]().render(data, render_time)
            display.send_image(render_frame(image, entry.options))
            count += 1
            next_frame = now + 1 / entry.options.fps
        return count
    finally:
        display.close()

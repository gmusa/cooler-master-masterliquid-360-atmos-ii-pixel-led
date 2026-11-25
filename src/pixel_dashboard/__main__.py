"""Bounded, USB-free local preview."""
import argparse
import sys

from .config import ConfigError, ConfigStore
from .pipeline import Sequencer, render_frame
from .widgets import registry


def main(argv=None):
    parser = argparse.ArgumentParser(prog='pixel-dashboard')
    parser.add_argument('mode', choices=['preview', 'live'])
    parser.add_argument('--config', required=True)
    parser.add_argument('--frames', type=int, default=10)
    parser.add_argument('--output')
    parser.add_argument('--duration', type=float)
    parser.add_argument('--locked', action='store_true')
    parser.add_argument('--trace', action='store_true', help='print logical frame time and widget')
    args = parser.parse_args(argv)
    if args.mode == 'live':
        if args.output is not None or args.duration is None or not 0 < args.duration <= 3600:
            parser.error('live requires --duration between 0 and 3600 and no --output')
        try:
            from .live import run
            run(args.config, args.duration)
        except ConfigError as exc:
            parser.error(str(exc))
        except (OSError, RuntimeError, ImportError) as exc:
            print(f'pixel-dashboard live: {exc}', file=sys.stderr)
            return 1
        return 0
    if args.output is None or args.duration is not None:
        parser.error('preview requires --output and no --duration')
    if not 1 <= args.frames <= 300:
        parser.error('frames must be between 1 and 300')
    try:
        store = ConfigStore(args.config)
    except ConfigError as exc:
        parser.error(str(exc))
    images = []
    delays = []
    traces = []
    seconds = 0.0
    for index in range(args.frames):
        store.poll()
        config = store.current
        assert config is not None  # constructor requires an initial valid config
        playlist = config.locked if args.locked else config.normal
        entry = Sequencer(playlist).at(seconds)
        # GIF stores each frame delay in a 16-bit centisecond field.
        if entry.options.fps < 0.01:
            parser.error('invalid fps')
        # Synthetic sample for the demo only; no sensors or USB are opened.
        sample = ({'temperature': 60} if entry.name == 'cpu' else
                  {'temperature': 60, 'usage': 70} if entry.name == 'gpu' else {})
        image = registry[entry.name]().render(sample, seconds)
        frame = render_frame(image, entry.options)
        if args.frames > 1:
            frame = frame.convert('RGBA')
            # Outside the LED topology: distinct transparent colors prevent GIF frame coalescing.
            frame.putpixel((0, 0), (index % 256, 0, 0, 0))
        images.append(frame)
        traces.append(f'{seconds:.3f} {entry.name}')
        delay = 1 / entry.options.fps
        delays.append(max(10, round(delay * 1000 / 10) * 10))
        seconds = round(seconds + delay, 9)
    images[0].save(args.output, save_all=True, append_images=images[1:], duration=delays, loop=0,
                   optimize=False, disposal=2)
    if args.trace:
        print('\n'.join(traces))
    print(f'{len(images)} frames rendered')
    return 0


if __name__ == '__main__':
    sys.exit(main())

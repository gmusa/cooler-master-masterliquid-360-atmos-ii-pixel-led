"""CLI for USB-free preview, bounded live runs, and persistent service mode."""
import argparse
import signal
import sys

from .config import ConfigError, ConfigStore
from .pipeline import Sequencer, render_frame
from .widget_plugins.animation import AnimationPlayback
from .widgets import registry


def _stop_service(_signum, _frame):
    raise KeyboardInterrupt


def main(argv=None):
    parser = argparse.ArgumentParser(prog='pixel-dashboard')
    parser.add_argument('mode', choices=['preview', 'live', 'serve'])
    parser.add_argument('--config', required=True)
    parser.add_argument('--frames', type=int, default=10)
    parser.add_argument('--output')
    parser.add_argument('--duration', type=float)
    parser.add_argument('--locked', action='store_true', help='preview the locked playlist')
    parser.add_argument('--palette', help='explicit generated Noctalia palette TOML path')
    parser.add_argument('--trace', action='store_true', help='print logical frame time and widget')
    args = parser.parse_args(argv)
    if args.mode in ('live', 'serve'):
        if args.mode == 'live' and (args.output is not None or args.duration is None or not 0 < args.duration <= 3600):
            parser.error('live requires --duration between 0 and 3600 and no --output')
        if args.mode == 'serve' and (args.output is not None or args.duration is not None):
            parser.error('serve requires no --duration or --output')
        try:
            from .live import run
            previous = None
            if args.mode == 'serve':
                previous = signal.getsignal(signal.SIGTERM)
                signal.signal(signal.SIGTERM, _stop_service)
            try:
                try:
                    run(args.config, args.duration, args.palette)
                except KeyboardInterrupt:
                    if args.mode != 'serve':
                        raise
            finally:
                if previous is not None:
                    signal.signal(signal.SIGTERM, previous)
        except (ConfigError, ValueError) as exc:
            parser.error(str(exc))
        except (OSError, RuntimeError, ImportError) as exc:
            print(f'pixel-dashboard {args.mode}: {exc}', file=sys.stderr)
            return 1
        return 0
    if args.output is None or args.duration is not None:
        parser.error('preview requires --output and no --duration')
    if not 1 <= args.frames <= 300:
        parser.error('frames must be between 1 and 300')
    try:
        store = ConfigStore(args.config)
        from .palette import PaletteStore
        palette = PaletteStore(args.palette) if args.palette else None
    except (ConfigError, ValueError) as exc:
        parser.error(str(exc))
    images = []
    delays = []
    traces = []
    seconds = 0.0
    playback = AnimationPlayback()
    for index in range(args.frames):
        store.poll()
        config = store.current
        assert config is not None  # constructor requires an initial valid config
        playlist = config.locked if args.locked else config.normal
        sequencer = Sequencer(playlist)
        entry, phase = sequencer.at_phase(seconds)
        # GIF stores each frame delay in a 16-bit centisecond field.
        if entry.options.fps < 0.01:
            parser.error('invalid fps')
        # Synthetic sample for the demo only; no sensors or USB are opened.
        sample = ({'temperature': 60} if entry.name == 'cpu' else
                  {'temperature': 60, 'usage': 70} if entry.name == 'gpu' else {})
        colors = palette.poll() if palette else None
        image = playback.render(config, entry, phase, int(seconds // sequencer.period), sample, seconds, colors)
        if image is None:
            widget = registry[entry.name]()
            if entry.name in ('cpu', 'gpu'):
                image = widget.render(sample, seconds, colors, phase=phase, duration=entry.options.duration)
            else:
                image = widget.render(sample, seconds, colors) if colors else widget.render(sample, seconds)
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

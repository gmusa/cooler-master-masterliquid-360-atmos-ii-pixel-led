"""Best-effort user-facing feedback; stderr is always the primary journal record."""
import shutil
import subprocess
import sys


def report_invalid(error):
    message = f'pixel-dashboard: invalid configuration: {error}'
    print(message, file=sys.stderr)
    if shutil.which('notify-send'):
        try:
            subprocess.run(['notify-send', '-t', '5000', 'Pixel dashboard configuration', message],
                           timeout=2, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.TimeoutExpired):
            pass

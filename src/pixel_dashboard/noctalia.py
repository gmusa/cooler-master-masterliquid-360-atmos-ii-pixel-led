"""Read-only Noctalia IPC lock-state reconciliation."""
import json
import subprocess


def locked_status():
    try:
        result = subprocess.run(['noctalia', 'msg', 'status'], capture_output=True,
                                text=True, timeout=1, check=True)
        value = json.loads(result.stdout)['locked']
        return value if isinstance(value, bool) else None
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError):
        return None

"""Read-only sensor adapters; absent metrics remain absent."""
import json
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class Sample:
    temperature: float | None = None
    usage: float | None = None
    fan_rpm: float | None = None


def _number(value):
    try:
        number = float(value)
        return number if 0 <= number < 100000 and number == number else None
    except (ValueError, TypeError):
        return None


def parse_cpu(text):
    try:
        sensor = json.loads(text).get('k10temp-pci-00c3', {}).get('Tctl', {})
        return Sample(temperature=_number(sensor.get('temp1_input')))
    except (ValueError, AttributeError, TypeError):
        return Sample()


def parse_gpu(text):
    try:
        row = next(line for line in text.splitlines() if line.strip())
        parts = [part.strip() for part in row.split(',')]
        if len(parts) != 4 or 'RTX 5070' not in parts[0]:
            return Sample()
        return Sample(_number(parts[1]), _number(parts[2]))
    except StopIteration:
        return Sample()


def sample_cpu():
    try:
        result = subprocess.run(['sensors', '-j'], capture_output=True, text=True, timeout=2, check=False)
        return parse_cpu(result.stdout)
    except (OSError, subprocess.TimeoutExpired):
        return Sample()


def sample_gpu():
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,temperature.gpu,utilization.gpu,fan.speed',
                                 '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=2, check=False)
        # nvidia-smi fan.speed is percentage, not RPM: never relabel it.
        parsed = parse_gpu(result.stdout)
        return Sample(parsed.temperature, parsed.usage)
    except (OSError, subprocess.TimeoutExpired):
        return Sample()

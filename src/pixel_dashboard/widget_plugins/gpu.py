"""GPU sensor widget."""
from .gauge import Gauge


class GPU(Gauge):
    color = 'magenta'
    label = 'GPU'

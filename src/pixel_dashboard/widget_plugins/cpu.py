"""CPU sensor widget."""
from .gauge import Gauge


class CPU(Gauge):
    color = 'cyan'
    label = 'CPU'

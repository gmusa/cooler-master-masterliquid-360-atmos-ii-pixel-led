"""Compatibility exports and fixed registry for built-in widgets."""
from .widget_plugins.animation import Animation
from .widget_plugins.clock import Clock
from .widget_plugins.cpu import CPU
from .widget_plugins.date import Date
from .widget_plugins.gauge import Gauge
from .widget_plugins.gpu import GPU

registry = {'clock': Clock, 'date': Date, 'cpu': CPU, 'gpu': GPU, 'animation': Animation}

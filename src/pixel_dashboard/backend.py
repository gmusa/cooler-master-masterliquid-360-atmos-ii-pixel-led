"""Explicit HID backend selection, never imported by the USB-free preview."""
import importlib


def create_display():
    """Bind cm-pixel's device module to hidraw before opening the display."""
    hidraw = open_hidraw_backend()
    device = importlib.import_module('cmpixel.device')
    device.__dict__['hid'] = hidraw
    return device.PixelDisplay()


def open_hidraw_backend():
    """Choose hidraw explicitly; the hidapi distribution also exposes `hid`."""
    return importlib.import_module('hidraw')

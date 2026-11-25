"""Explicit HID backend selection, never imported by the USB-free preview."""
import importlib


def open_hidraw_backend():
    """Choose hidraw explicitly; the hidapi distribution also exposes `hid`."""
    return importlib.import_module('hidraw')

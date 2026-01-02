"""
Mock EDMC modules for standalone testing
"""
import sys
from unittest.mock import MagicMock
from types import SimpleNamespace


class MockConfigObject:
    """Mock EDMC config object"""
    def get_str(self, key, default=""):
        return default

    def get_int(self, key, default=0):
        return default

    def get_bool(self, key, default=False):
        return default

    def get_list(self, key, default=None):
        return default if default is not None else []

    def set(self, key, value):
        pass


# Create mock config module
config_module = SimpleNamespace()
config_module.appname = "EDMarketConnector"
config_module.config = MockConfigObject()


# Create mock Tkinter
class MockStringVar:
    def __init__(self, value="", **kwargs):
        self._value = value

    def get(self):
        return self._value

    def set(self, value):
        self._value = value


class MockBooleanVar:
    def __init__(self, value=False, **kwargs):
        self._value = value

    def get(self):
        return self._value

    def set(self, value):
        self._value = value


class MockIntVar:
    def __init__(self, value=0, **kwargs):
        self._value = value

    def get(self):
        return self._value

    def set(self, value):
        self._value = value


tkinter_module = SimpleNamespace()
tkinter_module.StringVar = MockStringVar
tkinter_module.BooleanVar = MockBooleanVar
tkinter_module.IntVar = MockIntVar
tkinter_module.Tk = MagicMock
tkinter_module.Frame = MagicMock
tkinter_module.Label = MagicMock
tkinter_module.Button = MagicMock
tkinter_module.Entry = MagicMock
tkinter_module.Text = MagicMock
tkinter_module.Scrollbar = MagicMock
tkinter_module.Canvas = MagicMock
tkinter_module.Toplevel = MagicMock
tkinter_module.W = "w"
tkinter_module.E = "e"
tkinter_module.N = "n"
tkinter_module.S = "s"
tkinter_module.BOTH = "both"
tkinter_module.LEFT = "left"
tkinter_module.RIGHT = "right"
tkinter_module.TOP = "top"
tkinter_module.BOTTOM = "bottom"
tkinter_module.X = "x"
tkinter_module.Y = "y"
tkinter_module.VERTICAL = "vertical"
tkinter_module.HORIZONTAL = "horizontal"
tkinter_module.END = "end"
tkinter_module.NORMAL = "normal"
tkinter_module.DISABLED = "disabled"

# Install mocks before imports
sys.modules['tkinter'] = tkinter_module
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['config'] = config_module
sys.modules['EDMCLogging'] = MagicMock()
sys.modules['theme'] = MagicMock()
sys.modules['ttkHyperlinkLabel'] = MagicMock()

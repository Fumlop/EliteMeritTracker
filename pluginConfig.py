import json
import tkinter as tk
from config import config

class ConfigPlugin:
    def __init__(self):
        self.version = 'v0.4.200.1.100'
        self.loadConfig()

    def getTextCopy(self):
        return "@Leadership earned @MeritsValue merits in @System, @CPControlling, @CPOpposition"
    
    def getCacheTime(self):
        return 43200
    
    def old(self):
        self.never = True
    
    def loadConfig(self):
        self.power_info_width = int(config.get_str("power_info_width") or "1280")
        self.power_info_height = int(config.get_str("power_info_height") or "800")
        self.cacheTime = int(config.get_str("cacheTime") or self.getCacheTime())
        self.copyText = tk.StringVar(value=config.get_str("copyText") or self.getTextCopy())
        self.reportOnFSDJump = tk.BooleanVar(value=config.get_bool("reportOnFSDJump") or False)
        self.discordHook = tk.StringVar(value=config.get_str("discordHook") or "")
        self.reportSave = config.get_bool("reportSave") or True
        self.never = config.get_bool("never") or False

    def dumpConfig(self):
        config.set("power_info_width", str(self.power_info_width))
        config.set("power_info_height", str(self.power_info_height))
        config.set("cacheTime", str(self.cacheTime))
        config.set("copyText", str(self.copyText.get()))
        config.set("reportOnFSDJump", bool(self.reportOnFSDJump.get()))
        config.set("discordHook", str(self.discordHook.get()))
        config.set("reportSave", bool(self.reportSave))
        config.set("never", bool(self.never))
        #config.set("keepHistory", str(self.keepHistory, 90))

class ConfigEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, tk.StringVar) or isinstance(o, tk.BooleanVar):
            return o.get()
        if isinstance(o, ConfigPlugin):
            config_dict = o.__dict__.copy()
            config_dict.pop('version', None)  # Remove version from config
            return config_dict
        if isinstance(o, ConfigPlugin):
            return o.__dict__
        return super().default(o)


configPlugin = ConfigPlugin()
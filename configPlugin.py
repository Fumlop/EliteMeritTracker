import logging
from config import config, appname
import json
import os

plugin_name = os.path.basename(os.path.dirname(__file__))

logger = logging.getLogger(f'{appname}.{plugin_name}')

class ConfigPlugin:
    def __init__(self):
        self.power_info_width: int = int(config.get_str("power_info_width") or "1280")
        self.power_info_height: int = int(config.get_str("power_info_height") or "800")
        self.cacheTime: int = int(config.get_str("cacheTime") or self.getCacheTime())
        self.copyText: str = config.get_str("copyText") or self.getTextCopy()
        self.reportOnFSDJump: bool = config.get_bool("reportOnFSDJump") or False
        self.discordHook: str = config.get_str("discordHook") or ""
        self.reportSave: bool = config.get_bool("reportSave") or True
        self.never: bool = config.get_bool("never") or False
        self.keepHistory =  min(int(config.get_str("keepHistory") or 90), 90)

    def getTextCopy(self):
        return "@Leadership earned @MeritsValue merits in @System, @CPControlling, @CPOpposition"
    
    def getCacheTime(self):
        return "43200"
    
    def old(self):
        self.never = True
        
    def dumpConfig(self):
        config.set("power_info_width", str(self.power_info_width))
        config.set("power_info_height", str(self.power_info_height))
        config.set("cacheTime", str(self.cacheTime))
        config.set("copyText", str(self.copyText))
        config.set("reportOnFSDJump", bool(self.reportOnFSDJump))
        config.set("discordHook", str(self.discordHook))
        config.set("reportSave", bool(self.reportSave))
        config.set("never", bool(self.never))
        config.set("keepHistory", str(self.keepHistory, 90))

class ConfigEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ConfigPlugin):
            return o.__dict__
        return super().default(o)

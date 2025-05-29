import requests
from log import logger, plugin_name
from configPlugin import configPlugin, ConfigEncoder

class Report:
    def send_to_discord(self, message: str) -> bool:
        webhook_url = getattr(configPlugin, "discordHook", None)
        if not isinstance(webhook_url, str) or not webhook_url.strip():
            return False

        payload = {"content": str(message)}

        try:
            response = requests.post(webhook_url, json=payload, timeout=5)
            if response.status_code in (200, 204):
                return True
            return False
        except requests.exceptions.RequestException as e:
            return False
        except Exception as e:
            return False

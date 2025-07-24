import requests
from log import logger, plugin_name
from pluginConfig import configPlugin, ConfigEncoder

class Report:
    def send_to_discord(self, message: str) -> bool:
        webhook_url = getattr(configPlugin, "discordHook", None)
        if not isinstance(webhook_url, str) or not webhook_url.strip():
            return False

        payload = {"content": str(message)}

        try:
            response = requests.post(webhook_url, json=payload, timeout=5)
            if response.status_code in (200, 204):
                from log import logger
                logger.info(f"Discord report sent successfully: {len(str(message))} chars")
                return True
            else:
                from log import logger
                logger.warning(f"Discord webhook failed with status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            from log import logger
            logger.warning(f"Discord webhook request failed: {type(e).__name__}")
            return False
        except Exception as e:
            from log import logger
            logger.error(f"Unexpected error in Discord webhook: {type(e).__name__}")
            return False

report = Report()
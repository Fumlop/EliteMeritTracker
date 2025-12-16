import requests
from core.logging import logger
from core.config import configPlugin

class Report:
    def send_to_discord(self, message: str) -> bool:
        """Send message to Discord webhook"""
        webhook_url = getattr(configPlugin, "discordHook", None)
        if not webhook_url:
            return False
            
        # Validate webhook URL format
        if not isinstance(webhook_url, str) or not webhook_url.strip():
            return False
            
        if not webhook_url.startswith(('http://', 'https://')):
            logger.warning("Invalid Discord webhook URL format")
            return False

        payload = {"content": str(message)}

        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            success = response.status_code in (200, 204)
            
            if success:
                logger.info(f"Discord report sent: {len(str(message))} chars")
            else:
                logger.warning(f"Discord webhook failed: HTTP {response.status_code}")
            
            return success
            
        except requests.exceptions.Timeout:
            logger.warning("Discord webhook timed out")
            return False
        except requests.exceptions.ConnectionError:
            logger.warning("Discord webhook connection failed") 
            return False
        except requests.exceptions.RequestException as e:
            logger.warning(f"Discord webhook request error: {type(e).__name__}")
            return False
        except Exception as e:
            logger.error(f"Unexpected Discord webhook error: {type(e).__name__}")
            return False

report = Report()
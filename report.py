from imports import *

class Report:
    def __init__(self):
        self.me = True
        
    def send_to_discord(self, message: str) -> bool:
        webhook_url = getattr(configPlugin, "discordHook", None)

        if not webhook_url:
            logger.error("Webhook-URL nicht konfiguriert.")
            return False

        payload = {
            "content": message
        }

        try:
            response = requests.post(webhook_url, json=payload, timeout=5)
            if response.status_code in [200, 204]:
                logger.info("Nachricht erfolgreich an Discord gesendet.")
                return True
            else:
                logger.error(f"Discord-Fehler: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.exception("Fehler beim Senden an Discord:")
            return False
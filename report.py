import json
import requests
from imports import logger


class Report:
    def send_to_discord(self, message: str) -> bool:
        webhook_url = getattr(configPlugin, "discordHook", None)
        if not isinstance(webhook_url, str) or not webhook_url.strip():
            logger.error("Webhook-URL nicht konfiguriert oder ungültig.")
            return False

        payload = {"content": str(message)}

        try:
            response = requests.post(webhook_url, json=payload, timeout=5)
            if response.status_code in (200, 204):
                logger.info("Nachricht erfolgreich an Discord gesendet.")
                return True
            logger.error(f"Discord-Fehler: {response.status_code} - {response.text}")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Netzwerkfehler beim Senden an Discord: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unbekannter Fehler beim Senden an Discord: {e}")
            return False

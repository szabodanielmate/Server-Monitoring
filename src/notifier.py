import time
import httpx
from src.config import Config
from src.logger import setup_logger

logger = setup_logger()


class AlertNotifier:
    def __init__(self):
        self.last_alert_times = {}

    def _should_send(self, alert_key: str) -> bool:
        """Ellenőrzi, hogy letelt-e a cooldown az adott riasztástípusra."""
        now = time.time()
        last_time = self.last_alert_times.get(alert_key, 0)
        if now - last_time >= Config.ALERT_COOLDOWN:
            self.last_alert_times[alert_key] = now
            return True
        return False

    def send_alert(self, metric_name: str, current_value: float, threshold: float):
        """Riasztás küldése az aktív csatornákra (Discord / Telegram)."""
        alert_key = metric_name.lower()
        if not self._should_send(alert_key):
            return

        message = (
            f"⚠️ **SZERVER RIASZTÁS!**\n"
            f"Metrika: **{metric_name}**\n"
            f"Érték: **{current_value:.1f}%** (Küszöb: {threshold:.1f}%)\n"
            f"Idő: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        logger.warning(f"Riasztás aktiválva: {metric_name} ({current_value:.1f}% >= {threshold:.1f}%)")

        # 1. Discord Webhook küldés
        if Config.DISCORD_WEBHOOK_URL:
            self._send_discord(message)

        # 2. Telegram Bot küldés
        if Config.TELEGRAM_BOT_TOKEN and Config.TELEGRAM_CHAT_ID:
            self._send_telegram(message)

    def _send_discord(self, message: str):
        payload = {"content": message}
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.post(Config.DISCORD_WEBHOOK_URL, json=payload)
                if res.status_code not in (200, 204):
                    logger.error(f"Discord küldés sikertelen: HTTP {res.status_code}")
        except Exception as e:
            logger.error(f"Hiba a Discord üzenet küldésekor: {e}")

    def _send_telegram(self, message: str):
        # A Markdown csillagozást egyszerűsítjük a Telegramnak
        clean_msg = message.replace("**", "*")
        url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": Config.TELEGRAM_CHAT_ID,
            "text": clean_msg,
            "parse_mode": "Markdown",
        }
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.post(url, json=payload)
                if res.status_code != 200:
                    logger.error(f"Telegram küldés sikertelen: HTTP {res.status_code}")
        except Exception as e:
            logger.error(f"Hiba a Telegram üzenet küldésekor: {e}")
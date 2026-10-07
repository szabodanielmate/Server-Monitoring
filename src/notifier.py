import socket
import time
import httpx
from src.config import Config
from src.logger import setup_logger

logger = setup_logger()


class AlertNotifier:
    def __init__(self):
        self.hostname = socket.gethostname()
        self.last_alert_times = {}     # Cooldown időpontok követése
        self.breach_start_times = {}    # Mikor kezdődött a folyamatos küszöbérték-átlépés
        self.alerted_states = {}        # Volt-e már kiküldött alert az aktuális hibaperiódusban

    def check_metric(self, metric_name: str, current_value: float, threshold: float):
        """
        Ellenőrzi a metrikát:
        - Ha normális: visszaállítja az időzítőt.
        - Ha küszöb felett van: elindítja az időmérést, és csak ALERT_DURATION idő után riaszt.
        """
        now = time.time()
        key = metric_name.lower()

        # 1. Normál tartományban van: hibaállapot törlése
        if current_value < threshold:
            if key in self.breach_start_times:
                del self.breach_start_times[key]
            if key in self.alerted_states:
                del self.alerted_states[key]
            return

        # 2. Küszöbérték átlépése
        if key not in self.breach_start_times:
            self.breach_start_times[key] = now
            logger.info(f"Metrika küszöb felett: {metric_name} ({current_value:.1f}% >= {threshold:.1f}%). Figyelés indítva...")
            return

        # 3. Fennállás idejének ellenőrzése
        duration = now - self.breach_start_times[key]

        if duration >= Config.ALERT_DURATION:
            last_alert = self.last_alert_times.get(key, 0)
            already_alerted = self.alerted_states.get(key, False)

            if not already_alerted or (now - last_alert >= Config.ALERT_COOLDOWN):
                self._trigger_alert(metric_name, current_value, threshold, int(duration))
                self.last_alert_times[key] = now
                self.alerted_states[key] = True

    def _trigger_alert(self, metric_name: str, current_value: float, threshold: float, duration_sec: int):
        """Üzenet formázása és elküldése a Hostname feltüntetésével."""
        message = (
            f"🚨 **TARTÓS SZERVER TERHELÉS!**\n"
            f"🖥️ Szerver: **{self.hostname}**\n"
            f"📊 Metrika: **{metric_name}**\n"
            f"⚠️ Jelenlegi érték: **{current_value:.1f}%** (Küszöb: {threshold:.1f}%)\n"
            f"⏳ Fennállás ideje: **legalább {duration_sec} másodperce folyamatosan**\n"
            f"🕒 Időbélyeg: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        logger.warning(f"[{self.hostname}] Riasztás kiküldve: {metric_name} ({current_value:.1f}% >= {threshold:.1f}%, tartam: {duration_sec}s)")

        if Config.DISCORD_WEBHOOK_URL:
            self._send_discord(message)

        if Config.TELEGRAM_BOT_TOKEN and Config.TELEGRAM_CHAT_ID:
            self._send_telegram(message)

    def _send_discord(self, message: str):
        payload = {"content": message}
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.post(Config.DISCORD_WEBHOOK_URL, json=payload)
                if res.status_code not in (200, 204):
                    logger.error(f"Discord hiba: HTTP {res.status_code}")
        except Exception as e:
            logger.error(f"Hiba a Discord küldés során: {e}")

    def _send_telegram(self, message: str):
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
                    logger.error(f"Telegram hiba: HTTP {res.status_code}")
        except Exception as e:
            logger.error(f"Hiba a Telegram küldés során: {e}")
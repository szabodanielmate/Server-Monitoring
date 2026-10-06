import os
from pathlib import Path
from dotenv import load_dotenv

# Projekt gyökérkönyvtára a scripthez képest
BASE_DIR = Path(__file__).resolve().parent.parent

# .env betöltése
load_dotenv(BASE_DIR / ".env")


class Config:
    # Küszöbértékek (%)
    CPU_THRESHOLD: float = float(os.getenv("CPU_THRESHOLD", 85.0))
    RAM_THRESHOLD: float = float(os.getenv("RAM_THRESHOLD", 90.0))
    DISK_THRESHOLD: float = float(os.getenv("DISK_THRESHOLD", 90.0))

    # Mintavételezési időköz (másodperc)
    CHECK_INTERVAL: int = int(os.getenv("CHECK_INTERVAL", 3))

    # Értesítések
    DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    # Docker figyelés kapcsoló
    ENABLE_DOCKER: bool = os.getenv("ENABLE_DOCKER", "false").lower() in ("true", "1", "yes")

    # Log fájl pontos útvonala
    LOG_FILE_PATH: Path = BASE_DIR / "server_monitor.log"

    # Hány másodperc szünet legyen két riasztás között (spam védelem)
    ALERT_COOLDOWN: int = int(os.getenv("ALERT_COOLDOWN", 300))
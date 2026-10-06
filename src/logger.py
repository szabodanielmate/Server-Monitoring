import logging
from logging.handlers import RotatingFileHandler
from src.config import Config


def setup_logger() -> logging.Logger:
    """Beállítja és visszaadja a fájlba forgó loggert."""
    logger = logging.getLogger("server_monitor")
    logger.setLevel(logging.INFO)

    # Ha már korábban hozzáadtunk handlert, ne duplázzuk meg a bejegyzéseket
    if not logger.handlers:
        # Max 5 MB méretű logfájl, legfeljebb 3 archív fájl megtartásával
        file_handler = RotatingFileHandler(
            Config.LOG_FILE_PATH,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8"
        )

        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
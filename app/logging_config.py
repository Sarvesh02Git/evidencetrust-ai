
import logging
from logging.handlers import RotatingFileHandler

from app.config import LOGS_DIR


def configure_logging() -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = RotatingFileHandler(
        LOGS_DIR / "evidencetrust.log",
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Avoid adding duplicate handlers if configuration is called again.
    if not root_logger.handlers:
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    else:
        for handler in root_logger.handlers:
            handler.setFormatter(formatter)


logger = logging.getLogger("evidencetrust")

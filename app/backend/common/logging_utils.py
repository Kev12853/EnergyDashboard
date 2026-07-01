import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger(name: str) -> logging.Logger:

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    PROJECT_ROOT = Path(__file__).resolve().parents[3]

    log_dir = PROJECT_ROOT / "logs"

    log_dir.mkdir(exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    file_handler = RotatingFileHandler(
        log_dir / f"{name}.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )

    logger.warning(f"Logging to {file_handler.baseFilename}")

    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.propagate = False

    return logger
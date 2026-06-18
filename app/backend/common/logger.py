# app/backend/common/logger.py

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# =====================================================
# Log location
# =====================================================

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "EnergyDashboard.log"

# =====================================================
# Root logger
# =====================================================

root_logger = logging.getLogger()

root_logger.setLevel(logging.DEBUG)

# Remove existing handlers
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)
    handler.close()

# =====================================================
# File handler
# =====================================================

file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=5 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8",
)

file_handler.setLevel(logging.DEBUG)

file_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
)

# =====================================================
# Console handler
# =====================================================

console_handler = logging.StreamHandler()

console_handler.setLevel(logging.ERROR)

console_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
)

# =====================================================
# Install handlers
# =====================================================

root_logger.addHandler(file_handler)

root_logger.addHandler(console_handler)

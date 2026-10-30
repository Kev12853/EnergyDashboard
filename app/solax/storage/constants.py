"""Legacy SolaX poller and storage settings retained for older code paths.

This file contains a second set of Modbus defaults and cloud API credential /
plant-identifier variables; their values are deliberately not repeated in
module documentation. Confirm active callers before using these legacy
settings in a new service, since the current poller configuration is in
``app.config.solax_config``. Importing this module also creates its log
 directory as a side effect.
"""

from pathlib import Path

# =========================================================
# CONNECTION
# =========================================================

INVERTER_IP = "192.168.1.67"  # legacy Modbus TCP host

MODBUS_PORT = 502  # legacy Modbus TCP port

DEVICE_ID = 1  # Modbus unit/device identifier

# =========================================================
# POLLING
# =========================================================

POLL_INTERVAL = 20  # legacy polling interval, seconds

# =========================================================
# REGISTER BLOCK
# =========================================================

RUNTIME_BLOCK_START = 20  # first register in the legacy runtime block

RUNTIME_BLOCK_COUNT = 20  # number of consecutive runtime registers

# =========================================================
# LOGGING
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[2]  # repository/application base

LOG_DIR = BASE_DIR / "logs"  # legacy log output directory

LOG_DIR.mkdir(exist_ok=True)

CSV_PATH = (  # register-scan output path
    LOG_DIR / f"registers_"
    f"{RUNTIME_BLOCK_START}_"
    f"{RUNTIME_BLOCK_START + RUNTIME_BLOCK_COUNT - 1}.csv"
)

# =========================================================
# SOLAX CLOUD API
# =========================================================

SOLAX_TOKEN_ID = "202307140243593619522312"

SOLAX_SERIAL_NUMBER = "SVKQDUUJLK"
# https://www.solaxcloud.com:9443/proxy/api/getRealtimeInfo.do?tokenId={202307140243593619522312}&sn={SVKQDUUJLK}

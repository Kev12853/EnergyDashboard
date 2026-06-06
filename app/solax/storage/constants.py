from pathlib import Path

# =========================================================
# CONNECTION
# =========================================================

INVERTER_IP = "192.168.1.66"

MODBUS_PORT = 502

DEVICE_ID = 1

# =========================================================
# POLLING
# =========================================================

POLL_INTERVAL = 20

# =========================================================
# REGISTER BLOCK
# =========================================================

RUNTIME_BLOCK_START = 20

RUNTIME_BLOCK_COUNT = 20

# =========================================================
# LOGGING
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

LOG_DIR = BASE_DIR / "logs"

LOG_DIR.mkdir(exist_ok=True)

CSV_PATH = (
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

# =========================================================
# UPDATED LOGGER
# =========================================================
#
# poller/solax/cloud_api/logger.py
#
# =========================================================

"""
SolaX Cloud Telemetry Logger
============================

Purpose
-------
Continuously polls the SolaX Cloud API and stores
normalized telemetry snapshots into SQLite.

Polling
-------
Poll interval: 30 seconds

Cloud update cadence is typically ~5 minutes.

Duplicate snapshots are suppressed using upload_time.
"""

import datetime
import time

from app.solax.cloud_api.cloud_client import (
    SolaxCloudClient,
)
from app.solax.storage.constants import (
    SOLAX_TOKEN_ID,
    SOLAX_SERIAL_NUMBER,
)
from app.solax.storage.storage_repository import (
    insert_snapshot,
)
from app.solax.storage.schema import (
    create_schema,
)

# =========================================================
# DATABASE
# =========================================================

create_schema()

# =========================================================
# CLIENT
# =========================================================

client = SolaxCloudClient(
    token_id=SOLAX_TOKEN_ID,
    serial_number=SOLAX_SERIAL_NUMBER,
)

# =========================================================
# MAIN LOOP
# =========================================================

print("Starting SolaX cloud logger...")

last_upload_time = None

try:
    while True:
        try:
            snapshot = client.get_snapshot()

            # =============================================
            # DUPLICATE SUPPRESSION
            # =============================================

            if snapshot.upload_time != last_upload_time:
                insert_snapshot(snapshot)

                last_upload_time = snapshot.upload_time

                print(f"Logged: {snapshot.upload_time}")

            else:
                print("No new inverter update")

        except Exception as e:
            print(f"[{datetime.datetime.now()}] Logger error: {e}")

        #
        # Poll interval
        #

        time.sleep(30)

except KeyboardInterrupt:
    print("\nStopping logger...")

from pprint import pprint

from app.solax.storage.storage_repository import (
    TelemetryRepository,
)


repository = TelemetryRepository()


# =====================================================
# LATEST SNAPSHOT
# =====================================================

latest = repository.get_latest_snapshot()

print("\nLATEST:\n")

pprint(dict(latest))


# =====================================================
# 1 MINUTE HISTORY
# =====================================================

history = repository.get_1m_history(
    start="2026-05-28 00:00:00",
    end="2026-05-29 00:00:00",
)

print("\n1M HISTORY:\n")

for row in history[:5]:
    pprint(dict(row))

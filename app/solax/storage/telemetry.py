"""Provide a legacy high-level facade for obtaining SolaX telemetry snapshots. It delegates polling/parsing to lower layers and is read-only with respect to the inverter."""

from datetime import datetime

from app.solax.storage.constants import (
    RUNTIME_BLOCK_COUNT,
    RUNTIME_BLOCK_START,
)
from app.solax.storage.parser import SolaxParser
from app.solax.telemetry.models import PowerFlowSnapshot


class SolaxTelemetryService:
    """Legacy telemetry facade that composes polling and storage helpers; it is read-oriented and does not own inverter control."""
    def __init__(self, client):

        self.client = client

    def get_live_snapshot(self):
        """Poll and return the current snapshot through the wrapped telemetry service; communication failures propagate."""
        block = self.client.read_block(
            start=RUNTIME_BLOCK_START,
            count=RUNTIME_BLOCK_COUNT,
        )

        if block is None:
            return PowerFlowSnapshot(timestamp=datetime.now())

        parsed = SolaxParser.parse_runtime_block(block)

        snapshot = SolaxParser.build_snapshot(parsed)

        snapshot.timestamp = datetime.now()
        snapshot.raw_runtime_block = block

        return snapshot

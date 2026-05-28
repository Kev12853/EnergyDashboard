from datetime import datetime

from services.solax.constants import (
    RUNTIME_BLOCK_START,
    RUNTIME_BLOCK_COUNT,
)
from services.solax.models import PowerFlowSnapshot
from services.solax.parser import SolaxParser


class SolaxTelemetryService:

    def __init__(self, client):

        self.client = client

    def get_live_snapshot(self):
        block = self.client.read_block(
            start=RUNTIME_BLOCK_START,
            count=RUNTIME_BLOCK_COUNT,
        )

        if block is None:

            return PowerFlowSnapshot(
                timestamp=datetime.now()
            )

        parsed = SolaxParser.parse_runtime_block(block)

        snapshot = SolaxParser.build_snapshot(parsed)

        snapshot.timestamp = datetime.now()
        snapshot.raw_runtime_block = block

        return snapshot
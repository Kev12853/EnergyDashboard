"""Parse raw SolaX register blocks into typed telemetry snapshots. This conversion layer interprets readings but does not store them or control the inverter."""

from app.solax.telemetry.models import PowerFlowSnapshot


class SolaxParser:
    """
    Converts raw Modbus blocks into normalized telemetry.

    IMPORTANT
    ---------
    All mappings are provisional until validated
    against live inverter telemetry.
    """

    @staticmethod
    def parse_runtime_block(registers: list[int]) -> dict:

        #
        # Block assumptions
        #
        # start register = 40
        #
        # absolute register:
        #   40 + index
        #

        """Decode a raw Modbus register mapping into named runtime values; missing or malformed register data may raise during lookup/conversion."""
        def reg(index, default=None):

            """Read and convert one named value from the register mapping, applying the parser’s configured scaling when present."""
            try:
                return registers[index]

            except IndexError:
                return default

        parsed = {
            #
            # Strong candidates from live validation
            #
            "grid_voltage_v": reg(8, 0) / 10,
            "output_voltage_v": reg(9, 0) / 10,
            #
            # Provisional
            #
            "battery_power_w": reg(13),
            "load_power_w": reg(16),
            "battery_soc_pct": reg(10),
        }

        return parsed

    @staticmethod
    def build_snapshot(parsed: dict) -> PowerFlowSnapshot:

        """Build a PowerFlowSnapshot from parsed register values without database or network side effects."""
        return PowerFlowSnapshot(
            timestamp=None,
            battery_soc_pct=parsed.get("battery_soc_pct"),
            battery_power_w=parsed.get("battery_power_w"),
            load_power_w=parsed.get("load_power_w"),
            grid_voltage_v=parsed.get("grid_voltage_v"),
            output_voltage_v=parsed.get("output_voltage_v"),
        )

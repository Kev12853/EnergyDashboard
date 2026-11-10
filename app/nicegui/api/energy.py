
"""Live energy data API for external displays."""

from nicegui import app

from app.connections.connection import get_connection
from app.solax.storage.solax_repository import TelemetryRepository


@app.get("/api/energy/live")
def get_live_energy():
    """Return the latest available energy telemetry as JSON."""

    connection = get_connection()

    try:
        repository = TelemetryRepository(connection)
        snapshot = repository.get_latest_snapshot()

        if snapshot is None:
            return {
                "status": "no_data",
                "message": "No telemetry is available",
            }

        return {
            "status": "ok",
            "timestamp": snapshot["timestamp"],
            "source": snapshot["telemetry_source"],
            "solar_w": snapshot["solar_w"],
            "consumption_w": snapshot["consumption_w"],
            "battery_w": snapshot["battery_w"],
            "battery_soc_pct": snapshot["battery_soc_pct"],
            "grid_w": snapshot["grid_w"],
        }

    finally:
        connection.close()

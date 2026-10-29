
import os
import sqlite3
from datetime import timezone, datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException

app = FastAPI(title="Home Energy API")

# Configure ENERGY_DB_PATH to override this default.
PROJECT_DIR = Path(__file__).resolve().parent
DB_PATH = Path(
    os.environ.get(
        "ENERGY_DB_PATH",
        str(PROJECT_DIR / "data" / "energy_dashboard.db"),
    )
).expanduser().resolve()


def get_latest_telemetry():
    if not DB_PATH.is_file():
        raise HTTPException(
            status_code=500,
            detail=f"Database not found: {DB_PATH}",
        )

    # Open SQLite in read-only mode.
    uri = DB_PATH.as_uri() + "?mode=ro"

    try:
        with sqlite3.connect(uri, uri=True, timeout=5) as conn:
            conn.row_factory = sqlite3.Row

            row = conn.execute("""
                SELECT
                    timestamp,
                    solar_w,
                    battery_w,
                    consumption_w,
                    grid_w,
                    battery_soc_pct,
                    telemetry_source
                FROM telemetry_snapshots
                ORDER BY timestamp DESC
                LIMIT 1
            """).fetchone()

    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {exc}",
        ) from exc

    if row is None:
        raise HTTPException(
            status_code=503,
            detail="No telemetry snapshots available",
        )
    timestamp_text = row["timestamp"]

    try:
        recorded_at = datetime.fromisoformat(timestamp_text)

        if recorded_at.tzinfo is None:
            # Existing naive timestamps are assumed to be local time.
            recorded_at = recorded_at.astimezone()

        age_seconds = max(
            0,
            int(
                (
                    datetime.now(timezone.utc)
                    - recorded_at.astimezone(timezone.utc)
                ).total_seconds()
            ),
        )
    except (ValueError, TypeError):
        age_seconds = None

    return {
        "timestamp": row["timestamp"],
        "solar_kw": (row["solar_w"] or 0) / 1000,
        "battery_kw": (row["battery_w"] or 0) / 1000,
        "house_kw": (row["consumption_w"] or 0) / 1000,
        "grid_kw": (row["grid_w"] or 0) / 1000,
        "battery_percent": row["battery_soc_pct"],
        "source": row["telemetry_source"],
        "age_seconds": age_seconds,
        "is_stale": age_seconds is None or age_seconds > 120,
    }


@app.get("/api/energy")
def get_energy():
    return get_latest_telemetry()


@app.get("/health")
def health():
    return {"status": "ok"}

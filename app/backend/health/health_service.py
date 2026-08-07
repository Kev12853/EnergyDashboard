"""Compatibility API for the canonical system-health service."""

from app.backend.services.system_health_service import get_system_health


def get_health(repo):
    """Return the legacy health mapping using canonical health evaluation."""
    latest = repo.get_latest_snapshot()
    latest_time = None if latest is None else latest["timestamp"]
    system_health = get_system_health(
        last_snapshot_time=latest_time,
        last_successful_poll=latest_time,
    )

    periods = repo.get_periods()
    enabled = sum(1 for period in periods if period.enabled)
    inverter = (
        {"status": "error", "message": "Offline"}
        if latest is None
        else {"status": "healthy", "message": latest["work_mode"]}
    )

    return {
        "poller": {
            "status": system_health.poller_status.value,
            "message": system_health.data_age_text,
        },
        "inverter": inverter,
        "automation": {"status": "healthy", "message": f"{enabled} enabled periods"},
        "database": {"status": "healthy", "message": "SQLite operational"},
        "overall": {
            "status": system_health.overall_status.value,
            "message": "System status",
        },
    }

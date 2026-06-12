from datetime import datetime


def get_health(repo):

    health = {}

    # ---------------------------------
    # Poller
    # ---------------------------------

    latest = repo.get_latest_snapshot()

    if latest is None:

        health["poller"] = {
            "status": "error",
            "message": "No telemetry available",
        }

    else:

        latest_time = latest["timestamp"]

        if isinstance(latest_time, str):
            latest_time = datetime.fromisoformat(latest_time)

        age_minutes = (
            datetime.now() - latest_time
        ).total_seconds() / 60

        if age_minutes < 5:
            status = "healthy"

        elif age_minutes < 30:
            status = "warning"

        else:
            status = "error"

        health["poller"] = {
            "status": status,
            "message": f"{age_minutes:.1f} minutes old",
        }

    # ---------------------------------
    # Inverter
    # ---------------------------------

    if latest:

        health["inverter"] = {
            "status": "healthy",
            "message": latest["work_mode"],
        }

    else:

        health["inverter"] = {
            "status": "error",
            "message": "Offline",
        }

    # ---------------------------------
    # Automation
    # ---------------------------------

    periods = repo.get_periods()

    enabled = sum(
        1
        for p in periods
        if p.enabled
    )

    health["automation"] = {
        "status": "healthy",
        "message": f"{enabled} enabled periods",
    }

    # ---------------------------------
    # Database
    # ---------------------------------

    health["database"] = {
        "status": "healthy",
        "message": "SQLite operational",
    }

    # ---------------------------------
    # Overall
    # ---------------------------------

    states = [
        x["status"]
        for x in health.values()
    ]

    if "error" in states:
        overall = "error"

    elif "warning" in states:
        overall = "warning"

    else:
        overall = "healthy"

    health["overall"] = {
        "status": overall,
        "message": "System status",
    }

    return health
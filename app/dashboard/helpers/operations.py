from app.backend.services.system_health_service import HealthStatus
from app.dashboard.helpers.format_data import format_data_age

POWER_THRESHOLD_W = 300

def get_current_state(
    latest,
    health,
):

    #
    # Don't pretend stale telemetry is live.
    #

    if health.overall_status != HealthStatus.OPERATIONAL:

        age = health.data_age_text

        return {

            "work_mode": "Last known state",

            "status_icon": "⚫",

            "status_text":
                f"No telemetry ({age} old)",

        }

    #
    # Live telemetry
    #

    work_mode = latest["work_mode"]

    solar = latest.get("pv_power_w", 0)
    battery = latest.get("battery_power_w", 0)
    grid = latest.get("grid_power_w", 0)

    battery_soc = latest.get(
        "battery_soc_pct",
        None,
    )

    #
    # Operating regime
    #

    if battery > POWER_THRESHOLD_W and grid > POWER_THRESHOLD_W:

        icon = "🟢"
        text = "Grid charging battery"

    elif grid < -POWER_THRESHOLD_W:

        icon = "🟢"
        text = "Exporting surplus"

    elif battery < -POWER_THRESHOLD_W:

        icon = "🟢"
        text = "Battery supporting house"

    elif solar > POWER_THRESHOLD_W and abs(grid) < 200:

        icon = "🟢"
        text = "Solar powering house"

    elif grid > POWER_THRESHOLD_W:

        icon = "🟡"
        text = "Importing from grid"

    else:

        icon = "🟢"
        text = "System balanced"

    if battery_soc is None:

        mode = work_mode

    else:

        mode = (
            f"{work_mode}"
            f" | SOC {battery_soc:.0f}%"
        )

    return {

        "work_mode": mode,

        "status_icon": icon,

        "status_text": text,

    }

def get_operations_status(
    health,
):
    if health.overall_status == HealthStatus.OPERATIONAL:
        icon = "🟢"
        text = "Operating Normally"

    elif health.overall_status == HealthStatus.DEGRADED:
        icon = "🟡"
        text = "Degraded"

    elif health.overall_status == HealthStatus.FAULT:
        icon = "🔴"
        text = "Fault"

    else:
        icon = "⚪"
        text = "Unknown"

    return {
        "icon": icon,
        "text": text,
    }


def get_system_health(
    health,
):
    data_age_seconds = health.data_age_seconds

    if data_age_seconds is None:
        data_age = None
    else:
        data_age = format_data_age(data_age_seconds / 60)

    return {
        "overall_status": health.system_label,
        "overall_icon": health.system_icon,
        "data_age": data_age,
        "last_successful_poll": health.last_successful_poll,
        "last_error": health.last_error,
    }


def get_next_action(
    latest,
    latest_upload_time,
    data_age_minutes,
):
    return {
        "time": "23:30",
        "action": "Force Charge",
    }

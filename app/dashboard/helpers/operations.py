from app.backend.services.system_health_service import HealthStatus
from app.dashboard.helpers.format_data import format_data_age


def get_current_state(latest):
    return {
        "work_mode": latest["work_mode"],
        "status_icon": "🟢",
        "status_text": "Following Schedule",
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
        "overall_status": health.overall_status.name.title(),
        "data_age": data_age,
        "last_successful_poll": health.last_successful_poll,
        "consecutive_failures": health.consecutive_failures,
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

def get_current_state(latest):
    return {
        "work_mode": latest["work_mode"],
        "status_icon": "🟢",
        "status_text": "Following Schedule",
    }


def get_operations_status(
    data_age_minutes,
):
    return {
        "icon": "🟢",
        "text": "Operating Normally",
    }


def get_system_health(
    latest,
    latest_upload_time,
    data_age_minutes,
):

    return {
        "poller": {
            "icon": "🟢",
            "text": "Healthy",
        },

        "inverter": {
            "icon": "🟢",
            "text": "Connected",
        },

        "scheduler": {
            "icon": "🟢",
            "text": "Running",
        },

        "notifications": {
            "icon": "🟢",
            "text": "Active",
        },
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

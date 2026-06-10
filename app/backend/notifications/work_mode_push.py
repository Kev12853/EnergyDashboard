def send_work_mode_push(
    pushover,
    change,
):

    title = "⚡ Energy Dashboard"

    message = (
        f"Work mode changed\n\n"
        f"{change['previous']}\n"
        f"↓\n"
        f"{change['current']}\n\n"
        f"{change['timestamp']:%H:%M:%S}"
    )

    pushover.send_push(
        title,
        message,
    )
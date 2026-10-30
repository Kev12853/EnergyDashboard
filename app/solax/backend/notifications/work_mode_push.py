"""Format and send a Pushover notification when the poller observes a work-mode change. The helper does not initiate a mode change."""

def send_work_mode_push(
    pushover,
    change,
):

    """Format a work-mode-change message and send it through the injected Pushover sender."""
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
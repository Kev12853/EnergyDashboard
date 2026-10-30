"""Format and send a notification when the poller observes a work-mode change. The helper does not initiate a mode change."""

def send_work_mode_email(
    sender,
    change,
):

    """Format a work-mode-change message and send it through the injected email sender."""
    subject = "Energy Dashboard - Work Mode Changed"

    body = f"""
Energy Dashboard detected a work mode change.

Time:
{change["timestamp"]:%H:%M:%S}

Previous:
{change["previous"]}

Current:
{change["current"]}

Detected by Energy Dashboard.
"""

    sender.send_email(
        subject,
        body,
    )
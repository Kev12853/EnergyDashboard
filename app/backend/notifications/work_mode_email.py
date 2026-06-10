def send_work_mode_email(
    sender,
    change,
):

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
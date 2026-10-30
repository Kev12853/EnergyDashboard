"""Send monitoring notifications by email using caller-supplied mail settings. This adapter is used by the poller and does not evaluate automation or control the inverter."""

import smtplib

from email.message import EmailMessage


class EmailSender:

    """Send email notifications using the configured SMTP endpoint and credentials; network or SMTP errors may be raised by the underlying client."""
    def __init__(
        self,
        smtp_server,
        smtp_port,
        username,
        password,
        sender,
        recipient,
    ):

        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

        self.username = username
        self.password = password

        self.sender = sender
        self.recipient = recipient

    def send_email(
        self,
        subject,
        body,
    ):

        """Send the supplied subject/body to the configured recipient; performs SMTP network I/O and may fail on connection or delivery errors."""
        message = EmailMessage()

        message["Subject"] = subject
        message["From"] = self.sender
        message["To"] = self.recipient

        message.set_content(body)

        with smtplib.SMTP_SSL(
            self.smtp_server,
            self.smtp_port,
        ) as smtp:

            smtp.login(
                self.username,
                self.password,
            )

            smtp.send_message(message)
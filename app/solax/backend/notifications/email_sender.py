import smtplib

from email.message import EmailMessage


class EmailSender:

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
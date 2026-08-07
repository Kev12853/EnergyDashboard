import smtplib

from email.message import EmailMessage


SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

EMAIL_ADDRESS = "kev12853@gmail.com"
APP_PASSWORD = "ulnr ftnv qxvc zlvn"


def send_test_email():

    message = EmailMessage()

    message["Subject"] = "Energy Dashboard Test"

    message["From"] = EMAIL_ADDRESS
    message["To"] = EMAIL_ADDRESS

    message.set_content(
        """
Congratulations!

Energy Dashboard email notifications are working.

🍺
"""
    )

    with smtplib.SMTP_SSL(
        SMTP_SERVER,
        SMTP_PORT,
    ) as smtp:

        smtp.login(
            EMAIL_ADDRESS,
            APP_PASSWORD,
        )

        smtp.send_message(message)

    print("Email sent successfully.")


if __name__ == "__main__":

    send_test_email()
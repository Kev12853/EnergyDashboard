import os

from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
APP_PASSWORD = os.getenv("APP_PASSWORD")
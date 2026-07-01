import os

from dotenv import load_dotenv

load_dotenv()

PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN")
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY")
"""Send monitoring notifications through Pushover using caller-supplied credentials. This adapter has no telemetry polling or inverter-control responsibility."""

import requests


class PushoverSender:

    """Send push notifications through the Pushover API using caller-provided credentials."""
    def __init__(
        self,
        api_token,
        user_key,
    ):

        self.api_token = api_token
        self.user_key = user_key

    def send_push(
        self,
        title,
        message,
    ):

        """Submit a title and message to Pushover; performs network I/O and propagates request failures."""
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": self.api_token,
                "user": self.user_key,
                "title": title,
                "message": message,
            },
            timeout=10,
        )
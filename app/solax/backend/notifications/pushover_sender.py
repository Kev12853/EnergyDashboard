import requests


class PushoverSender:

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
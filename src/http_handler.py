import os
import requests


class HttpHandler:
    def __init__(self):
        addr = os.environ.get("PAGER_ADDRESS", "http://localhost:8441/page")

        if not addr.startswith("http"):
            addr = f"http://{addr}"
        if not addr.endswith("/page"):
            addr = f"{addr}/page"

        self.url = addr

    def send(self, payload: str):
        requests.post(self.url, data=payload)
        print("EVENT SENT:", payload)

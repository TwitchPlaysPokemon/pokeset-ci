"""
Server-code for the github webhooks.
"""
from flask import Flask, request

WEBHOOK_URL = "/github_webhook"


class WebApp:
    def __init__(self):
        app = Flask(__name__)
        app.route(WEBHOOK_URL, methods=["POST"])(self.webhook)

    def webhook(self):
        data = request.data
        print(data)
        return ""

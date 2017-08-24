"""
Class representing the entirety of pokeset ci.
"""
from gevent.pywsgi import WSGIServer
from github import Github

from . import webapp
from .config import Config


class PokesetCi:
    def __init__(self, *, config: Config):
        self.config = config
        g = Github(login_or_token=config.oauth_token)
        self.repo = g.get_repo(config.repository)
        print(self.repo.full_name)

    def create_webhook(self):
        hook = self.repo.create_hook(
            name="web",
            config={
                "url": self.config.webhook_basepath + webapp.WEBHOOK_URL,
                "content_type": "json",
            },
            events=["push"],
            active=True,
        )
        print(hook)

    def run(self):
        app = webapp.WebApp()
        http_server = WSGIServer(('0.0.0.0', self.config.http_port), app)
        print("running webserver...")
        http_server.serve_forever()

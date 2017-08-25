"""
Class representing the entirety of pokeset ci.
"""
import logging

from gevent.pywsgi import WSGIServer
from github import Github

from . import webapp
from .config import Config

logger = logging.getLogger(__name__)


class PokesetCi:
    def __init__(self, *, config: Config):
        self.config = config
        self.github = Github(login_or_token=config.oauth_token)
        self.repo = self.github.get_repo(config.repository)
        logger.info("initialized for repository %s", self.repo.full_name)
        self.hook = self._get_webhook()
        logger.info("initialized with webhook: %s", self.hook)

    def _get_webhook(self):
        hook_url = self.config.webhook_basepath + webapp.WEBHOOK_URL
        for hook in self.repo.get_hooks():
            if hook.config["url"] == hook_url:
                return hook
        hook = self.repo.create_hook(
            name="web",
            config={
                "url": hook_url,
                "content_type": "json",
            },
            events=["push"],
            active=True,
        )
        logger.info("Created webhook %s for events %s and config %s", hook, hook.events, hook.config)
        return hook

    def run(self):
        app = webapp.WebApp(self.github, self.repo)
        http_server = WSGIServer(('', self.config.http_port), app)
        logger.info("running webserver...")
        http_server.serve_forever()

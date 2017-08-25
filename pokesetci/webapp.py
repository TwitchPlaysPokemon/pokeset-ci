"""
Server-code for the github webhooks.
"""
import logging

import gevent
from flask import Flask, request
from github import Github
from github.Repository import Repository

from .analyze import analyze_dir, Severity
from .temporary_repository import TemporaryRepository

WEBHOOK_URL = "/github_webhook"
logger = logging.getLogger(__name__)


class WebApp(Flask):
    def __init__(self, github: Github, repo: Repository):
        super().__init__(__name__)
        self.github = github
        self.repo = repo
        self.add_url_rule(
            WEBHOOK_URL,
            methods=["POST"],
            view_func=self.webhook
        )

    def webhook(self):
        data = request.json
        logger.info("webhook invoked, received payload: %s", data)
        commit_sha = data["head_commit"]["id"]
        gevent.spawn(self.analyze_commit, commit_sha)
        return ""

    def analyze_commit(self, commit_sha):
        commit = self.repo.get_commit(commit_sha)
        link = self.repo.get_archive_link("tarball", commit.sha)
        with TemporaryRepository(tarball_url=link) as repository:
            notes, pokesets = analyze_dir(repository)
            # filter out low priority notes
            notes = [n for n in notes if n.severity != Severity.NOTE]
            commit.create_comment("```{}```".format("\n".join(map(str, notes))))

"""
Config class for typesafe config access.
"""

class Config:
    def __init__(self, *,
                 oauth_token: str,
                 repository: str,
                 webhook_basepath: str,
                 http_port: int
                 ):
        self.oauth_token = oauth_token
        self.repository = repository
        self.webhook_basepath = webhook_basepath
        self.http_port = http_port

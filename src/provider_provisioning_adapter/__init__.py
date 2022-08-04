from gunicorn.app.base import BaseApplication

from .main import app
from .config import get_settings


class PPAServer(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def serve():
    settings = get_settings()
    options = {
        'bind': '%s:%s' % ('127.0.0.1', settings.ppa_port),
        'workers': 4,
        'worker-class': 'uvicorn.workers.UvicornWorker'
    }
    PPAServer(app, options).run()

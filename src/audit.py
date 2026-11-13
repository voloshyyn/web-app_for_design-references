"""Structured action log; no request bodies, query values or personal notes."""
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock


def timestamp():
    return datetime.now(timezone.utc).isoformat()


class Audit:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = Lock()

    def write(self, event, **fields):
        with self.lock, self.path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(dict(timestamp=timestamp(), event=event, **fields)) + '\n')

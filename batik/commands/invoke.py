import requests
from .base import Base


class Invoke(Base):
    """Invoke endpoints"""

    def run(self):
        endpoint = self.options["<endpoint>"]
        payload = self.options.get("payload") or None
        r = requests.post(f"http://localhost:5678/endpoint/{endpoint}", data = payload)
        print(str(r.content))
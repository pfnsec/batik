import requests
import json
from .base import Base


class Invoke(Base):
    """Invoke endpoints"""

    def run(self):
        endpoint = self.options["<endpoint>"]

        use_json = self.options.get("--json") or None
        if use_json:
            with open(self.options["<file>"]) as json_file:
                payload = json.load(json_file)
            r = requests.post(f"http://localhost:5678/endpoint/{endpoint}", json = payload)

        else:
            payload = self.options.get("payload") or None
            r = requests.post(f"http://localhost:5678/endpoint/{endpoint}", data = payload)

        print(str(r.content))
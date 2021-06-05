import requests
from .base import Base


class Reload(Base):
    """Reload Manifest"""

    def run(self):
        r = requests.post(f"http://localhost:5678/reload_manifest")
        print(str(r.content))
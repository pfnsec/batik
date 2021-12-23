
import json
from .base import Base
from batik import manifest
import batik.frontends


class Serve(Base):
    """Serve the Manifest"""

    async def run(self):
        mfst = manifest.Manifest()
        mfst.parse_file()

        backend = self.options.get("<backend>") or "http"

        if backend == "http":
            server = batik.frontends.http_basic.HTTPServer(mfst)
        
        await server.run()

from .base import Base
import batik
import batik.backends


class Serve(Base):
    """Serve the Manifest"""

    async def run(self):
        mfst = batik.api.Manifest()
        mfst.parse_file()

        backend = self.options.get("<backend>") or "http"

        if backend == "http":
            server = batik.backends.http_basic.HTTPServer(mfst)
        
        await server.run()

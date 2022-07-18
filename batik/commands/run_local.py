import json
from .base import Base
from batik.api import Manifest


class RunLocal(Base):
    """Load Manifest, run an endpoint, and quit"""

    async def run(self):
        mfst = Manifest()
        mfst.parse_file()

        endpoint = self.options["<endpoint>"]

        use_trace = self.options.get("--trace") or None
        if use_trace:
            trace = mfst.create_trace()
        else:
            trace = None

        use_json = self.options.get("--json") or None
        if use_json:
            with open(self.options["<file>"]) as json_file:
                payload = json.load(json_file)
                res = await mfst.run_endpoint(endpoint, payload, trace=trace)

        else:
            payload = self.options.get("<payload>") or None
            res = await mfst.run_endpoint(endpoint, payload, cast=True, trace=trace)

        print(str(res))
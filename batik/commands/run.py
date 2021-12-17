import json
from .base import Base
from batik import manifest


class Run(Base):
    """Load Manifest, run an endpoint, and quit"""

    def run(self):
        mfst = manifest.Manifest()
        mfst.parse_file()

        endpoint = self.options["<endpoint>"]

        use_trace = self.options.get("--trace") or None
        use_json = self.options.get("--json") or None
        if use_json:
            with open(self.options["<file>"]) as json_file:
                payload = json.load(json_file)
                res = mfst.run_endpoint(endpoint, payload)

        else:
            payload = self.options.get("<payload>") or None
            res = mfst.run_endpoint(endpoint, payload, cast=True)

        print(str(res))

from batik import manifest
from .base import Base


class Validate(Base):
    """Load a manifest and do nothing"""
    def __init__(self, options, *args, **kwargs):
        super().__init__(options, args, kwargs)

    def run(self):
        mfst = manifest.Manifest()
        mfst.parse_file()
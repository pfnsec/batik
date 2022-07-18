from .base import Base
import batik


class Validate(Base):
    """Load a manifest and do nothing"""
    def __init__(self, options, *args, **kwargs):
        super().__init__(options, args, kwargs)

    def run(self):
        mfst = batik.api.Manifest()
        mfst.parse_file()
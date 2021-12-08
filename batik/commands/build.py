import requests
import docker
import os
import pathlib

from .base import Base

import batik
from batik import manifest


class Build(Base):
    """Build a container from a manifest"""

    def run(self):
        client = docker.from_env()
        mfst = manifest.Manifest()
        mfst.parse_file()
        alias = mfst.alias

        registry = batik.env.get('image_registry')

        dockerfile = os.path.join(
            pathlib.Path(__file__).parent.resolve(),
            '../templates/docker/Dockerfile.default'
        )

        print(f"BUILD {registry}/{alias}")

        img, lines = client.images.build(
            path = '.',
            dockerfile = dockerfile,
            tag = f"{registry}/{alias}"
        )
        for line in lines:
            if 'stream' in line:
                print(line['stream'])
        
        if(self.options['--push']):
            res = client.images.push(f"{registry}/{alias}")
            print(res)

        
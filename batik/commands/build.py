import os
import tempfile
import pathlib
from jinja2 import Template
import asyncio
import subprocess

from .base import Base

import batik
from batik import manifest


class Build(Base):
    """Build a container from a manifest"""

    def run(self):
        mfst = manifest.Manifest()
        mfst.parse_file()
        alias = mfst.alias

        registry = batik.env.get('image_registry')

        template_base = '../templates/docker'
        template_file = os.path.join(
            pathlib.Path(__file__).parent.resolve(),
            template_base,
            'Dockerfile.default'
        )

        install_hook = 'pip install -r requirements.txt'

        with open(template_file) as f:
            template = Template(f.read())
        rendered = template.render(install_hook=install_hook)

        tmp = tempfile.NamedTemporaryFile(mode='w+', delete=False)
        try:
            print(tmp.name)
            tmp.write(rendered)
            tmp.seek(0)
            p = subprocess.Popen([
                'docker', 'build',
                '-f', tmp.name,
                '-t', f"{registry}/{alias}",
                '.',
            ], shell=False)
            p.wait()

        finally:
            tmp.close()
            os.unlink(tmp.name)
        
        if(self.options['--push']):
            subprocess.Popen([
                'docker', 'push',
                f"{registry}/{alias}",
            ], shell=False)

        
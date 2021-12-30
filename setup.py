"""Packaging settings."""


from codecs import open
from os.path import abspath, dirname, join
from subprocess import call

from setuptools import Command, find_packages, setup


this_dir = abspath(dirname(__file__))
with open(join(this_dir, 'README.md'), encoding='utf-8') as file:
    long_description = file.read()


class RunTests(Command):
    """Run all tests."""
    description = 'run tests'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        """Run all tests!"""
        errno = call(['py.test', '--cov=batik', '--cov-report=term-missing'])
        raise SystemExit(errno)


setup(
    name = 'batik',
    version = "0.4.0",
    description = 'batik',
    long_description = long_description,
    url = 'https://github.com/pfnsec/batik',
    author = 'Peter Sherman',
    author_email = 'pfnsec@gmail.com',
    license = 'MIT',
    classifiers = [
        'Intended Audience :: Developers',
        'Topic :: Utilities',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    keywords = 'cli',
    packages = find_packages(exclude=['docs', 'tests*']),
    install_requires = [
        'aiohttp',
        'pyyaml',
        'watchdog',
        'docopt',
        "jinja2",
        'docker',
        'kubernetes',
    ],
    extras_require = {
        'test': ['coverage', 'pytest', 'pytest-cov'],
    },
    entry_points = {
        'console_scripts': [
            'batik=batik.cli:main',
        ],
    },
    cmdclass = {'test': RunTests},
)

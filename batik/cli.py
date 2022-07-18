"""
batik

Usage:
  batik serve [--backend <backend>] [--hot-reload]
  batik invoke <endpoint> [(--json <file> | <payload>)]
  batik run <endpoint> [(--json <file> | <payload>)] [--trace]
  batik build [--push]
  batik validate

Options:
  -h --help                         Show this screen.
  --version                         Show version.

Examples:
  batik serve

Help:
  For help using this tool, please open an issue on the Github repository:
  https://github.com/pfnsec/batik
"""


import sys
import asyncio
import inspect
from inspect import getmembers, isclass

from docopt import docopt

from . import __version__ as VERSION
import batik.commands

command_map = {
  "serve": batik.commands.Serve,
  "validate": batik.commands.Validate,
  "invoke": batik.commands.Invoke,
  "run-local": batik.commands.RunLocal,
}

def main():
    if sys.platform == 'win32':
        #loop = asyncio.ProactorEventLoop()
        #asyncio.set_event_loop(loop)
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(co_main())
    loop.close()

async def co_main():
    options = docopt(__doc__, version=VERSION)

    # Here we'll try to dynamically match the command the user is trying to run
    # with a pre-defined command class we've already created.

    for (k, v) in options.items(): 
        #if hasattr(batik.commands, k) and v:
        if v:
            command = command_map[k](options)
            if inspect.iscoroutinefunction(command.run):
                await command.run()
            else:
                command.run()

"""
batik

Usage:
  batik serve [--backend <backend>]
  batik invoke <endpoint>  [--json <file>] [<payload>]
  batik reload
  batik hello

Options:
  -h --help                         Show this screen.
  --version                         Show version.

Examples:
  batik serve

Help:
  For help using this tool, please open an issue on the Github repository:
  https://github.com/batik-informat/batik
"""


from inspect import getmembers, isclass

from docopt import docopt

from . import __version__ as VERSION

def main():
    """Main CLI entrypoint."""
    import batik.commands
    options = docopt(__doc__, version=VERSION)

    # Here we'll try to dynamically match the command the user is trying to run
    # with a pre-defined command class we've already created.

    for (k, v) in options.items(): 
        if hasattr(batik.commands, k) and v:
            module = getattr(batik.commands, k)

            classes = getmembers(module, isclass)

            #command = [command[1] for command in classes if command[0] != 'Base'][0]
            # What a hack! Oh well
            command = [command[1] for command in classes if str(command[0]).lower() == k][0]
            command = command(options)
            command.run()

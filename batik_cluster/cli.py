"""
batik_cluster

Usage:
  batik_cluster serve 

Options:
  -h --help                         Show this screen.
  --version                         Show version.

Examples:
  batik_cluster serve

Help:
  For help using this tool, please open an issue on the Github repository:
"""


from inspect import getmembers, isclass

from docopt import docopt

from . import __version__ as VERSION

def main():
    """Main CLI entrypoint."""
    import batik_cluster.commands
    from batik_cluster import commands
    options = docopt(__doc__, version=VERSION)

    # Here we'll try to dynamically match the command the user is trying to run
    # with a pre-defined command class we've already created.

    for (k, v) in options.items(): 
        if hasattr(batik_cluster.commands, k) and v:
            module = getattr(batik_cluster.commands, k)

            classes = getmembers(module, isclass)
            print("classes")
            print(classes)

            command = [command[1] for command in classes if command[0] != 'Base'][0]
            command = command(options)
            command.run()

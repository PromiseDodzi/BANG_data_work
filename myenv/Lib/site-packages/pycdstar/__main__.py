import types

from docopt import docopt

import pycdstar
from pycdstar.config import Config
from pycdstar.api import Cdstar
from pycdstar import commands


COMMANDS = [getattr(commands, name) for name in dir(commands) if name.startswith('c_')]
COMMANDS = {f.__name__[2:]: f for f in COMMANDS}
MAX_CMD_NAME = max([len(name) for name in COMMANDS.keys()])

__doc__ = """
A cdstar client::

    usage: cdstar [options] <command> [<args>...]

    options:
        -h --help         Show this screen.
        --version         Show version.
        -V --verbose      Display status messages verbosely.
        --cfg=<CFG>       Path to config file.
        --service=<URL>   URL of the cdstar service.
        --user=<USER>
        --password=<PWD>

    The available commands are:
%s

    See 'cdstar help <command>' for more information on a specific command.

""" % '\n'.join(
    '        %s  %s' % (name.ljust(MAX_CMD_NAME), f.__doc__.split('\n')[0])
    for name, f in COMMANDS.items())


def main(argv=None):
    """Main entry point for the cdstar CLI."""
    args = docopt(__doc__, version=pycdstar.__version__, argv=argv, options_first=True)
    subargs = [args['<command>']] + args['<args>']

    if args['<command>'] in ['help', None]:
        cmd = None
        if len(subargs) > 1:
            cmd = COMMANDS.get(subargs[1])
        if cmd:
            print(cmd.__doc__)
        else:
            print(__doc__)
        return 0

    cmd = COMMANDS.get(args['<command>'])
    if not cmd:
        print('unknown command')
        print(__doc__)
        return 0

    cfg = Config(**dict(
        cfg=args.pop('--cfg', None),
        url=args.pop('--service', None),
        user=args.pop('--user', None),
        password=args.pop('--password', None)))

    try:
        res = cmd(
            Cdstar(cfg=cfg),
            docopt(cmd.__doc__, argv=subargs),
            verbose=args.get('--verbose'))
        if isinstance(res, types.GeneratorType):
            res = list(res)
        if isinstance(res, list):
            for line in res:
                print(line)
            res = 0
        return res or 0
    except:  # noqa: E722; # pragma: no cover
        # FIXME: log exception!
        return 256


if __name__ == '__main__':  # pragma: no cover
    main()

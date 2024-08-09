"""
Main command line interface of the cdstarcat package.
"""
import os
import sys
import contextlib

from clldutils.loglib import Logging
from clldutils.clilib import get_parser_and_subparsers, register_subcommands

from cdstarcat import Catalog
from cdstarcat.cli_util import add_cdstar
import cdstarcat.commands


def main(args=None, catch_all=False, parsed_args=None, log=None):
    parser, subparsers = get_parser_and_subparsers('cdstarcat')
    envvar = 'CDSTAR_CATALOG'
    parser.add_argument(
        '--catalog',
        help="defaults to ${0}".format(envvar),
        default=os.environ.get(envvar))
    add_cdstar(parser)
    register_subcommands(subparsers, cdstarcat.commands)

    args = parsed_args or parser.parse_args(args=args)

    if not hasattr(args, "main"):
        parser.print_help()
        return 1

    with contextlib.ExitStack() as stack:
        args.catalog = stack.enter_context(Catalog(
            args.catalog, cdstar_url=args.url, cdstar_user=args.user, cdstar_pwd=args.pwd))
        if not log:  # pragma: no cover
            stack.enter_context(Logging(args.log, level=args.log_level))
        else:
            args.log = log
        try:
            return args.main(args) or 0
        except KeyboardInterrupt:  # pragma: no cover
            return 0
        except Exception as e:  # pragma: no cover
            if catch_all:
                print(e)
                return 1
            raise


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main() or 0)

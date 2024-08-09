import os
import sys
import pathlib
import contextlib

from clldutils.clilib import get_parser_and_subparsers, register_subcommands, PathType
from clldutils.loglib import Logging

from zenodoclient import Zenodo
import zenodoclient.commands


def main(args=None, catch_all=False, parsed_args=None):
    parser, subparsers = get_parser_and_subparsers('zenodo')
    parser.add_argument(
        '--catalogs',
        type=PathType(type='dir'),
        default=pathlib.Path('.'),
        help='Location of catalog directory')
    parser.add_argument(
        '--token',
        default=os.environ.get('ZENODO_ACCESS_TOKEN'),
        help='zenodo access token')
    register_subcommands(subparsers, zenodoclient.commands)

    args = parsed_args or parser.parse_args(args=args)

    if not hasattr(args, "main"):
        parser.print_help()
        return 1

    with contextlib.ExitStack() as stack:
        stack.enter_context(Logging(args.log, level=args.log_level))
        args.zenodo = Zenodo(args.token)
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

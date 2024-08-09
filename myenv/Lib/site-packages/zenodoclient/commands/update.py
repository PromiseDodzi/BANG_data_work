"""
Update deposit
"""
from clldutils.clilib import PathType
from clldutils import jsonlib

from zenodoclient.catalog import Deposits


def register(parser):
    parser.add_argument('deposit', help='Deposit ID')
    parser.add_argument(
        '--metadata-file',
        help='JSON metadata file',
        type=PathType(type='file'))
    parser.add_argument(
        'metadata',
        nargs='*')


def run(args):
    with Deposits(args.catalogs / 'depositions.json') as cat:
        md = {}
        if args.metadata_file:
            md.update(jsonlib.load(args.metadata_file))
        for m in args.metadata:
            key, value = m.split('=', maxsplit=1)
            md[key] = value
        dep = args.zenodo.update_deposit(args.deposit, **md)
        cat.add(dep)

import os
import argparse

from cdstarcat.catalog import OBJID_PATTERN


class OBJIDType(object):
    def __call__(self, string):
        if not OBJID_PATTERN.match(string):
            raise argparse.ArgumentTypeError('No valid OBJID: {0}!'.format(string))
        return string


def add_objid(parser):
    parser.add_argument(
        'objid',
        metavar='OBJID',
        type=OBJIDType(),
        help='ID of an object in CDSTAR',
    )


def add_cdstar(parser):
    for arg in ['url', 'user', 'pwd']:
        envvar = 'CDSTAR_{0}'.format(arg.upper())
        parser.add_argument(
            '--' + arg,
            help="defaults to ${0}".format(envvar),
            default=os.environ.get(envvar))

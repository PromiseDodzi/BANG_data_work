"""
Create objects in CDSTAR (and record them in the catalog).
"""
from clldutils.clilib import PathType


def register(parser):
    parser.add_argument(
        'path',
        type=PathType(),
        help="Path to file or directory to create CDSTAR object(s) for. When PATH is a file, "
             "a single object (possibly with multiple bitstreams) is created; when PATH is a "
             "directory, an object will be created for each file in the directory "
             "(recursing into subdirectories).",
        metavar='PATH')


def run(args):
    for fname, created, obj in args.catalog.create(args.path, {}):
        args.log.info('{0} -> {1} object {2.id}'.format(
            fname, 'new' if created else 'existing', obj))

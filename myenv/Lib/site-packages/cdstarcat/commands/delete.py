"""
Delete an object from CDSTAR (and the catalog).
"""
from cdstarcat.cli_util import add_objid


def register(parser):
    add_objid(parser)


def run(args):
    n = len(args.catalog)
    args.catalog.delete(args.objid)
    args.log.info('{0} objects deleted'.format(n - len(args.catalog)))
    return n - len(args.catalog)

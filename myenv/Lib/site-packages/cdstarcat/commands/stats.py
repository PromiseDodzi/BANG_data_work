"""
Print summary statistics of bitstreams in the catalog to stdout.
"""
import itertools
import collections

from clldutils.clilib import Table, add_format


def register(parser):
    add_format(parser, default='simple')


def run(args):
    print('Summary:')
    print('  {0:,} objects with {1:,} bitstreams of total size {2}'.format(
        len(args.catalog), sum(len(obj.bitstreams) for obj in args.catalog), args.catalog.size_h))
    print('  {0} duplicate bitstreams'.format(
        sum(1 for objs in args.catalog.md5_to_object.values() if len(objs) > 1)))
    print('  {0} objects with no bitstreams'.format(
        sum(1 for obj in args.catalog if not obj.bitstreams)))

    print()
    types = collections.Counter(itertools.chain(
        *[[bs.mimetype for bs in obj.bitstreams] for obj in args.catalog]))
    with Table('maintype', 'subtype', 'bitstreams') as table:
        for maintype, items in itertools.groupby(
                sorted(types.items(), key=lambda p: (p[0].split('/')[0], -p[1])),
                lambda p: p[0].split('/')[0]):
            for k, v in items:
                table.append([maintype, k.split('/')[1], v])

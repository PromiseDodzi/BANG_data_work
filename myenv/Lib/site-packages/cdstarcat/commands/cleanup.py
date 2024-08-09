"""
Deletes objects with no bitstreams from CDSTAR and the catalog.
"""


def register(parser):
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=False,
        help='Only list objects to be deleted.',
    )


def run(args):
    n, d, r = len(args.catalog), [], []
    for obj in args.catalog:
        if not obj.bitstreams:
            if obj.is_special:  # pragma: no cover
                print('removing {0} from catalog'.format(obj.id))
                r.append(obj)
            else:
                print('deleting {0} from CDSTAR'.format(obj.id))
                d.append(obj)
    if not args.dry_run:
        for obj in d:
            args.catalog.delete(obj)
        for obj in r:  # pragma: no cover
            args.catalog.remove(obj)
    args.log.info('{0} objects deleted'.format(n - len(args.catalog)))
    return n - len(args.catalog)

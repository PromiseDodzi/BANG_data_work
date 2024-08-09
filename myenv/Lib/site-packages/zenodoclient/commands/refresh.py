"""
Refresh deposit catalog
"""
from zenodoclient.catalog import Deposits


def run(args):
    with Deposits(args.catalogs / 'depositions.json') as cat:
        for dep in args.zenodo.iter_deposits(all_versions=True):
            cat.add(dep)

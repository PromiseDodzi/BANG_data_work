"""
Add affiliation and orcid
"""
import collections

from clldutils import jsonlib

from zenodoclient.catalog import Deposits
from zenodoclient.api import ApiError


def run(args):
    people_by_name = {p['name']: p for p in jsonlib.load(args.catalogs / 'people.json')}
    with Deposits(args.catalogs / 'depositions.json') as cat:
        for dep in cat.objects.values():
            changed = False
            md = collections.defaultdict(list)
            for p in dep['metadata']['creators']:
                np = {k: v for k, v in p.items()}
                if np['name'] in people_by_name:
                    np.update(people_by_name[np['name']])
                    if np != p:
                        changed = True
                    md['creators'].append(np)

            for p in dep['metadata']['contributors']:
                np = {k: v for k, v in p.items()}
                if np['name'] in people_by_name:
                    np.update(people_by_name[np['name']])
                    if np != p:
                        changed = True
                    md['contributors'].append(np)

            if changed:
                print(dep['title'])
                print(md)
                try:
                    dep = args.zenodo.update_deposit(dep['id'], **md)
                    cat.add(dep)
                except ApiError as e:
                    print(e)

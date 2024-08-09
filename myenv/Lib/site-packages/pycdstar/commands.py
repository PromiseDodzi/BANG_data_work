import json
import fnmatch
import os
import os.path
import re
import pathlib
from datetime import datetime


def _split(s, separator=','):
    return [x.strip() for x in (s or '').split(separator) if x.strip()]


def set_metadata(spec, obj):
    if spec:
        spec_as_path = pathlib.Path(spec)
        if spec_as_path.exists() and spec_as_path.is_file():
            with spec_as_path.open(encoding='utf8') as fp:
                obj.metadata = json.load(fp)
        else:
            obj.metadata = json.loads(spec)
        return True
    return False


def c_metadata(api, args, verbose=False):
    """
Set or get metadata associated with an object::

    usage: cdstar metadata <URL> [<JSON>]

    <JSON>  Path to metadata in JSON, or JSON literal.
"""
    obj = api.get_object(args['<URL>'].split('/')[-1])
    if not set_metadata(args['<JSON>'], obj):
        return json.dumps(obj.metadata.read(), indent=4)


def c_delete(api, args, verbose=False):
    """
Delete an object::

    usage: cdstar delete <URL>
"""
    obj = api.get_object(args['<URL>'].split('/')[-1])
    obj.delete()
    if verbose:
        return ['deleted object at', api.url(obj)]


def c_ls(api, args, verbose=False):
    """
List bitstreams of an object::

    usage: cdstar ls [options] <URL>

    options:
        -t  sort by modification time, newest first
        -s  sort by filesize, biggest first
        -r  reverse order while sorting
"""
    obj = api.get_object(args['<URL>'].split('/')[-1])
    res = []
    for bitstream in obj.bitstreams:
        res.append((
            api.url(bitstream),
            bitstream._properties['content-type'],
            bitstream._properties['filesize'],
            datetime.fromtimestamp(bitstream._properties['last-modified'] / 1000.0)
        ))
    if args['-t']:
        res = sorted(res, key=lambda t: t[3], reverse=True)
    elif args['-s']:
        res = sorted(res, key=lambda t: t[2], reverse=True)
    if args['-r']:
        res = reversed(res)

    for r in res:
        yield '{0}\t{1}\t{2:>8}\t{3}'.format(*r) if verbose else r[0]


def c_create(api, args, verbose=False):
    """
Create a new object uploading files from a directory as bitstreams::

    usage: cdstar create [options] <DIR>

    options:
        --metadata=<JSON>    Path to metadata in JSON, or JSON literal.
        --include=<PATTERNS> comma-separated list of filename patterns to include.
        --exclude=<PATTERNS> comma-separated list of filename patterns to exclude.
"""
    def patterns(opt):
        res = _split(opt)
        if res:
            return r'|'.join([fnmatch.translate(x) for x in res])

    includes = patterns(args['--include'])
    excludes = patterns(args['--exclude'])

    obj = api.get_object()
    if verbose:
        yield 'object created at'
        yield api.url(obj)

    if set_metadata(args['--metadata'], obj):
        if verbose:
            yield 'adding metadata'
            yield api.url(obj.metadata)

    for root, dirs, files in os.walk(args['<DIR>']):
        # exclude/include files
        files = [os.path.join(root, f) for f in files]
        if excludes:
            files = [f for f in files if not re.match(excludes, f)]
        if includes:
            files = [f for f in files if re.match(includes, f)]

        for fname in files:
            bitstream = obj.add_bitstream(fname=fname)
            if verbose:
                yield 'adding bitstream'
                yield api.url(bitstream)

    yield api.url(obj)

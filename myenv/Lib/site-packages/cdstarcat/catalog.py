import re
import time
import json
import pathlib
import zipfile
import datetime
import mimetypes
import collections

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning, InsecurePlatformWarning
import attr

from pycdstar import media
from pycdstar.catalog import filter_hidden, iter_files
from pycdstar.api import Cdstar
from clldutils.jsonlib import dump, load
from clldutils.misc import format_size

from cdstarcat.resources import RollingBlob

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)

mimetypes.add_type('video/mp4', '.mod', strict=False)

OBJID_PATTERN = re.compile('-'.join(['[A-F0-9]{%s}' % n for n in [5, 4, 4, 4, 1]]) + '$')


class WithHumanReadableSize(object):
    @property
    def size_h(self):
        return format_size(getattr(self, 'size', 0))


@attr.s(frozen=True)
class Bitstream(WithHumanReadableSize):
    id = attr.ib()
    size = attr.ib()
    mimetype = attr.ib()
    md5 = attr.ib()
    created = attr.ib()
    modified = attr.ib()

    @property
    def created_datetime(self):
        return datetime.datetime.utcfromtimestamp(self.created / 1e3)

    @property
    def modified_datetime(self):
        return datetime.datetime.utcfromtimestamp(self.modified / 1e3)

    @classmethod
    def fromdict(cls, d):
        return cls(
            d['bitstreamid'],
            d['filesize'],
            d['content-type'],
            d['checksum'],
            d['created'],
            d['last-modified'])

    def asdict(self):
        return collections.OrderedDict([
            ("bitstreamid", self.id),
            ("checksum", self.md5),
            ("created", self.created),
            ("checksum-algorithm", "MD5"),
            ("last-modified", self.modified),
            ("filesize", self.size),
            ("content-type", self.mimetype)
        ])


@attr.s(frozen=True)
class Object(WithHumanReadableSize):
    id = attr.ib()
    bitstreams = attr.ib()
    metadata = attr.ib()

    @property
    def size(self):
        return sum(bs.size for bs in self.bitstreams)

    @property
    def is_special(self):
        return 'warning' in self.metadata

    @classmethod
    def fromdict(cls, id_, d):
        return cls(id_, [Bitstream.fromdict(bs) for bs in d['bitstreams']], d['metadata'])

    def asdict(self):
        return collections.OrderedDict([
            ('bitstreams', [bs.asdict() for bs in self.bitstreams]),
            ('metadata', collections.OrderedDict(
                [(k, v) for k, v in sorted(self.metadata.items())]))]
        )


class Catalog(WithHumanReadableSize):
    """
    A catalog of objects in a CDSTAR instance.

    For operations resulting in changes the Catalog should be used as context manager to
    make sure changes are written to disk.
    """
    def __init__(self, path, cdstar_url=None, cdstar_user=None, cdstar_pwd=None):
        self.path = pathlib.Path(path)
        self.objects = {}
        if self.path.exists():
            if self.path.suffix.lower() == '.zip':
                with zipfile.ZipFile(str(self.path), 'r') as z:
                    for filename in z.namelist():
                        with z.open(filename) as f:
                            self.objects = {i: Object.fromdict(i, d) for i, d in json.loads(
                                f.read().decode('utf-8')).items()}
                        break
            else:
                self.objects = {i: Object.fromdict(i, d) for i, d in load(self.path).items()}
        self.api = Cdstar(service_url=cdstar_url, user=cdstar_user, password=cdstar_pwd)

    @property
    def md5_to_object(self):
        res = collections.defaultdict(list)
        for obj in self.objects.values():
            for bs in obj.bitstreams:
                res[bs.md5].append(obj)
        return res

    def __enter__(self):
        return self

    def __exit__(self, *args):
        ordered = collections.OrderedDict(
            [(k, v.asdict()) for k, v in sorted(self.objects.items())])
        if self.path.suffix.lower() == '.zip':
            with zipfile.ZipFile(str(self.path), 'w', zipfile.ZIP_DEFLATED) as z:
                z.writestr(self.path.stem, json.dumps(
                    ordered, ensure_ascii=False, indent=0, separators=(',', ':')))
        else:
            dump(ordered, self.path, indent=0, separators=(',', ':'))

    def __len__(self):
        """
        :return: The number of objects in the catalog
        """
        return len(self.objects)

    def __iter__(self):
        return iter(self.objects.values())

    def __contains__(self, item):
        """
        Check whether an object or a a bitstream (specified by md5 sum) is in the catalog.

        :param item:
        :return:
        """
        item = getattr(item, 'id', item)
        return (item in self.objects) or (item in self.md5_to_object)

    def __getitem__(self, item):
        item = getattr(item, 'id', item)
        if item in self.objects:
            return self.objects[item]
        md5_to_objects = self.md5_to_object
        if item in md5_to_objects:
            return md5_to_objects[item]
        raise KeyError(item)

    def __setitem__(self, item, obj):
        objid = getattr(item, 'id', item)
        if not OBJID_PATTERN.match(objid):
            raise ValueError('invalid object ID: %s' % objid)
        if not isinstance(obj, Object):
            raise ValueError('invalid object type: %s' % type(obj))
        self.objects[objid] = obj

    @property
    def size(self):
        return sum(obj.size for obj in self)

    def add(self, obj, metadata=None, update=False):
        """
        Add an existing CDSTAR object to the catalog.

        :param obj: A pycdstar.resource.Object instance
        """
        if (obj not in self) or update:
            self[obj.id] = Object.fromdict(
                obj.id,
                dict(
                    metadata=obj.metadata.read() if metadata is None else metadata,
                    bitstreams=[bs._properties for bs in obj.bitstreams]))
            time.sleep(0.1)
            return self.objects[obj.id]

    def add_rollingblob(self, fname, oid=None, collection=None, name=None, **kw):
        rb = RollingBlob(oid=oid, collection=collection, name=name)
        keep = kw.pop('keep', 5)
        rb.add(self.api, fname, **kw)
        rb.expunge(self.api, keep=keep)
        return self.add(rb.get_object(self.api), update=True)

    def remove(self, obj):
        del self.objects[getattr(obj, 'id', obj)]

    def delete(self, obj):
        """
        Delete an object in CDSTAR and remove it from the catalog.

        :param obj: An object ID or an Object instance.
        """
        obj = self.api.get_object(getattr(obj, 'id', obj))
        obj.delete()
        self.remove(obj.id)

    def create(self, path, metadata, filter_=filter_hidden, object_class=None):
        """
        Create objects in CDSTAR and register them in the catalog.

        Note that we guess the mimetype based on the filename extension, using
        `mimetypes.guess_type`. Thus, it is the caller's responsibility to add custom or
        otherwise uncommon types to the list of known types using `mimetypes.add_type`.

        :param path:
        :param metadata: A metadata `dict` or a `callable` accepting a `Path` as sole argument \
        and returning a metadata `dict`.
        :param filter_: A `callable` accepting a `Path` as sole argument and returning `True` if \
        the corresponding file should be uploaded, `False` otherwise.
        :return:
        """
        for fname in iter_files(path):
            if not filter_ or filter_(fname):
                created, obj = self._create(
                    fname,
                    metadata if isinstance(metadata, dict) else metadata(fname),
                    object_class=object_class)
                yield fname, created, obj

    def _create(self, path, metadata, object_class=None):
        mimetype = mimetypes.guess_type(str(path), strict=False)[0] \
            or 'application/octet-stream'
        maintype, subtype = mimetype.split('/')
        cls = object_class or getattr(media, maintype.capitalize(), media.File)
        file_ = cls(path)
        if file_.md5 not in self.md5_to_object:
            obj, md, bitstreams = file_.create_object(self.api, metadata)
            return True, self.add(obj, metadata=md)
        return False, self.md5_to_object[file_.md5][0]

    def update_metadata(self, obj, metadata, mode='merge'):
        objid = getattr(obj, 'id', obj)
        assert OBJID_PATTERN.match(objid) and objid in self
        obj = self.api.get_object(objid)
        md = obj.metadata.read() if mode == 'merge' else {}
        md.update(metadata)
        obj.metadata = md
        return self.add(obj, md, update=True)

    def add_query(self, query, limit=500, offset=0):
        def search(offset):
            time.sleep(0.2)
            return self.api.search(query, index='metadata', limit=limit, offset=offset)

        results = search(offset)
        total_results = 0
        while results:
            for res in results:
                total_results += 1
                self.add(res.resource)
            offset += limit
            results = search(offset)
        return total_results

    def add_objids(self, *objids, **kw):
        for objid in objids:
            self.add(self.api.get_object(objid), update=kw.get('update', False))

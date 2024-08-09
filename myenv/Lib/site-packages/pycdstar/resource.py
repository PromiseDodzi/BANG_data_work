import re
import string
from mimetypes import guess_type
import json


class Resource(object):
    def __init__(self, api, id=None, obj=None, **kw):
        self.id = id
        self.obj = obj
        self._api = api
        self._properties = {}

        if id is None:
            self.create(**kw)

    def exists(self):
        return self.read(assert_status=[200, 404], json=False).status_code != 404

    def create(self, **kw):
        raise NotImplementedError

    def read(self, **kw):
        return self._api._req(self.path, **kw)

    def update(self, **kw):
        raise NotImplementedError

    def delete(self):
        assert self.id
        return self._api._req(
            self.path, method='delete', assert_status=204, json=False)

    @property
    def service_name(self):
        return '%ss' % self.__class__.__name__.lower()

    @property
    def path(self):
        path = '/%s/' % self.service_name
        if self.obj:
            path += '%s' % getattr(self.obj, 'id', self.obj)
        if self.id:
            if not path.endswith('/'):
                path += '/'
            path += '%s' % self.id
        return path


class Object(Resource):
    def create(self, **kw):
        res = self._api._req(self.path, method='post', assert_status=201)
        self.id = res['uid']

    def read(self):
        self._properties = Resource.read(self)
        return self._properties

    @property
    def metadata(self):
        md = Metadata(self._api, id=self.id)
        if md.exists():
            return md

    @metadata.setter
    def metadata(self, value):
        md = Metadata(self._api, id=self.id)
        if md.exists():
            md.update(metadata=value)
        else:
            md.create(metadata=value)

    @property
    def bitstreams(self):
        if not self._properties:
            self.read()
        return [
            Bitstream(self._api, id=spec['bitstreamid'], obj=self, properties=spec)
            for spec in self._properties['bitstream']]

    def add_bitstream(self, **kw):
        return Bitstream(self._api, obj=self, **kw)

    @property
    def acl(self):
        return ACL(self._api, id=self.id)


class Metadata(Resource):
    @property
    def service_name(self):
        return 'metadata'

    def _cu(self, method, **kw):
        _kw = dict(
            method=method,
            assert_status=201,
            data=json.dumps(kw['metadata']),
            headers={'content-type': 'application/json'})
        return self._api._req(self.path, **_kw)

    def create(self, **kw):
        return self._cu('post', **kw)

    def update(self, **kw):
        return self._cu('put', **kw)


class ACL(Resource):
    @property
    def service_name(self):
        return 'accesscontrol'

    def update(self, **kw):
        acl = self.read()
        for permission in ['manage', 'read', 'write']:
            if permission in kw:
                acl[permission] = kw[permission]
        _kw = dict(
            method='put',
            assert_status=200,
            data=json.dumps(acl),
            headers={'content-type': 'application/json'})
        return self._api._req(self.path, **_kw)


class Bitstream(Resource):
    """Bitstreams are binary blobs (aka files) associated with an object."""
    NAME_PATTERN = re.compile(r'[%s0-9_\.]+$' % string.ascii_letters)

    def __init__(self, api, id=None, obj=None, **kw):
        """
        Retrieve an existing or create a new Bitstream.

        A Bitstream is created by uploading a local file, specified by its local path
        passed as `fname` keyword argument.

        :param api: An initialized Cdstar API client.
        :param id: UID of an existing bitstream or `None` to create a new bitstream.
        :param obj: The object the bistream is associated with.
        :param kw: A keyword parameter `mimetype` can be passed to explicitely specify \
        a content-type for the bitstream; a keyword parameter `name` can be passed to \
        specify an explicit Bitstream ID; note that Bitstream IDs are limited to \
        alphanumeric characters, underscore and dot.
        """
        assert obj
        Resource.__init__(self, api, id=id, obj=obj, **kw)
        if 'properties' in kw:
            self._properties = kw['properties']

    def _cu(self, method, **kw):
        content_type = kw.get('mimetype', guess_type(kw['fname'])[0])
        if not content_type:
            content_type = 'application/octet-stream'  # pragma: no cover
        with open(kw['fname'], 'rb') as f:
            _kw = dict(
                method=method,
                data=f,
                assert_status=201,
                headers={'content-type': content_type})
            return self._api._req(self.path, **_kw)

    def create(self, **kw):
        if 'name' in kw:
            assert self.NAME_PATTERN.match(kw['name'])
            self.id = kw['name']
        res = self._cu('post', **kw)
        self.id = res['bitstreamid']

    def update(self, **kw):
        return self._cu('put', **kw)

    def read(self):
        return Resource.read(self, json=False, stream=True).raw


class Result(object):
    def __init__(self, api, hit):
        self._api = api
        self.source = hit['source']
        self.score = hit['score']
        self.resource = Object(api, hit['uid'])
        if hit['type'] == 'fulltext':
            self.resource = Bitstream(api, id=hit['bitstreamid'], obj=self.resource)


class SearchResults(list):
    def __init__(self, api, res):
        self._api = api
        self.maxscore = res['maxscore']
        self.hitcount = res['hitcount']
        list.__init__(self, [Result(api, hit) for hit in res['hits']])

"""
http://developers.zenodo.org/
"""
import os
import re
import json
import shutil
import pathlib
import zipfile
import requests
import tempfile
import warnings
from http.client import responses as http_status
import urllib.request

from urllib3.exceptions import InsecurePlatformWarning
try:
    from urllib3.exceptions import SNIMissingWarning
except ImportError:
    SNIMissingWarning = None
from bs4 import BeautifulSoup as bs
from clldutils.path import md5

from zenodoclient.models import Deposition, DepositionFile, PUBLISHED, \
    UNSUBMITTED, Record
from zenodoclient import oai

if SNIMissingWarning is not None:
    warnings.simplefilter('once', SNIMissingWarning)
warnings.simplefilter('once', InsecurePlatformWarning)

API_URL = 'https://zenodo.org/api/'
API_URL_SANDBOX = 'https://sandbox.zenodo.org/api/'
ACCESS_TOKEN = os.environ.get('ZENODO_ACCESS_TOKEN')


class ApiError(Exception):
    def __init__(self, status, details=None):
        msg = '{0} {1}'.format(status, http_status[status])
        if details and 'message' in details:
            msg += ': {0}'.format(details['message'])
        self.errors = details.get('errors') if details else None
        Exception.__init__(self, msg)


class Zenodo(object):

    DOI_PATTERN = re.compile(r'10\.5281/zenodo\.(?P<id>[0-9]+)$')

    def __init__(self, access_token=ACCESS_TOKEN, api_url=API_URL):
        self._access_token = access_token
        self._api_url = api_url

    def _req(self, method, path='', prefix='deposit/depositions', expected=200, **kw):
        """
        http://developers.zenodo.org/#requests
        http://developers.zenodo.org/#responses
        """
        if path and not path.startswith('/'):
            path = '/' + path
        params = kw.pop('params', {})
        if method == 'get':
            params['access_token'] = self._access_token
        else:
            assert '?' not in path
            path += '?access_token={0}'.format(self._access_token)

        # All POST and PUT request bodies must be JSON encoded, and must have content
        # type of application/json [...]
        if method in ['post', 'put'] and 'data' in kw and 'files' not in kw:
            kw['headers'] = {"Content-Type": "application/json"}
            kw['data'] = json.dumps(kw['data'])

        response = getattr(requests, method)(
            '{0}{1}{2}'.format(self._api_url, prefix, path), params=params, **kw)
        if response.status_code == expected:
            if expected != 204:
                return response.json()
            return  # 204 No Content
        # See http://developers.zenodo.org/#errors
        raise ApiError(
            response.status_code,
            response.json() if 400 <= response.status_code < 500 else None)

    #
    # Records API
    #
    def download_record(self, rec, outdir):
        outdir = pathlib.Path(outdir) / rec.doi.split('/')[1]
        if outdir.exists():
            return outdir
        outdir.mkdir()
        for f in rec.files:
            with tempfile.TemporaryDirectory() as tmp:
                fname = pathlib.Path(tmp) / f.key.split('/')[-1]
                urllib.request.urlretrieve(f.url, str(fname))
                if f.checksum_protocol == 'md5':
                    assert md5(fname) == f.checksum_value
                if f.type == 'zip':
                    z = zipfile.ZipFile(str(fname))
                    z.extractall(str(outdir))
                elif f.type == 'gz':
                    # what about a tar in there?
                    raise NotImplementedError()
                elif f.type == 'gz':
                    raise NotImplementedError()
                else:
                    shutil.move(str(fname), str(outdir / f.key.split('/')[-1]))
        return outdir

    def record_from_id(self, id_):
        if not id_.startswith('http'):
            id_ = 'https://zenodo.org/record/' + id_
        soup = bs(requests.get(id_ + '/export/json').text, features='html.parser')
        return Record(**json.loads(soup.find('pre').text))

    def record_from_doi(self, doi):
        if not doi.startswith('http'):
            doi = 'https://doi.org/{0}'.format(doi)
        res = requests.get(doi)
        assert re.search('zenodo.org/record/[0-9]+$', res.url)
        return self.record_from_id(res.url)

    def iter_records(self, keywords=None, limit=None, community=None, **kw):
        """
        "https://zenodo.org/api/records/?sort=mostrecent&page=2&keywords=cldf&size=2",
        """
        if community:
            for rec in oai.Records(community):
                if not keywords or (keywords in rec.keywords):
                    yield self.record_from_id(rec.id)
            return

        i = 0
        res = self._req('get', prefix='records', path='/', params=dict(keywords=keywords))
        for i, rec in enumerate(res['hits']['hits'][:limit], start=1):
            yield Record(**rec)
        while ('next' in res['links']) and i < limit:
            res = requests.get(res['links']['next']).json()
            for i, rec in enumerate(res['hits']['hits'], start=i):
                if i <= limit:
                    yield Record(**rec)

    #
    # Deposition API
    #
    def list_deposits(self, q=None, status=None, sort=None, page=None, size=10, all_versions=False):
        params = {k: v for k, v in locals().items() if k != 'self' and v}
        return [Deposition.from_dict(d) for d in self._req('get', params=params)]

    def iter_deposits(self, q=None, status=None, sort=None, all_versions=False):
        page, size, i = 1, 10, 0
        for i, d in enumerate(self.list_deposits(
                q=q, status=status, sort=sort, page=page, size=size, all_versions=all_versions)):
            yield d
        while i:
            page += 1
            i = 0
            for i, d in enumerate(self.list_deposits(
                    q=q,
                    status=status,
                    sort=sort,
                    page=page,
                    size=size,
                    all_versions=all_versions)):
                yield d

    def _dep(self, method, **kw):
        return Deposition.from_dict(self._req(method, **kw))

    def create_deposit(self, **md):
        res = self._dep('post', expected=201, data={})
        # FIXME: Should we immediately discard the deposition if updating fails?
        return self.update_deposit(res, **md) if md else res

    def _update(self, dep):
        dep.validate_update()
        return self._dep(
            'put', path='{0}'.format(dep), data={'metadata': dep.metadata.asdict()})

    def retrieve_deposit(self, dep):
        return self._dep('get', path='{0}'.format(dep))

    def delete_deposit(self, dep):
        self._req('delete', path='{0}'.format(dep), expected=201)

    def publish_deposit(self, dep):
        dep.validate_publish()
        return self._dep('post', path='{0}/actions/publish'.format(dep), expected=202)

    def edit_deposit(self, dep):
        return self._dep('post', path='{0}/actions/edit'.format(dep), expected=201)

    def discard_deposit(self, dep):
        return self._dep('post', path='{0}/actions/discard'.format(dep), expected=201)

    def newversion_deposit(self, dep):
        return self._dep('post', path='{0}/actions/newversion'.format(dep), expected=201)

    def update_deposit(self, dep, **kw):
        if not isinstance(dep, Deposition):
            dep = self.retrieve_deposit(dep)

        # We automatically unlock published Depositions for editing:
        published = dep.state == PUBLISHED
        if published:
            print('unlock for editing')
            dep = self.edit_deposit(dep)

        for k, v in kw.items():
            # Set the metadata attributes, thereby triggering validators:
            setattr(dep.metadata, k, v)

        dep = self._update(dep)
        if published:
            print('publish changes')
            dep = self.publish_deposit(dep)
        return dep

    #
    # legacy Deposition File API
    #
    def create_files(self, dep, *paths, **kw):  # pragma: no cover
        for path in paths:
            yield self.create_file(dep, path, verify=kw.get('verify', True))

    def create_file(self, dep, path, verify=True):  # pragma: no cover
        if dep.state != UNSUBMITTED:
            raise ValueError('files can only be uploaded for unsubmitted depositions')
        path = pathlib.Path(path)
        if not path.exists():
            raise ValueError('file to be uploaded does not exist')
        with path.open('rb') as fp:
            res = DepositionFile.from_dict(self._req(
                'post',
                path='{0}/files'.format(dep),
                expected=201,
                data={'filename': path.name},
                files={'file': fp}))
        if verify and res.checksum != md5(path):
            # We delete the deposition file immediately:
            self.delete_file(dep, res)
            raise ValueError('invalid file upload')
        dep.files.append(res)
        return res

    def list_files(self, dep):  # pragma: no cover
        return [
            DepositionFile.from_dict(d) for d in
            self._req('get', path='{0}/files'.format(dep))]

    def sort_files(self, dep, sorted_):  # pragma: no cover
        res = self._req(
            'put',
            path='{0}/files'.format(dep),
            data=[{'id': "{0}".format(d)} for d in sorted_])
        dep.files = [DepositionFile.from_dict(d) for d in res]
        return dep.files

    def retrieve_file(self, dep, depfile):  # pragma: no cover
        return DepositionFile.from_dict(self._req('get', path='{0}'.format(depfile)))

    def update_file(self, dep, depfile, filename):  # pragma: no cover
        return DepositionFile.from_dict(self._req(
            'put', path='{0}/files/{1}'.format(dep, depfile), data={'filename': filename}
        ))

    def delete_file(self, dep, depfile):  # pragma: no cover
        self._req('delete', path='{0}/files/{1}'.format(dep, depfile), expected=204)

"""
Read metadata from Zenodo via a community's OAI-PMH feed.
"""
import re
import html
import functools
import collections
import packaging.version
from xml.etree import ElementTree as ET

import requests

OAI = "https://zenodo.org/oai2d"
OAI_NS = "http://www.openarchives.org/OAI/2.0/"
DATACITE_NS = "http://datacite.org/schema/kernel-3"


def qname(ns, lname):
    return '{%s}%s' % (ns, lname)


oai = functools.partial(qname, OAI_NS)
datacite = functools.partial(qname, DATACITE_NS)


class Metadata(object):
    def __init__(self, e):
        self.e = e

    @property
    def text(self):
        return self.e.text

    def __getitem__(self, item):
        return self.e.attrib[item]

    def __getattr__(self, item):
        if item.endswith('s'):
            return self.getall(item[:-1], parent=self.get(item).e)
        return self.get(item)

    @staticmethod
    def _path(lname):
        return './/{0}'.format(datacite(lname))

    def get(self, lname, parent=None):
        return Metadata((parent or self.e).find(self._path(lname)))

    def getall(self, lname, parent=None):
        return [Metadata(e) for e in (parent or self.e).findall(self._path(lname))]


Repository = collections.namedtuple('Repository', ['org', 'repos'])


class Record:
    def __init__(self, e):
        self.e = e
        self.identifier = self.e.find('.//{0}'.format(oai('identifier')))
        self.metadata = Metadata(self.e.find('.//{0}'.format(datacite('resource'))))
        self.repos = Repository(None, None)
        self.tag = None
        self.version = None
        repos_url_pattern = re.compile(
            r"https://github\.com/(?P<org>[^/]+)/(?P<repos>[^/]+)/tree/(?P<tag>.+)")
        for o in self.metadata.relatedIdentifiers:
            if o['relatedIdentifierType'] == 'URL':
                match = repos_url_pattern.match(o.text)
                if match:
                    self.repos = Repository(match.group('org'), match.group('repos'))
                    self.tag = match.group('tag')
                    self.version = packaging.version.parse(self.tag)
                    break

    @property
    def citation(self):
        for line in requests.get('https://zenodo.org/record/{}'.format(self.id)).text.split('\n'):
            if 'vm.citationResult' in line:
                line = line.split("'", maxsplit=1)[1]
                assert line.endswith("'\"")
                return html.unescape(line[:-2])

    @property
    def id(self):
        return self.identifier.text.split(':')[-1]

    @property
    def doi(self):
        return self.metadata.identifier.text

    @property
    def keywords(self):
        return [e.text for e in self.metadata.subjects]


class OAIXML:
    def __init__(self, xml):
        self.xml = ET.fromstring(xml)

    def __call__(self, lname, parent=None, method='find'):
        return getattr(parent or self.xml, method)('.//{0}'.format(oai(lname)))

    @property
    def resumption_token(self):
        return getattr(self('resumptionToken'), 'text', None)


def request(**params):
    return OAIXML(requests.get(OAI, params=params).text)


class Records(list):
    def __init__(self, community):
        self.community = community
        res = request(
            set='user-{0}'.format(community), metadataPrefix='oai_datacite', verb='ListRecords')
        recs = res('record', method='findall')
        while res.resumption_token:  # pragma: no cover
            res = request(verb='ListRecords', resumptionToken=res.resumption_token)
            recs.extend(res('record', method='findall'))
        list.__init__(self, [Record(e) for e in recs])

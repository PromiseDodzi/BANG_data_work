import datetime

# We use a timestamp format which is compatible with the syntax of CDSTAR bitstream names:
TIMESTAMP_FORMAT = '%Y%m%dT%H%M%SZ'


class RollingBlob(object):
    """
    RollingBlobs are big(gish), versioned files of which only the last couple of versions need to
    be available (such as log files or database dumps).
    """
    def __init__(self, collection=None, name=None, oid=None):
        if not oid:
            if not (collection and name):
                raise ValueError
        else:
            if collection or name:
                raise ValueError
        self.collection = collection
        self.name = name
        self.oid = oid

    @staticmethod
    def parse_timestamp(bsid):
        try:
            return datetime.datetime.strptime(bsid.split('_')[-1].split('.')[0], TIMESTAMP_FORMAT)
        except (ValueError, TypeError):
            # Make sure invalid timestamps are sorted as earlier than any valid ones.
            return datetime.datetime.strptime('19000101T000000Z', TIMESTAMP_FORMAT)

    def get_object(self, cdstar):
        obj = cdstar.get_object(uid=self.oid)
        if self.oid is None:
            self.oid = obj.id
            obj.metadata = {
                'collection': self.collection,
                'name': self.name,
                'type': self.__class__.__name__,
            }
        else:
            md = obj.metadata.read()
            self.name = md['name']
            self.collection = md['collection']
        return obj

    def add(self, cdstar, fname, suffix='', timestamp=None, mimetype=None):
        if '_' in suffix:
            raise ValueError(suffix)
        timestamp = timestamp or datetime.datetime.utcnow()
        if isinstance(timestamp, str):
            timestamp = datetime.datetime.strptime(timestamp, TIMESTAMP_FORMAT)
        if suffix and not suffix.startswith('.'):
            suffix = '.' + suffix
        obj = self.get_object(cdstar)
        kw = dict(
            name='{0}_{1}{2}'.format(self.name, timestamp.strftime(TIMESTAMP_FORMAT), suffix),
            fname=fname)
        if mimetype:
            kw['mimetype'] = mimetype
        obj.add_bitstream(**kw)

    def sorted_bitstreams(self, cdstar):
        obj = self.get_object(cdstar)
        return sorted(obj.bitstreams, key=lambda bs: self.parse_timestamp(bs.id), reverse=True)

    def latest(self, cdstar):
        res = self.sorted_bitstreams(cdstar)
        if res:
            return res[0]

    def expunge(self, cdstar, keep=5):
        deleted = 0
        for i, bs in enumerate(self.sorted_bitstreams(cdstar)):
            if i + 1 > keep:
                bs.delete()
                deleted += 1
        return deleted

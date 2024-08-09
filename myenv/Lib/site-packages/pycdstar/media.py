import os
import hashlib
from string import ascii_letters
import logging
from time import time, strftime
import subprocess
from tempfile import NamedTemporaryFile
import json
from mimetypes import guess_type
import pathlib

from unidecode import unidecode

import pycdstar
from pycdstar.resource import Bitstream


log = logging.getLogger(pycdstar.__name__)


def ensure_unicode(s):
    if not isinstance(s, str):  # pragma: no cover
        s = s.decode('utf8')
    return s


class File(object):
    def __init__(self, path, temporary=False, name=None, type='original', mimetype=None):
        path = pathlib.Path(path)
        assert path.exists() and path.is_file()
        self.path = path
        self.temporary = temporary
        self.bitstream_name = name or self.clean_name
        self.bitstream_type = type
        self._md5 = None
        self.mimetype = mimetype or guess_type(self.path.name, strict=False)[0]

    @property
    def ext(self):
        return self.path.suffix.lower()

    @property
    def clean_name(self):
        valid_characters = ascii_letters + '._0123456789'
        name = ensure_unicode(self.path.name)
        res = ''.join([c if c in valid_characters else '_' for c in unidecode(name)])
        assert Bitstream.NAME_PATTERN.match(res)
        return res

    @property
    def md5(self):
        if self._md5 is None:
            self._md5 = hashlib.md5()
            with self.path.open(mode="rb") as fp:
                self._md5.update(fp.read())
            self._md5 = self._md5.hexdigest()
        return self._md5

    @property
    def size(self):
        return self.path.stat().st_size

    @staticmethod
    def format_size(num):
        suffix = 'B'
        for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)

    @property
    def size_h(self):
        return self.format_size(self.size)

    def add_bitstreams(self):
        return []

    def add_metadata(self):
        return {}

    def create_object(self, api, metadata=None):
        """
        Create an object using the CDSTAR API, with the file content as bitstream.

        :param api:
        :return:
        """
        metadata = {k: v for k, v in (metadata or {}).items()}
        metadata.setdefault('creator', '{0.__name__} {0.__version__}'.format(pycdstar))
        metadata.setdefault('path', '%s' % self.path)
        metadata.update(self.add_metadata())
        bitstream_specs = [self] + self.add_bitstreams()
        obj = api.get_object()
        res = {}
        try:
            obj.metadata = metadata
            for file_ in bitstream_specs:
                res[file_.bitstream_type] = file_.add_as_bitstream(obj)
        except:  # noqa: E722
            obj.delete()
            raise
        return obj, metadata, res

    def add_as_bitstream(self, obj):
        start = time()
        log.info('{0} uploading bitstream {1} for object {2} ({3})...'.format(
            strftime('%H:%M:%S'), self.bitstream_name, obj.id, self.size_h))
        obj.add_bitstream(
            fname=str(self.path), name=self.bitstream_name, mimetype=self.mimetype)
        log.info('... done in {0:.2f} secs'.format(time() - start))
        if self.temporary and self.path.exists():
            self.path.unlink()
        return self.bitstream_name


class Audio(File):
    """
    Audio file handling requires the `lame` command to convert files to mp3.
    """
    def _convert(self):
        with NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            subprocess.check_call(['lame', '--preset', 'insane', str(self.path), fp.name])
        return fp.name

    def add_bitstreams(self):
        if self.mimetype == 'audio/mpeg':
            # we only need an alias with correct name!
            path = self.path
            temporary = False
        else:
            path = self._convert()
            temporary = True
        return [File(path, name='web.mp3', type='web', temporary=temporary)]


class Image(File):
    """
    Image file handling requires ImageMagick's `convert` and `identify` commands to
    create different resolutions of a file and determine its dimensions.
    """
    resolutions = {
        'thumbnail': '-thumbnail 103x103^ -gravity center -extent 103x103'.split(),
        'web': '-resize 357x357'.split(),
    }

    def _convert(self, opts):
        with NamedTemporaryFile(delete=False, suffix='.jpg') as fp:
            subprocess.check_call(['convert', str(self.path)] + opts + [fp.name])
        return fp.name

    def _identify(self):
        res = ensure_unicode(subprocess.check_output(['identify', str(self.path)]))
        assert res.startswith(str(self.path))
        dim = res.replace(str(self.path), '').strip().split()[1]
        return dict(zip(['height', 'width'], map(int, dim.split('x'))))

    def add_bitstreams(self):
        return [
            File(self._convert(opts), temporary=True, name=type_ + '.jpg', type=type_)
            for type_, opts in self.resolutions.items()]

    def add_metadata(self):
        return self._identify()


class Video(File):
    """
    Video file handling requires the `ffmpeg` command to convert files to mp4 and the
    `ffprobe` command to determine the duration of a video.
    """
    def __init__(self, *args, **kw):
        File.__init__(self, *args, **kw)
        self._props = None

    def _ffprobe(self):
        cmd = 'ffprobe -loglevel quiet -print_format json -show_streams'.split()
        return json.loads(ensure_unicode(subprocess.check_output(cmd + [str(self.path)])))

    @property
    def duration(self):
        if self._props is None:
            self._props = self._ffprobe()
        return float(self._props['streams'][0]['duration'])

    def _ffmpeg(self, iopts, opts, suffix):
        with NamedTemporaryFile(delete=False, suffix=suffix) as fp:
            if os.path.exists(fp.name):
                os.remove(fp.name)
            subprocess.check_call(
                ['ffmpeg'] + iopts + ['-i', str(self.path)] + opts + [fp.name])
        return fp.name

    def add_bitstreams(self):
        thumbnail_offset = '-{0}'.format(min([int(self.duration / 2), 20]))
        res = [File(
            self._ffmpeg(
                ['-itsoffset', thumbnail_offset],
                ['-vcodec', 'mjpeg', '-vframes', '1', '-an', '-f', 'rawvideo'],
                '.jpg'),
            temporary=True,
            name='thumbnail.jpg',
            type='thumbnail')]

        if self.ext in ['.mov', '.qt', '.mod', '.avi']:
            res.append(File(
                self._ffmpeg([], '-c:v libx264'.split(), '.mp4'),
                name=os.path.splitext(self.clean_name)[0] + '.mp4',
                type='mp4'))

        return res

    def add_metadata(self):
        return {'duration': self.duration}

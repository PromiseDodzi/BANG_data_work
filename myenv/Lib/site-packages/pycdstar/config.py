import os
import logging
from configparser import RawConfigParser

from appdirs import AppDirs

APP_DIRS = AppDirs('pycdstar')


class NoDefault(object):
    pass


NO_DEFAULT = NoDefault()


class Config(RawConfigParser):
    def __init__(self, **kw):
        cfg_path = kw.pop('cfg', None) \
            or os.path.join(APP_DIRS.user_config_dir, 'config.ini')
        cfg_path = os.path.abspath(cfg_path)

        RawConfigParser.__init__(self)

        if os.path.exists(cfg_path):
            assert os.path.isfile(cfg_path)
            self.read(cfg_path)
        else:
            self.add_section('service')
            for opt in 'url user password'.split():
                self.set('service', opt, kw.get(opt, '') or '')
            self.add_section('logging')
            self.set('logging', 'level', 'INFO')

            config_dir = os.path.dirname(cfg_path)
            if not os.path.exists(config_dir):
                try:
                    os.makedirs(config_dir)
                except OSError:  # pragma: no cover
                    # this happens when run on travis-ci, by a system user.
                    pass
            if os.path.exists(config_dir):
                with open(cfg_path, 'w') as fp:
                    self.write(fp)
        level = self.get('logging', 'level', default=None)
        if level:
            logging.basicConfig(level=getattr(logging, level))

    def get(self, section, option, default=NO_DEFAULT):
        if default is not NO_DEFAULT:
            if not self.has_option(section, option):
                return default
        return RawConfigParser.get(self, section, option)

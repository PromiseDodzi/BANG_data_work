import pathlib
import collections

from clldutils import jsonlib


class Deposits:
    def __init__(self, path):
        self.path = pathlib.Path(path)
        if self.path.exists():
            self.objects = collections.OrderedDict([
                (o['id'], o) for o in
                jsonlib.load(self.path, object_pairs_hook=collections.OrderedDict)])
        else:
            self.objects = collections.OrderedDict()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        jsonlib.dump(sorted(self.objects.values(), key=lambda o: o['id']), self.path, indent=4)

    def add(self, dep):
        dep = dep.to_dict()
        self.objects[dep['id']] = dep

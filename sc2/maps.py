def get(name=None):
    maps = []
    try:
        from .paths import Paths
    except:
        return maps
    for mapdir in (p for p in Paths.MAPS.iterdir() if p.is_dir()):
        for mapfile in (p for p in mapdir.iterdir() if p.is_file()):
            if mapfile.suffix == ".SC2Map":
                maps.append(Map(mapfile))

    if name is None:
        return maps

    for m in maps:
        if m.matches(name):
            return m

    # raise KeyError(f"Map '{name}' was not found")
    print(f"Map '{name}' was not found")

class Map(object):
    def __init__(self, path):
        self.path = path

    @property
    def name(self):
        return self.path.stem

    @property
    def data(self):
        with open(self.path, "rb") as f:
            return f.read()

    def matches(self, name):
        return self.name.lower().replace(" ", "") == name.lower().replace(" ", "")

    def __repr__(self):
        return f"Map({self.path})"

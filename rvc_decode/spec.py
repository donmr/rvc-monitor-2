from ruamel.yaml import YAML

_yaml = YAML()


def load_spec(path):
    with open(path, 'r') as specfile:
        return _yaml.load(specfile)


def merge_specs(*specs):
    """Merge spec dicts left-to-right; on key collisions, later args win (same as dict `|`)."""
    merged = {}
    for s in specs:
        merged |= s
    return merged

import ruamel.yaml as yaml


def load_spec(path):
    with open(path, 'r') as specfile:
        return yaml.round_trip_load(specfile)


def merge_specs(*specs):
    """Merge spec dicts left-to-right; on key collisions, later args win (same as dict `|`)."""
    merged = {}
    for s in specs:
        merged |= s
    return merged

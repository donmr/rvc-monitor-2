from collections import namedtuple

ArbitrationId = namedtuple('ArbitrationId', ['priority', 'dgn', 'source_address'])


def parse_arbitration_id(arbitration_id):
    bits = "{0:029b}".format(arbitration_id)
    priority = int(bits[0:3], 2)
    dgn = "{0:05X}".format(int(bits[4:21], 2))
    source_address = "{0:02X}".format(int(bits[24:], 2))
    return ArbitrationId(priority, dgn, source_address)

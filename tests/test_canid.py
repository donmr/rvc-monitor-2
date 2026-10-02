from rvc_decode import parse_arbitration_id


def test_parses_typical_extended_id():
    result = parse_arbitration_id(0x19FEDB99)
    assert result.priority == 6
    assert result.dgn == "1FEDB"
    assert result.source_address == "19"


def test_zero_padding_with_leading_zero_bits():
    # Top bits of this 29-bit ID are 0. A non-zero-padded binary string would
    # come out shorter than 29 characters, so the fixed-position slices used
    # to grab the wrong bits (or raise on an empty slice). Padding to 29 bits
    # keeps the field positions correct regardless of the leading bits.
    result = parse_arbitration_id(0x00FEDB99)
    assert result.priority == 0
    assert result.dgn == "0FEDB"
    assert result.source_address == "19"

from rvc_decode import rvc_decode, get_bytes, get_bits, parameterize_string


def test_get_bytes_single_index():
    assert get_bytes("0102030405060708", 0) == "01"
    assert get_bytes("0102030405060708", 3) == "04"


def test_get_bytes_range_is_little_endian():
    # bytes 0-1 on the wire combine to the 16-bit value 0x0201
    assert get_bytes("0102030405060708", "0-1") == "0201"


def test_get_bits_single_bit():
    # 0x05 == 0b00000101
    assert get_bits(0x05, 0) == "1"
    assert get_bits(0x05, 1) == "0"


def test_get_bits_range():
    assert get_bits(0b00001100, "2-3") == "11"


def test_parameterize_string():
    assert parameterize_string("Manufacturer Code (LSB) in/out") == "manufacturer_code_lsb_in_out"


def test_rvc_decode_unknown_dgn_falls_back(spec):
    result = rvc_decode("FFFFF", "0000000000000000", spec)
    assert result["name"] == "UNKNOWN-FFFFF"


def test_rvc_decode_enum_values_populate_definition_field(spec):
    # Regression check for the parameterized_strings dead-code removal:
    # enumerated 'values' lookups must actually populate "<name> definition".
    result = rvc_decode("1FE9F", "FA47040000FFFFFF", spec)
    assert result["name"] == "GENERIC_ALARM_STATUS"
    assert result["Alarm Triggered definition"] == "alarm not triggered"

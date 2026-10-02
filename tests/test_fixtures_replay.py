import json

from rvc_decode import rvc_decode


def _load_fixture_lines(fixtures_dir, name):
    with open(fixtures_dir / name) as f:
        return [json.loads(line) for line in f if line.strip()]


def test_view_boot_trace_unique_decodes_without_error(spec, fixtures_dir):
    records = _load_fixture_lines(fixtures_dir, "view_boot_trace_unique.rvc")
    assert len(records) > 1000
    for record in records:
        result = rvc_decode(record["dgn"], record["data"], spec)
        assert "name" in result


def test_solar_fixture_decodes_without_error(spec, fixtures_dir):
    records = _load_fixture_lines(fixtures_dir, "solar.rvc")
    assert records
    for record in records:
        result = rvc_decode(record["dgn"], record["data"], spec)
        assert "name" in result

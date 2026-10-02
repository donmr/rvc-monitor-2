# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A monitor/decoder for the RV-C CAN-Bus protocol (and a bit of SAE J1939), used on RVs with a CAN interface
(typically a Raspberry Pi + PiCAN2/MCP2515 board). It reads frames off a CAN bus (or replays a previously
captured file), decodes them against YAML protocol spec files, and emits one JSON object per message.

This is a fresh rewrite ("rvc-monitor-2") of an earlier project; see `NOTICE` for lineage. No build step —
everything runs directly as Python 3 scripts.

## Running it

The entry point is `usr/bin/rvc-monitor-2`, a thin wrapper that calls the Python script with the repo-local spec file:

```
./myrun                       # runs: ./usr/bin/rvc-monitor-2 -s etc/rvc/rvc-spec.yml
./usr/bin/rvc-monitor-2 -i can0                       # live decode from a CAN interface, JSON to stdout
./usr/bin/rvc-monitor-2 -r solar.rvc                  # replay a captured JSON-lines file instead of live CAN
./usr/bin/rvc-monitor-2 -d 1 -i can0                  # with debug tracing to stderr
```

Key flags (see `usr/bin/rvc-monitor-2` argparse block): `-i/--interface` (CAN iface, default `can0`),
`-r/--replay` (read a previously saved `.rvc` JSON-lines file instead of a live bus — mutually exclusive with
live CAN), `-s/--specfile` (RV-C spec YAML, default `/etc/rvc/rvc-spec.yml`), `-j/--j1939specfile` (SAE J1939
spec YAML, default `/etc/rvc/sae-j1939.yml`), `-d/--debug {0,1,2}`.

All informational/debug output goes to **stderr**; decoded JSON results go to **stdout** only — this keeps
`stdout` pipeable (e.g. into `jq`, or saved as a `.rvc` capture file for later `-r` replay).

There is no MQTT publishing in the current `usr/bin/rvc-monitor-2` tool. `usr/bin/rvc2mqtt.py` (untracked,
WIP) is an older sibling script that still has MQTT publish/subscribe logic (`paho.mqtt`) and a slightly
different CLI (`-b/--broker`, `-m/--mqtt`, `-o/--output`, `-t/--topic`, `-p/--pstrings`) — treat it as a
reference for re-adding MQTT support, not as the maintained tool; it has its own copy of the decode logic
that has drifted from `rvc_decode/` (below). The `etc/default/rvc2mqtt` env file and
`etc/systemd/system/rvc2mqtt@.service` systemd unit both still target that MQTT-era script/CLI
(`/usr/bin/rvc2mqtt.py`), not `rvc-monitor-2` — keep that mismatch in mind when touching deployment files.

Dependencies (`requirements.txt`): `python-can`, `ruamel.yaml`, `paho.mqtt`, `pytest`. Install with
`pip3 install -r requirements.txt`. Note the installed `ruamel.yaml` must still support the deprecated
`round_trip_load`/`round_trip_load_all` API (used throughout `rvc_decode/spec.py`) — the apt package
`python3-ruamel.yaml` (0.17.x) works; a fresh `pip install ruamel.yaml` can pull a newer release that removed
it entirely.

## Tests

Unit/integration tests live in `tests/` (pytest). Run with `pytest` from the repo root.

- `tests/conftest.py` provides a session-scoped `spec` fixture (merged RV-C + J1939 spec) and a `fixtures_dir`
  fixture.
- `tests/test_canid.py`, `test_spec.py`, `test_decoder.py` are unit tests against the `rvc_decode` package.
- `tests/test_fixtures_replay.py` replays the small fixtures under `tests/fixtures/` end-to-end and asserts
  every record decodes without raising.
- The root-level `conftest.py` (empty) exists only so pytest's import-mode puts the repo root on `sys.path`,
  letting test modules `import rvc_decode` regardless of invocation directory.

Larger/raw `.rvc` captures (full boot traces, etc.) live in `Captures/`, which is gitignored — that's where to
drop new real-world captures without bloating the repo; promote a trimmed/deduplicated sample into
`tests/fixtures/` if it's worth keeping as a regression fixture.

## Architecture

**`rvc_decode/` is a standalone package** holding all decode logic, deliberately separated from CAN-bus I/O,
threading, and CLI handling so other programs can decode RV-C/J1939 frames without pulling in `python-can`:
- `decoder.py`: `rvc_decode(dgn, data, spec)` — the core per-DGN decode; `get_bytes`/`get_bits` (byte/bit range
  extraction); `parameterize_string`.
- `units.py`: `convert_unit`, `tempC2F` — pure value-scaling functions.
- `canid.py`: `parse_arbitration_id(arbitration_id)` — splits a 29-bit extended CAN ID into
  `(priority, dgn, source_address)` via a *zero-padded* binary string (padding matters: an unpadded format on
  an ID with leading zero bits silently mis-slices the fields).
- `spec.py`: `load_spec(path)` (parses one YAML spec file) and `merge_specs(*specs)` (dict-union merge,
  **later args win** on key collisions).
- `__init__.py` re-exports the full public surface; `usr/bin/rvc-monitor-2` imports from it via a `sys.path`
  bootstrap relative to its own file location (the package isn't pip-installed — it's a plain importable
  directory at the repo root).

**Decode pipeline**, driven from `usr/bin/rvc-monitor-2`:
1. A background thread (`CANWatcher`) reads raw frames from `python-can` and pushes them onto a `queue.Queue`.
   In replay mode (`-r`) there's no bus/thread at all — lines are read directly from the replay file instead.
2. The main loop (`getLine`) pulls one message at a time, calls `parse_arbitration_id` to get
   `prio`/`dgn`/`src`, then calls `rvc_decode(dgn, hex_data, spec)` where `spec` is the merged RV-C+J1939 spec
   dict built once at startup (`merge_specs(load_spec(rvc_specfile), load_spec(j1939_specfile))`).
3. `rvc_decode` looks up the DGN in `spec`, applies each `parameter` definition to pull bytes/bits out of the
   raw hex payload, converts units, and resolves enumerated `values`.
4. Result is a flat dict (`dgn`/`pri`/`src` + decoded fields) printed as one JSON line to stdout. If a DGN has
   no spec entry, or none of its parameters matched (`param_count == 0`), the output carries a
   `DECODER PENDING` / `UNKNOWN-<dgn>` marker instead of failing — decoding is best-effort and intentionally
   never raises on a bad/partial match (every per-parameter conversion is wrapped in a bare `try/except: pass`).

**Spec files are the real logic**, not the Python code — `etc/rvc/rvc-spec.yml` and `etc/rvc/sae-j1939.yml`
are YAML keyed by 5-hex-digit DGN/PGN, each with a `name` and a `parameters` list. Each parameter entry
describes *how to extract a value from the raw payload*, not just what it's called:
- `byte`: a single index, or `"lo-hi"` byte range (multi-byte fields are little-endian; see `get_bytes`,
  which reverses byte order for ranges).
- `bit`: optional sub-byte range (`"lo-hi"`), extracted via `get_bits` from the 8-bit binary string.
- `type`: `uintN` for numeric fields, `bit`/`bitmap` for flag fields, `ascii` for text.
- `unit`: drives `convert_unit`'s scaling (`pct`, `deg C`, `V`, `A`, `W`, `Ah`, `Ohm`, `Hz`, `sec`, `bitmap`,
  plus J1939's `rpm`) — these encode the RV-C spec's documented scale factors and "not available" sentinel
  values (e.g. `0xFF`/`0xFFFF` means "n/a" for most analog fields), so get them right rather than
  reverse-engineering scaling in Python.
- `values`: maps decoded integer values to human-readable enum strings (adds a `"<name> definition"` field).
- `alias`: a DGN entry can borrow another DGN's `parameters` list (see usage in `rvc_decode`) for near-duplicate
  messages.

**`rvc-spec.yml` is explicitly versioned** (`API_VERSION` field) — it states in its own header comment that
changes to field names/casing can break downstream MQTT consumers, so treat renames there as a compat-breaking
change, not a free-form edit.

`etc/rvc/rvc_table2yaml.py` is a one-off generator: given the official RVIA DGN table
(`etc/rvc/RV-C_DGN_Table_RVIA.txt`, a whitespace-columnar text dump) and an existing `rvc-spec.yml`, it adds
stub `{name: ...}` entries for any DGN present in the table but missing from the spec (it does not overwrite
existing entries). Run it after refreshing the RVIA table to pick up newly-documented DGNs as unparsed stubs.

## Capture/replay file format (`.rvc` files)

Files like `solar.rvc`, `view_boot_trace.rvc` are just captured stdout from a live run: one JSON object per
line, `{"dgn", "pri", "src", "data", ...decoded fields}`. `*_decoded.rvc` files are the same capture after
spec parameters were resolved (more fields present). These are useful as realistic fixtures when changing
decode logic — diff decoded output before/after a change against a known-good `*_decoded.rvc` file rather than
needing a live CAN bus. See "Tests" above for where captures/fixtures actually live in this repo.

## Licensing

Apache 2.0 (see `LICENSE`). `NOTICE` records that this project started from
https://github.com/linuxkidd/rvc-monitor-py with the MPPT solar-charger function removed and the RVC/J1939
specs updated — keep `NOTICE` accurate if further code is carried over from or contributed back to upstream
projects.

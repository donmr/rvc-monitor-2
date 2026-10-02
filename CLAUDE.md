QTTLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working
with code in this repository.

## What this is

A monitor/decoder for the RV-C CAN-Bus protocol (and a bit of SAE J1939),
used on RVs with a CAN interface.  It reads frames off a CAN bus (or replays
a previously captured file), decodes them against YAML protocol spec files,
and emits one JSON object per message.

This is a fresh rewrite ("rvc-monitor-2") of an earlier project; see
`NOTICE` for lineage. The repo is small, has no automated test suite,
and no build step — everything runs directly as Python 3 scripts.

## Running it

The entry point is `usr/bin/rvc-monitor-2`, a thin wrapper that calls the Python script with the repo-local spec file:

```
./test                       # runs: ./usr/bin/rvc-monitor-2 -s etc/rvc/rvc-spec.yml
./usr/bin/rvc-monitor-2 -i can0                       # live decode from a CAN interface, JSON to stdout
./usr/bin/rvc-monitor-2 -r solar.rvc                  # replay a captured JSON-lines file instead of live CAN
```

Key flags (see `usr/bin/rvc-monitor-2` argparse block): 
    `-i/--interface` (CAN iface, default `can0`), 
    `-r/--replay` (read a previously saved `.rvc` JSON-lines file instead of a live bus),
    `-s/--specfile` (RV-C spec YAML, default `/etc/rvc/rvc-spec.yml`),
    `-j/--j1939specfile` (SAE J1939 spec YAML, default `/etc/rvc/sae-j1939.yml`),

All informational/debug output goes to **stderr**; decoded JSON results
go to **stdout** only — this keeps `stdout` pipeable (e.g. into `jq`,
or saved as a `.rvc` capture file for later `-r` replay).

Dependencies (`requirement.txt`, note the non-standard filename — not `requirements.txt`):
`python-can`, `ruamel.yaml`. Install with `pip3 install -r requirement.txt`.

## Architecture

**Decode pipeline** (`usr/bin/rvc-monitor-2`):
1. A background thread (`CANWatcher`) reads raw frames from `python-can` and pushes them onto a `queue.Queue`.
   In replay mode (`-r`) there's no bus/thread at all — lines are read directly from the replay file instead.
2. The main loop (`getLine`) pulls one message at a time, extracts `prio`/`dgn`/`src` from the 29-bit extended
   CAN arbitration ID by slicing its binary string representation (bits 0-2 = priority, 4-20 = DGN, 24-31 =
   source address), then calls `rvc_decode(dgn, hex_data)`.
3. `rvc_decode` looks up the DGN in the merged spec dict (`spec = rvc_spec | sae_spec`, so J1939 entries can be
   overridden/supplemented by RV-C ones with the same key), applies each `parameter` definition from the spec
   to pull bytes/bits out of the raw hex payload, converts units, and resolves enumerated `values`.
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

`etc/rvc/rvc_table2yaml.py` is a one-off generator: given the official RVIA DGN table
(`etc/rvc/RV-C_DGN_Table_RVIA.txt`, a whitespace-columnar text dump) and an existing `rvc-spec.yml`, it adds
stub `{name: ...}` entries for any DGN present in the table but missing from the spec (it does not overwrite
existing entries). Run it after refreshing the RVIA table to pick up newly-documented DGNs as unparsed stubs.

## Capture/replay file format (`.rvc` files)

Files like `solar.rvc`, `view_boot_trace.rvc` are just captured stdout from a live run: one JSON object per
line, `{"dgn", "pri", "src", "data", ...decoded fields}`. `*_decoded.rvc` files are the same capture after
spec parameters were resolved (more fields present). These are useful as realistic fixtures when changing
decode logic — diff decoded output before/after a change against a known-good `*_decoded.rvc` file rather than
needing a live CAN bus.

## Licensing

Apache 2.0 (see `LICENSE`). `NOTICE` records that this project started from
https://github.com/linuxkidd/rvc-monitor-py with the MQTT function removed and the RVC/J1939
specs updated — keep `NOTICE` accurate if further code is carried over from or contributed back to upstream
projects.

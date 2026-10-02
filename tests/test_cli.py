import json
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "usr" / "bin" / "rvc-monitor-2"
RVC_SPEC = REPO_ROOT / "etc" / "rvc" / "rvc-spec.yml"
J1939_SPEC = REPO_ROOT / "etc" / "rvc" / "sae-j1939.yml"

# ELECTRONIC_ENGINE_CONTROLLER_1 is SAE J1939 DGN 0F004 - only resolvable
# when the J1939 spec is loaded alongside the RV-C one.
J1939_ONLY_RECORD = {"dgn": "0F004", "pri": 6, "src": "1A", "data": "FFFFFFFFFFFFFFFF"}


def _run_replay(tmp_path, *specfile_args):
    replay_file = tmp_path / "replay.rvc"
    replay_file.write_text(json.dumps(J1939_ONLY_RECORD) + "\n")
    return subprocess.run(
        [sys.executable, str(SCRIPT), "-r", str(replay_file), *specfile_args],
        capture_output=True, text=True, timeout=10,
    )


def test_multiple_s_flags_merge_specs(tmp_path):
    result = _run_replay(tmp_path, "-s", str(RVC_SPEC), "-s", str(J1939_SPEC))
    assert result.returncode == 0, result.stderr
    decoded = json.loads(result.stdout.strip())
    assert decoded["name"] == "ELECTRONIC_ENGINE_CONTROLLER_1"
    assert decoded["Engine Speed"] == 65535


def test_single_s_flag_replaces_default_rather_than_appending(tmp_path):
    result = _run_replay(tmp_path, "-s", str(RVC_SPEC))
    assert result.returncode == 0, result.stderr
    decoded = json.loads(result.stdout.strip())
    # Without the J1939 spec also loaded, this DGN is unresolvable.
    assert decoded["name"] == "UNKNOWN-0F004"


def test_j_flag_no_longer_exists(tmp_path):
    result = _run_replay(tmp_path, "-j", str(J1939_SPEC))
    assert result.returncode != 0
    assert "unrecognized arguments" in result.stderr.lower()

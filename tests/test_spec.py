import pathlib

from rvc_decode import load_spec, merge_specs

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_merge_specs_right_hand_wins_on_collision():
    a = {"X": 1, "SHARED": "from_a"}
    b = {"Y": 2, "SHARED": "from_b"}
    assert merge_specs(a, b) == {"X": 1, "Y": 2, "SHARED": "from_b"}


def test_merge_specs_with_no_args_returns_empty_dict():
    assert merge_specs() == {}


def test_load_spec_reads_known_dgn():
    spec = load_spec(REPO_ROOT / "etc/rvc/rvc-spec.yml")
    assert spec["17F00"]["name"] == "GENERAL_RESET"

import pathlib

import pytest

from rvc_decode import load_spec, merge_specs

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURES_DIR = pathlib.Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(scope="session")
def spec():
    return merge_specs(
        load_spec(REPO_ROOT / "etc/rvc/rvc-spec.yml"),
        load_spec(REPO_ROOT / "etc/rvc/sae-j1939.yml"),
    )


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR

"""The explorer's algorithm (scripts/build_explorer_data.py, a line-by-line mirror of
explorer/paired.js) reproduces every official value of both references. The page's own
JavaScript is checked by scripts/check_explorer_js.mjs inside scripts/reproduce.py."""

import importlib.util
import json

import pytest

from casestudy import ROOT

spec = importlib.util.spec_from_file_location("build_explorer_data", ROOT / "scripts" / "build_explorer_data.py")
bed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bed)


@pytest.fixture(scope="module", params=["reward", "triage"])
def case(request):
    built = bed.build(request.param, bed.CASES[request.param])
    return json.loads(json.dumps(built))  # as the page reads it


def test_explorer_reproduces_the_references(case):
    verify = bed.verify_reward if case["case"] == "reward" else bed.verify_triage
    assert verify(case) > 0


def test_explorer_empty_selection(case):
    m = next(iter(case["data"]))
    assert bed.estimate(case, m, next(iter(case["contrasts"])), []) is None

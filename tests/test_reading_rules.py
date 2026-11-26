"""The pre-registered reading rules of case 1 (casestudy.read_awake, read_well, read_why),
checked line by line, including the boundaries where a CI bound touches a cut exactly."""
import pytest

import casestudy as cs
from casestudy import read_awake, read_well, read_why

D = cs.DELTA_A  # 0.02
M = cs.MARGIN_WELL  # 0.032

SLEEPS_MORE = "no: with the reward the pet sleeps more"
SAME = "no: stays the same"
UP_SMALL = "goes up, but below the relevant size"
YES = "yes, stays awake more"
INCONCLUSIVE = "inconclusive"


def test_constants_are_the_preregistered_ones():
    assert D == cs.REF["preregistered"]["delta_a"] == 0.02
    assert M == cs.REF["preregistered"]["margin_well"] == 0.032


# ---- L-AWAKE: "upper < 0" first, then "inside [-delta, +delta]", then "lower > delta" ----


@pytest.mark.parametrize(
    ("lo", "hi", "label"),
    [
        (-0.0113, -0.0105, SLEEPS_MORE),  # the official D1 interval
        (-0.5, -1e-12, SLEEPS_MORE),  # far below -delta still reads "sleeps more": upper < 0 wins
        (-0.01, 0.0, SAME),  # upper exactly 0 is not "< 0": falls to the band
        (-0.01, 0.01, SAME),
        (-D, D, SAME),  # both bounds touching +-delta are inside the band (<=)
        (-D, 0.0, SAME),
        (0.0, 0.01, SAME),  # lower exactly 0 is not "> 0": no sub-label
        (1e-12, 0.01, UP_SMALL),
        (0.005, D, UP_SMALL),  # upper touching +delta, lower above 0
        (D, D, UP_SMALL),  # a degenerate interval at +delta is still inside the band
        (D + 1e-12, 0.05, YES),
        (D, 0.05, INCONCLUSIVE),  # lower touching +delta is not "> delta", upper outside the band
        (0.01, D + 1e-12, INCONCLUSIVE),  # upper just outside the band, lower not above delta
        (-D - 1e-12, 0.01, INCONCLUSIVE),  # lower just outside the band, upper >= 0
        (-D - 1e-12, 0.0, INCONCLUSIVE),
        (-0.1, 0.1, INCONCLUSIVE),
    ],
)
def test_read_awake(lo, hi, label):
    assert read_awake(lo, hi) == label


def test_read_awake_delta_argument():
    assert read_awake(-0.04, 0.04) == INCONCLUSIVE
    assert read_awake(-0.04, 0.04, delta=0.04) == SAME


# ---- L-WELL: "lower > 0", then "lower > -margin", then "upper < -margin" ----


@pytest.mark.parametrize(
    ("lo", "hi", "label"),
    [
        (0.0152, 0.0215, "the pet is better off"),  # the official D1 interval on time well
        (1e-12, 0.1, "the pet is better off"),
        (0.0, 0.1, "not worse"),  # lower exactly 0 is not "> 0"
        (-M + 1e-12, 0.0, "not worse"),
        (-M, 0.0, INCONCLUSIVE),  # lower touching -margin is not "> -margin"
        (-0.1, -M, INCONCLUSIVE),  # upper touching -margin is not "< -margin"
        (-0.1, -M - 1e-12, "worse"),
        (-0.1, 0.1, INCONCLUSIVE),
    ],
)
def test_read_well(lo, hi, label):
    assert read_well(lo, hi) == label


def test_read_well_margin_argument():
    assert read_well(-0.04, 0.01) == INCONCLUSIVE
    assert read_well(-0.04, 0.01, margin=0.05) == "not worse"


# ---- L-WHY: only when L-AWAKE is not "stays the same"; the dose premise first ----

BODY = cs.WHY_BODY


@pytest.mark.parametrize("awake", [SAME, UP_SMALL])
def test_read_why_not_applied_when_awake_stays_the_same(awake):
    assert read_why(awake, 1.0, 1.0, True) is None
    assert read_why(awake, -1.0, -1.0, False) is None


@pytest.mark.parametrize("awake", [SLEEPS_MORE, YES, INCONCLUSIVE])
@pytest.mark.parametrize(
    ("d2_lo", "d3_lo", "dose", "label"),
    [
        (0.01, 0.01, True, "by the timely reward and by what the pet learns"),
        (-0.01, 0.01, True, "by the credit, at any time"),
        (0.0, 0.01, True, "by the credit, at any time"),  # D2 lower exactly 0 is not "> 0"
        (0.01, -0.01, True, "not defined by the plan"),
        (0.01, 0.0, True, "not defined by the plan"),  # D3 lower exactly 0 is not "> 0"
        (0.0, 0.0, True, BODY),
        (-0.01, -0.01, True, BODY),
        (0.01, 0.01, False, BODY),  # dose premise failed: only the body answer can come out
        (-0.01, -0.01, False, BODY),
    ],
)
def test_read_why(awake, d2_lo, d3_lo, dose, label):
    assert read_why(awake, d2_lo, d3_lo, dose) == label


def test_official_readings_from_the_published_data():
    """The three rules applied to the published extract give the official labels."""
    a, w = cs.contrast("D1", "awake_frac_d1_14"), cs.contrast("D1", "time_well")
    d2, d3 = cs.contrast("D2", "awake_frac_d1_14"), cs.contrast("D3", "awake_frac_d1_14")
    l_awake = read_awake(a["ci_low"], a["ci_high"])
    got = {
        "L-AWAKE": l_awake,
        "L-WELL": read_well(w["ci_low"], w["ci_high"]),
        "L-WHY": read_why(l_awake, d2["ci_low"], d3["ci_low"], cs.REF["dose_premise_held"]),
    }
    assert got == {k: v["label"] for k, v in cs.REF["readings"].items()}

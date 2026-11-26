"""The exploratory helpers (casestudy/explore.py) on synthetic data: TOST against statsmodels and
against the interval it is equivalent to, the bootstrap's determinism, and the precision
arithmetic against its own simulation."""

import numpy as np
import pytest
from statsmodels.stats.weightstats import ttost_paired

import casestudy as cs
from casestudy import explore


@pytest.fixture
def d():
    return np.random.default_rng(1).normal(-0.004, 0.01, 60)


def test_tost_matches_statsmodels(d):
    r = explore.tost_paired(d, 0.01)
    p, (t_low, p_low, _), (t_high, p_high, _) = ttost_paired(d, np.zeros_like(d), -0.01, 0.01)
    assert r["p"] == pytest.approx(p, rel=1e-10)
    assert (r["t_low"], r["p_low"]) == pytest.approx((t_low, p_low), rel=1e-10)
    assert (r["t_high"], r["p_high"]) == pytest.approx((t_high, p_high), rel=1e-10)


@pytest.mark.parametrize("delta", [0.002, 0.005, 0.007, 0.01, 0.02])
def test_tost_at_0_025_is_the_95_interval_inside_the_band(d, delta):
    ci = cs.summarize(d)
    inside = -delta < ci["ci_low"] and ci["ci_high"] < delta
    assert (explore.tost_paired(d, delta)["p"] < 0.025) == inside


def test_smallest_margin():
    assert explore.smallest_margin(-0.0113, -0.0105) == 0.0113
    assert explore.smallest_margin(-0.002, 0.005) == 0.005


def test_bootstrap_is_deterministic_and_close_to_t(d):
    a, b = explore.bootstrap_ci(d, seed=7), explore.bootstrap_ci(d, seed=7)
    assert a == b
    ci = cs.summarize(d)
    assert a[0] < ci["mean"] < a[1]
    assert a == pytest.approx((ci["ci_low"], ci["ci_high"]), abs=0.15 * (ci["ci_high"] - ci["ci_low"]))


def test_prob_ci_inside_limits():
    assert explore.prob_ci_inside(0.0, 0.03, 2000, 0.032) == pytest.approx(1.0)
    assert explore.prob_ci_inside(0.1, 0.03, 200, 0.032) == pytest.approx(0.0, abs=1e-12)
    assert explore.prob_ci_inside(0.0, 0.03, 3, 0.032) == 0.0  # the half-width alone exceeds delta


def test_prob_ci_inside_agrees_with_simulation():
    p = explore.prob_ci_inside(0.024, 0.031, 200, 0.032)
    s = explore.simulate_prob_ci_inside(0.024, 0.031, 200, 0.032, reps=20_000, seed=3)
    assert s == pytest.approx(p, abs=0.01)

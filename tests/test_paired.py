"""summarize, paired_differences (case 1) and the triage helpers (case 2) on tiny synthetic
tables, against a hand calculation; then each against one official value of the published data."""
import math

import duckdb
import numpy as np
import pandas as pd
import pytest
from scipy import stats

import casestudy as cs
from casestudy import triage


def test_summarize_by_hand():
    d = np.array([1.0, 2.0, 3.0, 4.0])
    # mean 2.5; squared deviations 2.25 + 0.25 + 0.25 + 2.25 = 5, over n - 1 = 3
    sd = math.sqrt(5 / 3)
    half = stats.t.ppf(0.975, 3) * sd / math.sqrt(4)
    r = cs.summarize(d)
    assert r["n"] == 4
    assert r["mean"] == pytest.approx(2.5, abs=1e-15)
    assert r["sd"] == pytest.approx(sd, rel=1e-15)
    assert r["ci_low"] == pytest.approx(2.5 - half, rel=1e-14)
    assert r["ci_high"] == pytest.approx(2.5 + half, rel=1e-14)
    assert r["dz"] == pytest.approx(2.5 / sd, rel=1e-15)
    assert stats.t.ppf(0.975, 3) == pytest.approx(3.182446305284263, rel=1e-12)  # the tabulated t(0.975; 3)


def test_summarize_ci_is_symmetric_and_shrinks_with_n():
    rng = np.random.default_rng(0)
    d = rng.normal(0.1, 1.0, 50)
    r = cs.summarize(d)
    assert r["mean"] - r["ci_low"] == pytest.approx(r["ci_high"] - r["mean"], rel=1e-12)
    wide = cs.summarize(d[:10])
    assert (wide["ci_high"] - wide["ci_low"]) > (r["ci_high"] - r["ci_low"])


def _lives_view(rows):
    con = duckdb.connect()
    con.register("synthetic", pd.DataFrame(rows, columns=["arm", "owner", "place", "unit", "m"]))
    con.execute("CREATE VIEW lives AS SELECT * FROM synthetic")
    return con


def test_paired_differences_by_hand(monkeypatch):
    # 2 units x 2 cells x 2 arms; the per-unit difference is the mean over the cells of (A - B)
    rows = [
        ("A", "o1", "p1", 1, 0.50), ("B", "o1", "p1", 1, 0.40),  # cell diff 0.10
        ("A", "o2", "p1", 1, 0.20), ("B", "o2", "p1", 1, 0.50),  # cell diff -0.30
        ("A", "o1", "p1", 2, 0.90), ("B", "o1", "p1", 2, 0.60),  # cell diff 0.30
        ("A", "o2", "p1", 2, 0.70), ("B", "o2", "p1", 2, 0.60),  # cell diff 0.10
        ("C", "o1", "p1", 1, 9.00), ("C", "o1", "p1", 2, 9.00),  # a third arm, ignored
    ]
    monkeypatch.setattr(cs, "_con", _lives_view(rows))
    d = cs.paired_differences("A", "B", "m")
    np.testing.assert_allclose(d, [(0.10 - 0.30) / 2, (0.30 + 0.10) / 2], rtol=0, atol=1e-15)
    d_o1 = cs.paired_differences("A", "B", "m", where="owner = 'o1'")
    np.testing.assert_allclose(d_o1, [0.10, 0.30], rtol=0, atol=1e-15)
    np.testing.assert_allclose(cs.paired_differences("B", "A", "m"), -d, rtol=0, atol=1e-15)


def test_contrast_reproduces_an_official_value():
    got = cs.contrast("D1", "awake_frac_d1_14")
    assert got["n"] == cs.N_UNITS
    cs.assert_matches(got, cs.REF["contrasts"]["awake_frac_d1_14"]["D1"], "D1 awake")


def test_fmt_and_minutes():
    assert cs.fmt({"mean": -0.0109, "ci_low": -0.01131, "ci_high": -0.01049}) == "-0.0109 [-0.0113; -0.0105]"
    assert cs.minutes(1 / 96) == pytest.approx(15.0)  # one decision = 15 simulated minutes


# ---- case 2: triage ----


def _triage_view(levels):
    """20 units x the 3 places of one owner x 2 arms; control = levels(unit, place),
    body_variant = control + effect(place) + (unit - 10.5) / 1000 (a spread that sums to 0 over units)."""
    effect = {"at_feeder": 0.01, "far": 0.04, "far_fixed": 0.07}
    rows = []
    for u in range(1, triage.N_UNITS + 1):
        for p, e in effect.items():
            c = levels(u, p)
            rows += [("control", "attentive", p, u, c), ("body_variant", "attentive", p, u, c + e + (u - 10.5) / 1000)]
    con = duckdb.connect()
    con.register("synthetic", pd.DataFrame(rows, columns=["arm", "owner", "place", "unit", "time_well"]))
    con.execute("CREATE VIEW triage AS SELECT * FROM synthetic")
    return con, effect


def test_triage_estimate_by_hand(monkeypatch):
    con, effect = _triage_view(lambda u, p: 0.5 + 0.01 * u)
    monkeypatch.setattr(triage, "_con", con)
    r = triage.estimate("time_well", "12_cells")  # every cell of the synthetic table
    assert r["n"] == 20
    assert r["mean"] == pytest.approx(sum(effect.values()) / 3, abs=1e-15)
    assert r["control"] == pytest.approx(0.5 + 0.01 * 10.5, abs=1e-15)  # mean of units 1..20
    assert r["body_variant"] == pytest.approx(r["control"] + r["mean"], abs=1e-15)
    far = triage.estimate("time_well", "far")
    assert far["mean"] == pytest.approx(0.04, abs=1e-15)
    cell = triage.estimate("time_well", "attentive|far_fixed")  # a single cell 'owner|place'
    assert cell["mean"] == pytest.approx(0.07, abs=1e-15)


def test_triage_estimate_ci_by_hand(monkeypatch):
    con, effect = _triage_view(lambda u, p: 0.5)
    monkeypatch.setattr(triage, "_con", con)
    r = triage.estimate("time_well", "at_feeder")
    d = np.array([effect["at_feeder"] + (u - 10.5) / 1000 for u in range(1, 21)])
    sd = math.sqrt(((d - d.mean()) ** 2).sum() / 19)
    half = stats.t.ppf(0.975, 19) * sd / math.sqrt(20)
    assert r["mean"] == pytest.approx(0.01, abs=1e-15)
    assert r["sd"] == pytest.approx(sd, rel=1e-12)
    assert r["ci_low"] == pytest.approx(0.01 - half, rel=1e-12)
    assert r["ci_high"] == pytest.approx(0.01 + half, rel=1e-12)
    assert triage.half_width(r["sd"], r["n"]) == pytest.approx(half, rel=1e-12)


def test_triage_estimate_needs_every_unit(monkeypatch):
    con, _ = _triage_view(lambda u, p: 0.5)
    con.execute("CREATE OR REPLACE VIEW triage AS SELECT * FROM synthetic WHERE unit <= 19")
    monkeypatch.setattr(triage, "_con", con)
    with pytest.raises(AssertionError):
        triage.estimate("time_well", "12_cells")


def test_half_width_by_hand():
    assert triage.half_width(1.0, 20) == pytest.approx(2.093024054408263 / math.sqrt(20), rel=1e-12)
    assert triage.half_width(0.0, 20) == 0.0
    assert triage.half_width(2.0, 5) == pytest.approx(2 * triage.half_width(1.0, 5), rel=1e-15)


def test_where_of_and_split():
    assert triage.where_of("12_cells") == "TRUE"
    assert triage.where_of("far") == "place = 'far'"
    assert triage.where_of("random|far") == "owner = 'random' AND place = 'far'"
    assert triage.split("health_d8_14|random|far") == ("health_d8_14", "random|far")


def test_triage_reproduces_an_official_value():
    got = triage.estimate("time_well", "12_cells")
    triage.assert_matches(got, triage.REF["estimates"]["time_well|12_cells"], "time_well|12_cells")
    assert triage.fmt(got) == "+0.024 [+0.009; +0.038]"

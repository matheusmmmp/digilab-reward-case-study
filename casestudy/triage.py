"""Helpers for case 2 (the body-variant triage): data loading, the paired estimate over
a set of cells, and the plan's constants. No result numbers live here."""

import json

import duckdb
import numpy as np
import pandas as pd

from . import ROOT, TOL, summarize

LIVES = (ROOT / "data" / "body_triage_lives.parquet").as_posix()
REF = json.loads((ROOT / "data" / "body_triage_reference.json").read_text())

# Constants quoted from the analysis plan (also checked against the reference where it holds them).
MARGIN = 0.032  # the plan's margin delta for "time well" (no external source)
CUT_PROPOSED = 2 * MARGIN  # a go/no-go cut proposed before the triage and never decided
NEAR_CEILING = 0.99  # descriptive cut: lives with time_well above it are "near the ceiling"
N_UNITS = 20  # the triage
N_UNITS_PLANNED = 200  # the confirmatory run that was planned and not run
assert REF["margin"] == MARGIN and REF["units"] == N_UNITS

ARMS = ["control", "body_variant"]
OWNERS = ["attentive", "neglectful", "random", "inconsistent"]
PLACES = ["at_feeder", "far", "far_fixed"]
COPY_CELL = ("inconsistent", "at_feeder")  # identical to (attentive, at_feeder) in every life
MEASURES = [
    "time_well",
    "time_well_d8_14",
    "health_d8_14",
    "deprivation",
    "exhaustion",
    "episode_rate",
    "meals_per_day",
    "sleep_frac_ticks",
    "kicks",
    "play_decisions",
]

# A "group" is the set of cells a per-unit difference is averaged over.
GROUPS = {
    "12_cells": "TRUE",
    "11_cells": f"NOT (owner = '{COPY_CELL[0]}' AND place = '{COPY_CELL[1]}')",
    **{p: f"place = '{p}'" for p in PLACES},
    "neglectful_and_random": "owner IN ('neglectful', 'random')",
}

_con = duckdb.connect()
_con.execute("SET threads = 1")  # fixed summation order: the ~1e-16 diffs shown are stable across runs
_con.execute(f"CREATE VIEW triage AS SELECT * FROM read_parquet('{LIVES}')")


def sql(query: str) -> pd.DataFrame:
    """Run DuckDB SQL; the view `triage` is the parquet file."""
    return _con.execute(query).df()


def where_of(group: str) -> str:
    """SQL filter for a named group, or for a single cell written 'owner|place'."""
    if group in GROUPS:
        return GROUPS[group]
    owner, place = group.split("|")
    return f"owner = '{owner}' AND place = '{place}'"


def per_unit(measure: str, group: str) -> pd.DataFrame:
    """One row per unit: the arm levels and the body_variant - control difference,
    each averaged over the cells of the group."""
    q = f"""
        WITH wide AS (
            SELECT unit, owner, place,
                   max({measure}) FILTER (WHERE arm = 'body_variant') AS v,
                   max({measure}) FILTER (WHERE arm = 'control') AS c
            FROM triage WHERE {where_of(group)}
            GROUP BY unit, owner, place)
        SELECT unit, avg(c) AS control, avg(v) AS body_variant, avg(v - c) AS diff, count(*) AS cells
        FROM wide GROUP BY unit ORDER BY unit"""
    return sql(q)


def estimate(measure: str, group: str) -> dict:
    """Levels by arm and the paired estimate (mean, Student-t 95% CI over the 20 units, sd)."""
    u = per_unit(measure, group)
    assert len(u) == N_UNITS and u.cells.nunique() == 1
    return dict(control=float(u.control.mean()), body_variant=float(u.body_variant.mean()), **summarize(u["diff"].to_numpy()))


def max_diff(got: dict, ref: dict, keys=("control", "body_variant", "mean", "sd", "ci_low", "ci_high")) -> float:
    return max(abs(got[k] - ref[k]) for k in keys if k in ref)


def assert_matches(got: dict, ref: dict, what: str) -> float:
    d = max_diff(got, ref)
    assert d <= TOL, f"{what}: |diff| {d:.2e} vs reference ({got} vs {ref})"
    return d


def split(name: str) -> tuple[str, str]:
    """'health_d8_14|random|far' -> ('health_d8_14', 'random|far')"""
    m, g = name.split("|", 1)
    return m, g


def fmt(r: dict, digits: int = 3) -> str:
    return f"{r['mean']:+.{digits}f} [{r['ci_low']:+.{digits}f}; {r['ci_high']:+.{digits}f}]"


def half_width(sd: float, n: int) -> float:
    from scipy import stats

    return float(stats.t.ppf(0.975, n - 1)) * sd / np.sqrt(n)

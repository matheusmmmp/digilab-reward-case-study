"""Shared helpers for the case-study notebooks: data loading, the pre-registered
paired contrast, and the pre-registered reading rules. No numbers live here."""
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
LIVES = (ROOT / "data" / "lives.parquet").as_posix()
REF = json.loads((ROOT / "data" / "reference.json").read_text())
TOL = 1e-9

# Pre-registered constants (quoted from the analysis plan, also stored in reference.json).
DELTA_A = 0.02        # relevant size for the awake fraction
MARGIN_WELL = 0.032   # non-inferiority margin for time_well
N_UNITS = 200
DECISIONS_PER_DAY = 96  # one decision every 15 simulated minutes: 1,344 decisions in 14 days
MIN_PER_DAY = 24 * 60  # so a fraction of the pet's decisions reads as the same fraction of its day

ARMS = ["no_petting", "petting_body_only", "petting_with_credit",
        "petting_with_credit_random_time"]
OWNERS = ["attentive", "neglectful", "random", "inconsistent"]
PLACES = ["at_feeder", "near", "far"]
CONTRASTS = REF["contrast_definitions"]  # D1, D2, D3 -> {a, b}

_con = duckdb.connect()
_con.execute(f"CREATE VIEW lives AS SELECT * FROM read_parquet('{LIVES}')")


def sql(query: str) -> pd.DataFrame:
    """Run DuckDB SQL; the view `lives` is the parquet file."""
    return _con.execute(query).df()


def lives() -> pd.DataFrame:
    return sql("SELECT * FROM lives ORDER BY arm, owner, place, unit")


def paired_differences(a: str, b: str, measure: str, where: str = "TRUE") -> np.ndarray:
    """Per-unit difference A - B, averaged over the cells kept by `where`
    (all 12 cells by default). Returns one value per unit, ordered by unit."""
    q = f"""
        WITH wide AS (
            SELECT unit, owner, place,
                   max({measure}) FILTER (WHERE arm = '{a}') AS a,
                   max({measure}) FILTER (WHERE arm = '{b}') AS b
            FROM lives WHERE {where}
            GROUP BY unit, owner, place)
        SELECT unit, avg(a - b) AS diff FROM wide GROUP BY unit ORDER BY unit"""
    return sql(q)["diff"].to_numpy()


def summarize(d: np.ndarray) -> dict:
    """Mean, 95% Student-t CI over units, sd and the standardized effect dz."""
    n = len(d)
    mean, sd = float(d.mean()), float(d.std(ddof=1))
    half = float(stats.t.ppf(0.975, n - 1)) * sd / np.sqrt(n)
    return dict(n=n, mean=mean, ci_low=float(mean - half), ci_high=float(mean + half), sd=sd, dz=mean / sd)


def contrast(cid: str, measure: str, where: str = "TRUE") -> dict:
    c = CONTRASTS[cid]
    return summarize(paired_differences(c["a"], c["b"], measure, where))


def assert_matches(got: dict, ref: dict, what: str) -> None:
    for k in ("mean", "ci_low", "ci_high"):
        diff = abs(got[k] - ref[k])
        assert diff <= TOL, f"{what} {k}: {got[k]!r} vs reference {ref[k]!r} (|diff| {diff:.2e})"


# ---- pre-registered reading rules, applied in the order written in the plan ----

def read_awake(lo: float, hi: float, delta: float = DELTA_A) -> str:
    if hi < 0:
        return "no: with the reward the pet sleeps more"
    if -delta <= lo and hi <= delta:
        if lo > 0:  # the plan's sub-label of "stays the same"
            return "goes up, but below the relevant size"
        return "no: stays the same"
    if lo > delta:
        return "yes, stays awake more"
    return "inconclusive"


def read_well(lo: float, hi: float, margin: float = MARGIN_WELL) -> str:
    if lo > 0:
        return "the pet is better off"
    if lo > -margin:
        return "not worse"
    if hi < -margin:
        return "worse"
    return "inconclusive"


WHY_BODY = "by the body effect of petting, not by learning"


def read_why(awake_label: str, d2_lo: float, d3_lo: float, dose_premise_held: bool) -> str | None:
    if awake_label in ("no: stays the same", "goes up, but below the relevant size"):
        return None  # the rule is only applied when D1 is not "stays the same"
    if not dose_premise_held:
        return WHY_BODY  # the plan: with the dose premise failed, only the third answer can come out
    if d2_lo > 0 and d3_lo > 0:
        return "by the timely reward and by what the pet learns"
    if d3_lo > 0:
        return "by the credit, at any time"
    if d2_lo > 0:
        return "not defined by the plan"  # D2 above 0 without D3: the plan has no line for it
    return WHY_BODY


def fmt(r: dict, digits: int = 4) -> str:
    return f"{r['mean']:+.{digits}f} [{r['ci_low']:+.{digits}f}; {r['ci_high']:+.{digits}f}]"


def minutes(frac: float) -> float:
    return frac * MIN_PER_DAY

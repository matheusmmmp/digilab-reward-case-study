"""Export the compact data behind the two explorer pages (explorer/data/*.json, not committed)
and check, in Python, that the explorer's algorithm reproduces the official numbers.

For each contrast x measure the JSON holds the paired difference (arm A - arm B) of every
unit in every cell, as one flat array indexed [unit * 12 + cell]. A measure whose values are
all k / den for one integer den (a count of decisions, days or events) is stored as the integer
numerators k_A - k_B and the den; the others are stored at full float precision. The JSON also
carries the Student-t critical value for the page's n (the CI is over units, so n does not
change with the subset of cells) so the page needs no t-distribution.

The explorer's method is the official one: per unit, the mean over the selected cells of the
arm difference; estimate = mean over units; sd with ddof=1; CI = mean +/- t * sd / sqrt(n).
`estimate()` below is the same algorithm as explorer/paired.js, run over the exported JSON;
it must match data/reference.json and data/body_triage_reference.json within 1e-9 for every
selection those files hold."""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "explorer" / "data"
TOL = 1e-9
DENOMINATORS = [1, 14, 672, 1344]  # counts, per-day counts, decisions of days 8-14, of days 1-14

CASES = {
    "reward": dict(
        parquet="lives.parquet", reference="reference.json", n_units=200,
        owners=["attentive", "neglectful", "random", "inconsistent"],
        places=["at_feeder", "near", "far"],
        measures=["awake_frac_d1_14", "awake_frac_d8_14", "time_well", "episode_rate"],
        contrasts=None,  # read from the reference: D1, D2, D3
    ),
    "triage": dict(
        parquet="body_triage_lives.parquet", reference="body_triage_reference.json", n_units=20,
        owners=["attentive", "neglectful", "random", "inconsistent"],
        places=["at_feeder", "far", "far_fixed"],
        measures=["time_well", "time_well_d8_14", "health_d8_14", "deprivation", "exhaustion",
                  "episode_rate", "meals_per_day", "sleep_frac_ticks", "kicks", "play_decisions"],
        contrasts={"V": {"a": "body_variant", "b": "control"}},
    ),
}


def denominator(values: np.ndarray) -> int | None:
    """The smallest den in DENOMINATORS with every value exactly k / den, else None."""
    for den in DENOMINATORS:
        k = np.round(values * den)
        if np.array_equal(k / den, values):
            return den
    return None


def build(name: str, spec: dict) -> dict:
    lives = pd.read_parquet(ROOT / "data" / spec["parquet"])
    ref = json.loads((ROOT / "data" / spec["reference"]).read_text())
    contrasts = spec["contrasts"] or ref["contrast_definitions"]
    owners, places, n = spec["owners"], spec["places"], spec["n_units"]
    cells = [(o, p) for o in owners for p in places]
    units = list(range(1, n + 1))
    assert sorted(lives.unit.unique()) == units
    assert set(map(tuple, lives[["owner", "place"]].drop_duplicates().to_numpy())) == set(cells)

    out = dict(case=name, n_units=n, owners=owners, places=places,
               cells=[f"{o}|{p}" for o, p in cells],
               t975=float(stats.t.ppf(0.975, n - 1)),
               contrasts=contrasts, data={})
    for m in spec["measures"]:
        den = denominator(lives[m].to_numpy(dtype=float))
        wide = lives.pivot_table(index=["unit", "owner", "place"], columns="arm", values=m,
                                 aggfunc="first")
        # rows in [unit][cell] order: index = (unit - 1) * len(cells) + cell
        order = pd.MultiIndex.from_tuples([(u, o, p) for u in units for o, p in cells])
        wide = wide.reindex(order)
        assert not wide.isna().any().any()
        entry = dict(den=den)
        for cid, c in contrasts.items():
            a, b = wide[c["a"]].to_numpy(float), wide[c["b"]].to_numpy(float)
            if den is None:
                entry[cid] = [float(x) for x in a - b]
            else:
                ka, kb = np.round(a * den).astype(np.int64), np.round(b * den).astype(np.int64)
                entry[cid] = [int(x) for x in ka - kb]
        out["data"][m] = entry
    return out


# ---- the explorer's algorithm (mirrors explorer/paired.js line by line) ----

def estimate(case: dict, measure: str, contrast: str, selected_cells: list[str]) -> dict | None:
    if not selected_cells:
        return None
    entry = case["data"][measure]
    values, den = entry[contrast], entry["den"] or 1
    ncell = len(case["cells"])
    idx = [case["cells"].index(c) for c in selected_cells]
    n = case["n_units"]
    d = []
    for u in range(n):
        s = 0.0
        for c in idx:
            s += values[u * ncell + c]
        d.append(s / len(idx) / den)
    mean = sum(d) / n
    sd = math.sqrt(sum((x - mean) ** 2 for x in d) / (n - 1))
    half = case["t975"] * sd / math.sqrt(n)
    return dict(n=n, mean=mean, sd=sd, ci_low=mean - half, ci_high=mean + half)


def select(case: dict, owners=None, places=None, drop=()) -> list[str]:
    owners = owners or case["owners"]
    places = places or case["places"]
    return [f"{o}|{p}" for o in owners for p in places if f"{o}|{p}" not in drop]


def check(got: dict, ref: dict, what: str, log: list) -> None:
    keys = [k for k in ("mean", "sd", "ci_low", "ci_high") if k in ref]
    diff = max(abs(got[k] - ref[k]) for k in keys)
    assert diff <= TOL, f"explorer {what}: |diff| {diff:.2e} ({got} vs {ref})"
    log.append(diff)


def verify_reward(case: dict) -> int:
    ref = json.loads((ROOT / "data" / CASES["reward"]["reference"]).read_text())
    log = []
    for m in CASES["reward"]["measures"]:
        for cid in case["contrasts"]:
            check(estimate(case, m, cid, select(case)), ref["contrasts"][m][cid], f"{m} {cid}", log)
    for owner, by_m in ref["by_owner"].items():
        for m, by_c in by_m.items():
            for cid, r in by_c.items():
                check(estimate(case, m, cid, select(case, owners=[owner])), r, f"{owner} {m} {cid}", log)
    for place, by_m in ref["by_place"].items():
        for m, by_c in by_m.items():
            for cid, r in by_c.items():
                check(estimate(case, m, cid, select(case, places=[place])), r, f"{place} {m} {cid}", log)
    print(f"explorer reward: {len(log)} official values reproduced (max |diff| {max(log):.1e})")
    return len(log)


def verify_triage(case: dict) -> int:
    ref = json.loads((ROOT / "data" / CASES["triage"]["reference"]).read_text())
    copy = "inconsistent|at_feeder"  # identical to attentive|at_feeder in every life
    groups = {"12_cells": select(case), "11_cells": select(case, drop=[copy]),
              "neglectful_and_random": select(case, owners=["neglectful", "random"]),
              **{p: select(case, places=[p]) for p in case["places"]}}

    def cells_of(group):
        return groups[group] if group in groups else [group]  # a single cell 'owner|place'

    log = []
    for key, r in ref["estimates"].items():
        m, group = key.split("|", 1)
        check(estimate(case, m, "V", cells_of(group)), r, key, log)
    for group, by_m in ref["by_group"].items():
        for m, r in by_m.items():
            if m in case["data"]:  # share_time_well_above_0_99 is not a column
                check(estimate(case, m, "V", cells_of(group)), r, f"{group} {m}", log)
    for cell, r in ref["time_well_by_cell"].items():
        check(estimate(case, "time_well", "V", [cell]), r, f"time_well {cell}", log)
    print(f"explorer triage: {len(log)} official values reproduced (max |diff| {max(log):.1e})")
    return len(log)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, spec in CASES.items():
        case = build(name, spec)
        path = OUT / f"{name}.json"
        text = json.dumps(case, separators=(",", ":"))
        # verify over the JSON exactly as the page will read it
        reread = json.loads(text)
        (verify_reward if name == "reward" else verify_triage)(reread)
        assert estimate(reread, spec["measures"][0], next(iter(reread["contrasts"])), []) is None
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"explorer: wrote {path.relative_to(ROOT).as_posix()} ({path.stat().st_size / 1024:.0f} KiB)")

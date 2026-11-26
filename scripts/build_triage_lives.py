"""Build data/body_triage_lives.parquet (case 2) from the private per-life measures file.

Only the source fields behind the published columns are read; nothing else from the
source is touched or written. The sleep fraction is nested inside a larger per-life
record that is not published; it is located by its own (unique) leaf name, so the script
names no other part of that record.

The committed file was written by an earlier version of this script that used polars 2.1.0;
this one writes it with pyarrow: the same schema, values (bit for bit) and row order, but not
the same bytes (the writer name and page layout inside the file differ)."""

import argparse
import hashlib
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

SHA = "937dad3e7e997e0454191b6f1d0d7b607ac38d7b478ed06ba5b2ca429aa401be"
ARM = {"CTRL": "control", "DTB": "body_variant"}
OWNER = {"atencioso": "attentive", "relapso": "neglectful", "aleatorio": "random", "incoerente": "inconsistent"}
PLACE = {"comedouro": "at_feeder", "longe": "far", "longe_fixo": "far_fixed"}
N = 480
N_UNITS = 20
DESIGN = ["arm", "owner", "place", "unit"]


def leaf(record, name):
    """The value of the one nested key called `name` (fails unless exactly one exists)."""
    found = []

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == name:
                    found.append(v)
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(record)
    if len(found) != 1:
        raise ValueError(f"{name}: {len(found)} occurrences, expected 1")
    return found[0]


def row(r):
    return {
        "arm": ARM[r["braco"]],
        "owner": OWNER[r["dono"]],
        "place": PLACE[r["lugar"]],
        "_unit_key": int(r["base"]),  # replaced by its dense rank below, never written
        "time_well": float(r["tempo_bem"]),
        "time_well_d8_14": float(r["tempo_bem_8_14"]),
        "health_d8_14": float(r["saude_media"]),
        "deprivation": float(r["privacao_vida"]),
        "exhaustion": float(r["exaustao_vida"]),
        "episode_rate": float(r["episodios_fome"]["taxa"]),
        "meals_per_day": float(r["cadeia"]["refeicoes_por_dia"]),
        "sleep_frac_ticks": float(leaf(r, "fracao_ticks_dormindo")),
        "kicks": int(r["chutes"]),
        "play_decisions": int(r["brincar"]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="medidas.json of the triage")
    ap.add_argument("--out", default="data/body_triage_lives.parquet")
    a = ap.parse_args()
    raw = Path(a.source).read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != SHA:
        raise SystemExit(f"source sha256 mismatch: {got} != {SHA}")
    lives = json.loads(raw)
    if len(lives) != N:
        raise ValueError(f"expected {N} rows, got {len(lives)}")
    rows = [row(r) for r in lives]  # KeyError on any missing key / unknown code
    # unit = 1..20: the dense rank of the private unit key
    keys = sorted({r["_unit_key"] for r in rows})
    rank = {k: i + 1 for i, k in enumerate(keys)}
    for r in rows:
        r["unit"] = rank[r.pop("_unit_key")]
    if len(keys) != N_UNITS or max(rank.values()) != N_UNITS:
        raise ValueError(f"expected {N_UNITS} units")
    measures = [c for c in rows[0] if c not in DESIGN]
    rows.sort(key=lambda r: (r["arm"], r["owner"], r["place"], r["unit"]))
    if len(rows) != N or not all(1 <= r["unit"] <= N_UNITS for r in rows):
        raise ValueError("row count or unit range changed")
    # strings as large_string, integers as int64, measures as double: the published schema
    types = {c: pa.large_string() for c in DESIGN if c != "unit"}
    table = pa.table(
        {
            c: pa.array([r[c] for r in rows], types.get(c, pa.float64() if isinstance(rows[0][c], float) else pa.int64()))
            for c in DESIGN + measures
        }
    )
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, a.out, compression="zstd", write_statistics=False)
    print(f"wrote {a.out}: {table.num_rows} rows, {table.num_columns} columns")


if __name__ == "__main__":
    main()

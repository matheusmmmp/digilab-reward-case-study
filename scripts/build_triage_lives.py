"""Build data/body_triage_lives.parquet (case 2) from the private per-life measures file.

Only the source fields behind the published columns are read; nothing else from the
source is touched or written. The sleep fraction is nested inside a larger per-life
record that is not published; it is located by its own (unique) leaf name, so the script
names no other part of that record."""
import argparse
import hashlib
import json
from pathlib import Path

import polars as pl

SHA = "937dad3e7e997e0454191b6f1d0d7b607ac38d7b478ed06ba5b2ca429aa401be"
ARM = {"CTRL": "control", "DTB": "body_variant"}
OWNER = {"atencioso": "attentive", "relapso": "neglectful",
         "aleatorio": "random", "incoerente": "inconsistent"}
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
        "arm": ARM[r["braco"]], "owner": OWNER[r["dono"]], "place": PLACE[r["lugar"]],
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
    df = pl.DataFrame(rows)
    df = df.with_columns(pl.col("_unit_key").rank("dense").cast(pl.Int64).alias("unit"))
    if df["_unit_key"].n_unique() != N_UNITS or df["unit"].max() != N_UNITS:
        raise ValueError(f"expected {N_UNITS} units")
    measures = [c for c in rows[0] if c not in DESIGN and c != "_unit_key"]
    df = df.select(DESIGN + measures).sort("arm", "owner", "place", "unit")
    if df.height != N or not df["unit"].is_between(1, N_UNITS).all():
        raise ValueError("row count or unit range changed")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(a.out, compression="zstd", statistics=False)
    print(f"wrote {a.out}: {df.height} rows, {df.width} columns")


if __name__ == "__main__":
    main()

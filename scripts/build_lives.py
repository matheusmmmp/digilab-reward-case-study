"""Build data/lives.parquet from the private per-life measures file.

Only the source fields behind the published columns are read; nothing else from the
source is touched or written."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

import polars as pl

SHA = "e8333972cc635f366ef7ae41b1e767adaa192858168d0a44310e3e7e3ad0e413"
ARM = {"R0": "no_petting", "R-CORPO": "petting_body_only",
       "R-CB": "petting_with_credit", "R-SORT": "petting_with_credit_random_time"}
OWNER = {"atencioso": "attentive", "relapso": "neglectful",
         "aleatorio": "random", "incoerente": "inconsistent"}
PLACE = {"comedouro": "at_feeder", "perto": "near", "longe": "far"}
N = 9600
N_UNITS = 200
DESIGN = ["arm_code", "arm", "owner", "place", "unit"]


def row(r):
    return {
        "arm_code": r["braco"], "arm": ARM[r["braco"]],
        "owner": OWNER[r["dono"]], "place": PLACE[r["lugar"]],
        "_unit_key": int(r["base"]),  # replaced by its dense rank below, never written
        "awake_frac_d1_14": float(r["t_acordado"]),
        "awake_frac_d8_14": float(r["t_acordado_8_14"]),
        "time_well": float(r["tempo_bem"]),
        "episode_rate": float(r["episodios_fome"]["taxa"]),
        "eat_decisions": int(r["decisoes_comer"]),
        "play_decisions": int(r["decisoes_brincar"]),
        "sleep_decisions": int(r["acoes"]["dormir"]),
        "extra_pets": int(r["carinhos_a_mais"]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--out", default="data/lives.parquet")
    a = ap.parse_args()
    raw = gzip.open(a.source).read()
    got = hashlib.sha256(raw).hexdigest()
    if got != SHA:
        raise SystemExit(f"source sha256 mismatch: {got} != {SHA}")
    lives = json.loads(raw)
    if len(lives) != N:
        raise ValueError(f"expected {N} rows, got {len(lives)}")
    rows = [row(r) for r in lives]  # KeyError on any missing key / unknown code
    df = pl.DataFrame(rows)
    # unit = 1..200: the dense rank of the private unit key
    df = df.with_columns(pl.col("_unit_key").rank("dense").cast(pl.Int64).alias("unit"))
    if df["_unit_key"].n_unique() != N_UNITS or df["unit"].max() != N_UNITS:
        raise ValueError(f"expected {N_UNITS} units")
    measures = [c for c in rows[0] if c not in DESIGN and c != "_unit_key"]
    df = df.select(DESIGN + measures).sort("arm_code", "owner", "place", "unit")
    if df.height != N:
        raise ValueError("row count changed")
    if not df["unit"].is_between(1, N_UNITS).all():
        raise ValueError("unit outside 1..200")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(a.out, compression="zstd", statistics=False)
    print(f"wrote {a.out}: {df.height} rows, {df.width} columns")


if __name__ == "__main__":
    main()

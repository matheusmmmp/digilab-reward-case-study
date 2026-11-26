"""Build data/lives.parquet from the private per-life measures file.

Only the source fields behind the published columns are read; nothing else from the
source is touched or written.

The committed file was written by an earlier version of this script that used polars 2.1.0;
this one writes it with pyarrow: the same schema, values (bit for bit) and row order, but not
the same bytes (the writer name and page layout inside the file differ)."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

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
    # unit = 1..200: the dense rank of the private unit key
    keys = sorted({r["_unit_key"] for r in rows})
    rank = {k: i + 1 for i, k in enumerate(keys)}
    for r in rows:
        r["unit"] = rank[r.pop("_unit_key")]
    if len(keys) != N_UNITS or max(rank.values()) != N_UNITS:
        raise ValueError(f"expected {N_UNITS} units")
    measures = [c for c in rows[0] if c not in DESIGN]
    rows.sort(key=lambda r: (r["arm_code"], r["owner"], r["place"], r["unit"]))
    if len(rows) != N:
        raise ValueError("row count changed")
    if not all(1 <= r["unit"] <= N_UNITS for r in rows):
        raise ValueError("unit outside 1..200")
    # strings as large_string, integers as int64, measures as double: the published schema
    types = {c: pa.large_string() for c in DESIGN if c != "unit"}
    table = pa.table({c: pa.array([r[c] for r in rows],
                                  types.get(c, pa.float64() if isinstance(rows[0][c], float) else pa.int64()))
                      for c in DESIGN + measures})
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, a.out, compression="zstd", write_statistics=False)
    print(f"wrote {a.out}: {table.num_rows} rows, {table.num_columns} columns")


if __name__ == "__main__":
    main()

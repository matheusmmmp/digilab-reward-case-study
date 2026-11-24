"""Run the DuckDB checks in sql/ against the published parquet files:
sql/checks.sql on data/lives.parquet (case 1) and sql/checks_body_triage.sql on
data/body_triage_lives.parquet (case 2)."""
import json
import re
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
TOL = 1e-9
SUITES = [  # (sql file, parquet, reference json, label prefix)
    ("checks.sql", "lives.parquet", "reference.json", ""),
    ("checks_body_triage.sql", "body_triage_lives.parquet", "body_triage_reference.json", "triage: "),
]
failed = 0


def report(name, ok, detail=""):
    global failed
    failed += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {name} {detail}".rstrip())


con = duckdb.connect()
for sql_file, parquet, ref_file, prefix in SUITES:
    lives = (ROOT / "data" / parquet).as_posix()
    text = (ROOT / "sql" / sql_file).read_text()
    blocks = re.split(r"^-- name: (\w+)\n", text, flags=re.M)[1:]
    for name, sql in zip(blocks[::2], blocks[1::2]):
        q = sql.replace("{lives}", lives).strip().rstrip(";")
        if name == "arm_means":
            ref = json.loads((ROOT / "data" / ref_file).read_text())["arm_means"]
            cur = con.execute(q)
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
            n_arms = len(ref)
            report(f"{prefix}arm_means_cover_{n_arms}_arms", sorted(r[0] for r in rows) == sorted(ref))
            for r in rows:
                for c, v in zip(cols[1:], r[1:]):
                    diff = abs(v - ref[r[0]][c])
                    report(f"{prefix}mean[{r[0]}][{c}]", diff <= TOL,
                           f"(sql={v!r} ref={ref[r[0]][c]!r} |diff|={diff:.2e})")
        else:
            report(prefix + name, bool(con.execute(q).fetchone()[0]))
print(f"{failed} failed" if failed else "all checks passed")
sys.exit(1 if failed else 0)

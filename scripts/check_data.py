"""Run the DuckDB checks in sql/checks.sql against data/lives.parquet."""
import json
import re
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
LIVES = (ROOT / "data" / "lives.parquet").as_posix()
TOL = 1e-9
failed = 0


def report(name, ok, detail=""):
    global failed
    failed += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {name} {detail}".rstrip())


text = (ROOT / "sql" / "checks.sql").read_text()
blocks = re.split(r"^-- name: (\w+)\n", text, flags=re.M)[1:]
con = duckdb.connect()
for name, sql in zip(blocks[::2], blocks[1::2]):
    q = sql.replace("{lives}", LIVES).strip().rstrip(";")
    if name == "arm_means":
        ref = json.loads((ROOT / "data" / "reference.json").read_text())["arm_means"]
        cur = con.execute(q)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        report("arm_means_cover_4_arms", sorted(r[0] for r in rows) == sorted(ref))
        for r in rows:
            for c, v in zip(cols[1:], r[1:]):
                diff = abs(v - ref[r[0]][c])
                report(f"mean[{r[0]}][{c}]", diff <= TOL,
                       f"(sql={v!r} ref={ref[r[0]][c]!r} |diff|={diff:.2e})")
    else:
        report(name, bool(con.execute(q).fetchone()[0]))
print(f"{failed} failed" if failed else "all checks passed")
sys.exit(1 if failed else 0)

"""One command to rebuild everything that needs no private data:
check the data extracts, execute every notebook in place, render the site into docs/.

Execution timing metadata is not recorded and cell metadata is kept stable, so a second
run leaves the committed notebooks (and docs/) unchanged."""
import subprocess
import sys
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = ["notebooks/01_reproduce_official_results.ipynb",
             "notebooks/02_case_study.ipynb",
             "notebooks/03_reproduce_body_triage.ipynb",
             "notebooks/04_body_triage_case_study.ipynb"]
QUARTO = Path(sys.executable).with_name("quarto.exe" if sys.platform == "win32" else "quarto")


def strip_volatile(path):
    """Drop per-cell execution timestamps (left by older runs) and write LF line endings
    (nbconvert writes the platform's), so commits stay clean."""
    nb = nbformat.read(ROOT / path, as_version=4)
    for cell in nb.cells:
        cell.metadata.pop("execution", None)
    with open(ROOT / path, "w", encoding="utf-8", newline="\n") as f:
        nbformat.write(nb, f)


def run(cmd):
    print("$", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)


run([sys.executable, "scripts/check_data.py"])
for nb in NOTEBOOKS:
    run([sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute",
         "--inplace", "--ExecutePreprocessor.record_timing=False", nb])
    strip_volatile(nb)
run([str(QUARTO) if QUARTO.exists() else "quarto", "render"])
(ROOT / "docs" / ".nojekyll").touch()  # GitHub Pages: serve site_libs/ as is
print("reproduce: OK")

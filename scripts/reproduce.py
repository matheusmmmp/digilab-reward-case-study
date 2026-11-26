"""One command to rebuild everything that needs no private data:
check the data extracts, execute every notebook in place, draw the cover image, render the
site into docs/ (not committed: CI renders it and deploys it to GitHub Pages).

Execution timing metadata is not recorded and cell metadata is kept stable, so a second
run leaves the committed notebooks unchanged. Works on Windows, Linux and macOS."""
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = ["notebooks/01_reproduce_official_results.ipynb",
             "notebooks/02_case_study.ipynb",
             "notebooks/03_reproduce_body_triage.ipynb",
             "notebooks/04_body_triage_case_study.ipynb"]
EXE = ".exe" if sys.platform == "win32" else ""


def find_quarto() -> str:
    """The quarto pinned in uv.lock (PyPI package quarto-cli), wherever this platform puts it:
    the console script next to the interpreter (.venv/Scripts/quarto.exe on Windows,
    .venv/bin/quarto on Linux and macOS), else the binary inside the package, else PATH."""
    candidates = [Path(sys.executable).with_name("quarto" + EXE)]
    spec = importlib.util.find_spec("quarto_cli")
    if spec and spec.submodule_search_locations:
        candidates.append(Path(list(spec.submodule_search_locations)[0]) / "bin" / ("quarto" + EXE))
    for c in candidates:
        if c.is_file():
            return str(c)
    found = shutil.which("quarto")
    if found:
        return found
    sys.exit("reproduce: quarto not found; run `uv sync` first")


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
run([sys.executable, "scripts/make_cover.py"])
run([find_quarto(), "render"])
(ROOT / "docs" / ".nojekyll").touch()  # GitHub Pages: serve site_libs/ as is
print("reproduce: OK")

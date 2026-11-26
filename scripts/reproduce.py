"""One command to rebuild everything that needs no private data:
check the data extracts, draw the cover image, export the explorer data (checked against the
references), then let Quarto execute every notebook and page and render the site into docs/
(not committed: CI renders it and deploys it to GitHub Pages).

Quarto executes each notebook in place (its outputs are written back into the .ipynb, so
GitHub shows them) and stops on the first failed assertion. `_quarto.yml` sets
`freeze: auto`, which makes a plain `quarto render` or `quarto preview` skip pages whose code
has not changed; this script clears that cache first, so it always executes everything, as CI
does. Line endings are written back as LF, so a second run leaves the committed notebooks
unchanged. Works on Windows, Linux and macOS."""

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
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


def run(cmd):
    print("$", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)


run([sys.executable, "scripts/check_data.py"])
run([sys.executable, "scripts/make_cover.py"])
run([sys.executable, "scripts/build_explorer_data.py"])  # explorer/data/*.json, parity asserted
if shutil.which("node"):  # the explorer's own JS against the references (node is on CI runners)
    run(["node", "scripts/check_explorer_js.mjs"])
else:
    print("reproduce: node not found, skipped the explorer JS check (the Python parity check ran)")
shutil.rmtree(ROOT / "_freeze", ignore_errors=True)  # execute every notebook and page, never reuse
run([find_quarto(), "render"])  # executes the notebooks in place (execute.enabled in _quarto.yml)
for nb in sorted((ROOT / "notebooks").glob("*.ipynb")):  # Quarto writes the platform's line endings
    raw = nb.read_bytes()
    if b"\r\n" in raw:
        nb.write_bytes(raw.replace(b"\r\n", b"\n"))
(ROOT / "docs" / ".nojekyll").touch()  # GitHub Pages: serve site_libs/ as is
print("reproduce: OK")

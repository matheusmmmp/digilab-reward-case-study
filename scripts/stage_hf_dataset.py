"""Stage the Hugging Face dataset mirror in a local folder, ready to upload by hand:
huggingface/README.md (the dataset card) as README.md, and the two published tables under data/,
the paths the card's `configs` point to. Every parquet is checked against the sha256 listed in
PROVENANCE.md (section "Published extracts") and in the card before it is copied. No network.

    uv run python scripts/stage_hf_dataset.py [target]   # default: build/hf_dataset (gitignored)

The target folder is replaced; it must be empty, absent or a previous staging folder."""

import hashlib
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARD = ROOT / "huggingface" / "README.md"
FILES = ["data/lives.parquet", "data/body_triage_lives.parquet"]  # same path in the repo and on the Hub


def listed_hashes(text: str) -> dict[str, str]:
    """`path` ... `sha256` table rows, as in PROVENANCE.md and the card."""
    rows = re.findall(r"^\|\s*`([^`]+\.parquet)`\s*\|.*`([0-9a-f]{64})`\s*\|\s*$", text, flags=re.M)
    return dict(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "build" / "hf_dataset"
    target = target.resolve()
    if target.exists() and any(target.iterdir()):
        known = {"README.md", "data"}
        if not {p.name for p in target.iterdir()} <= known:
            sys.exit(f"stage_hf_dataset: {target} has other files; refusing to replace it")
    provenance = listed_hashes((ROOT / "PROVENANCE.md").read_text(encoding="utf-8"))
    card = listed_hashes(CARD.read_text(encoding="utf-8"))
    for rel in FILES:
        got = sha256(ROOT / rel)
        for where, listed in (("PROVENANCE.md", provenance), ("huggingface/README.md", card)):
            if listed.get(rel) != got:
                sys.exit(f"stage_hf_dataset: {rel} sha256 {got} does not match {where} ({listed.get(rel)})")
        print(f"ok  {rel}  {got}")
    shutil.rmtree(target, ignore_errors=True)
    (target / "data").mkdir(parents=True)
    shutil.copyfile(CARD, target / "README.md")
    for rel in FILES:
        shutil.copyfile(ROOT / rel, target / rel)
        assert sha256(target / rel) == provenance[rel]
    print(f"stage_hf_dataset: staged {1 + len(FILES)} files in {target}")


if __name__ == "__main__":
    main()

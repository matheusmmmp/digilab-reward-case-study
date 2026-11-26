"""The Hugging Face dataset card (huggingface/README.md) and its staging script: the card's YAML
front matter, its configs pointing at the published tables, and the checksums listed in the card
and in PROVENANCE.md matching the files."""

import hashlib
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CARD = ROOT / "huggingface" / "README.md"
TABLES = {"reward_test": "data/lives.parquet", "body_triage": "data/body_triage_lives.parquet"}

sys.path.insert(0, str(ROOT / "scripts"))
from stage_hf_dataset import listed_hashes  # noqa: E402


def front_matter() -> dict:
    text = CARD.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    return yaml.safe_load(text.split("---\n", 2)[1])


def test_card_metadata():
    meta = front_matter()
    assert meta["license"] == "other"
    assert meta["license_name"] == "all-rights-reserved"
    assert meta["license_link"] == "https://github.com/matheusmmmp/digilab-reward-case-study/blob/main/LICENSE"
    assert meta["language"] == ["en"]
    configs = {c["config_name"]: c["data_files"] for c in meta["configs"]}
    assert configs == {name: [{"split": "train", "path": path}] for name, path in TABLES.items()}


def test_listed_checksums_match_the_files():
    provenance = listed_hashes((ROOT / "PROVENANCE.md").read_text(encoding="utf-8"))
    card = listed_hashes(CARD.read_text(encoding="utf-8"))
    for path in TABLES.values():
        got = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        assert provenance[path] == got
        assert card[path] == got


def test_stage_copies_card_and_tables(tmp_path):
    target = tmp_path / "hf"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "stage_hf_dataset.py"), str(target)], check=True)
    staged = sorted(p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_file())
    assert staged == sorted(["README.md", *TABLES.values()])
    for path in TABLES.values():
        assert (target / path).read_bytes() == (ROOT / path).read_bytes()


def test_card_column_dictionaries_match_the_tables():
    import re

    import pyarrow.parquet as pq

    text = CARD.read_text(encoding="utf-8")
    for name, path in TABLES.items():
        section = text.split(f"## `{name}`", 1)[1].split("\n## ", 1)[0]
        documented = re.findall(r"^\| `([a-z0-9_]+)` \| (?:string|int|float) \|", section, flags=re.M)
        assert documented == pq.read_schema(ROOT / path).names

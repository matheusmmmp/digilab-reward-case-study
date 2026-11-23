# Does reward keep a virtual pet awake? A pre-registered simulation study

- **Question:** if a virtual pet's simulated owner pets it right after it eats or plays (with reward credit for its learning agent), does the pet stay awake more?
- **Design, written before the run:** 4 arms x 4 owner types x 3 food places x 200 paired units = 9,600 simulated lives of 14 days; paired contrasts with Student-t CIs and a reading rule fixed in advance.
- **Result (pre-registered reading):** "no: with the reward the pet sleeps more", slightly (D1 = -0.0109 [-0.0113; -0.0105] of its decisions; each life has 96 decisions a day, so about 16 minutes a day). Its welfare measure improves (+0.0183 [+0.0152; +0.0215]), but that gain cannot be separated from the body effect of petting: the timing and credit contrasts on welfare (D2, D3) both have intervals that include 0, so it is not evidence that the reward credit itself makes the pet better off.
- **Also inside:** the analysis crashed after the lives were saved (a guard metric was never recorded); the fix, made before any result was read, and what I would do differently.
- **Every official number** on the site is recomputed from `data/lives.parquet` and asserted against `data/reference.json` (tolerance 1e-9); exploratory extras are labelled as such.

The case study is rendered as a static site in `docs/` (entry point `docs/index.html`).

## Stack

uv (pinned environment, `uv.lock`) · polars and DuckDB SQL over Parquet · Jupyter notebooks rendered with Quarto (pinned as `quarto-cli` from PyPI) · matplotlib · scikit-learn · scipy.

## Reproduce

```
uv sync
uv run python scripts/reproduce.py
```

This runs the DuckDB integrity checks (`scripts/check_data.py`), executes both notebooks in place (each stops on a failed assertion) and renders the site into `docs/`. A second run leaves `git status` clean.

## Repo map

| path | what it is |
|---|---|
| `notebooks/02_case_study.ipynb` | the case study (single source of the main page) |
| `notebooks/01_reproduce_official_results.ipynb` | reproduction appendix: all 18 official contrast x measure values |
| `resumo-pt.qmd` | one-page summary in Portuguese (numbers computed at render time) |
| `casestudy/` | shared helpers: DuckDB view, paired contrast, reading rules, chart style |
| `data/lives.parquet` | the published extract, one row per life (see `data/SCHEMA.md`) |
| `data/reference.json` | the official numbers and reading labels, copied from the study's result file |
| `sql/checks.sql`, `scripts/check_data.py` | integrity checks run before anything else |
| `scripts/reproduce.py` | the one command above |
| `PROVENANCE.md` | where the published data comes from: checksums, sample size, dates and the commit timeline |
| `scripts/build_lives.py`, `scripts/build_reference.py` | rebuild the extract and the reference from the private source files (not needed to reproduce) |
| `_quarto.yml`, `index.qmd`, `docs/` | Quarto website config and the rendered site (for GitHub Pages) |

## License

Code (`casestudy/`, `scripts/`, `sql/`, the notebooks' code cells): MIT. The text, figures, data and rendered site: all rights reserved. Details in [`LICENSE`](LICENSE).

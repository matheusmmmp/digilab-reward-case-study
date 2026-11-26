# Two experiments on a virtual pet

[![site](https://github.com/matheusmmmp/digilab-reward-case-study/actions/workflows/site.yml/badge.svg)](https://github.com/matheusmmmp/digilab-reward-case-study/actions/workflows/site.yml)

Two data-science case studies on the same simulated virtual pet, each told as question → design → data → result → what I would do differently, with every official number recomputed from the published data. The site is published at <https://matheusmmmp.github.io/digilab-reward-case-study/>.

## Case 1: does reward keep a virtual pet awake? A pre-registered simulation study

- **Question:** if a virtual pet's simulated owner pets it right after it eats or plays (with reward credit for its learning agent), does the pet stay awake more?
- **Design, written before the run:** 4 arms x 4 owner types x 3 food places x 200 paired units = 9,600 simulated lives of 14 days; paired contrasts with Student-t CIs and a reading rule fixed in advance.
- **Result (pre-registered reading):** "no: with the reward the pet sleeps more", slightly (D1 = -0.0109 [-0.0113; -0.0105] of its decisions; each life has 96 decisions a day, so about 16 minutes a day). Its welfare measure improves (+0.0183 [+0.0152; +0.0215]), but that gain cannot be separated from the body effect of petting: the timing and credit contrasts on welfare (D2, D3) both have intervals that include 0, so it is not evidence that the reward credit itself makes the pet better off.
- **Also inside:** the analysis crashed after the lives were saved (a guard metric was never recorded); the fix, made before any result was read, and what I would do differently.
- **Every official number** on the site is recomputed from `data/lives.parquet` and asserted against `data/reference.json` (tolerance 1e-9); exploratory extras are labelled as such.

## Case 2: the effect that shrank

- **Question:** a variant of the pet's body physiology raised its welfare measure ("time well") on an earlier version of the pet. Does it still do so on the current pet?
- **Design:** a triage written and approved before it ran: 2 arms x 4 owner types x 3 food places x 20 paired units = 480 lives of 14 days, only to estimate the size of the effect. **It has no formal reading**: no confirm / not-confirm, no cut applied.
- **Result:** +0.024 [+0.009; +0.038] on time well, against +0.062 [+0.058; +0.067] on the earlier pet (200 units). The two use different pets and seeds, so the pair is not a contrast. Alongside the estimates, without a reading, the official result describes that the current pet already starts higher, has little exhaustion (0.115 of its decisions), and near the feeder the measure is close to its maximum; these are the points the plan's prediction rested on, not a tested explanation.
- **Decision:** the question was closed without the confirmatory run; the decision records no reason. For context, the official result laid out that with 200 units an effect near +0.024 would have read "does not confirm" against the plan's margin (which has no source).
- **Every official number** is recomputed from `data/body_triage_lives.parquet` and asserted against `data/body_triage_reference.json` (tolerance 1e-9).

## Stack

uv (pinned environment, `uv.lock`) · DuckDB SQL and pandas over Parquet (pyarrow) · Jupyter notebooks rendered with Quarto (pinned as `quarto-cli` from PyPI) · matplotlib · scikit-learn · scipy · statsmodels (exploratory sections only).

## Reproduce

```
uv sync
uv run python scripts/reproduce.py
```

This runs the DuckDB integrity checks of both cases (`scripts/check_data.py`), exports the explorers' data (checked against both references; the page's JavaScript too when `node` is installed), then `quarto render` executes the four notebooks in place (each stops on a failed assertion; the outputs are written back into the `.ipynb`) and renders the site into `docs/` (ignored by git; open `docs/index.html`). A second run leaves `git status` clean.

On every push and pull request, GitHub Actions (`.github/workflows/site.yml`) runs the same command on Linux, so any number that no longer matches the official reference fails the build; on `main` the rendered site is deployed to GitHub Pages.

## Development

```
uv sync                      # the dev group (pytest, ruff) is installed by default; same as uv sync --group dev
uv run pytest -q             # unit tests: reading rules, paired estimates, explorer parity (no private data)
uv run ruff check            # lint (.py files; the notebooks are excluded, their code is shown on the site)
uv run ruff format --check   # formatting
uvx pre-commit install       # optional: run ruff on every commit (.pre-commit-config.yaml)
```

`_quarto.yml` sets `freeze: auto`, so a plain `uv run quarto preview` reuses the last execution of pages whose code has not changed (cached in `_freeze/`, not committed); `scripts/reproduce.py` and CI always execute everything. CI runs the lint, format and test steps before `reproduce.py`.

## Repo map

| path | what it is |
|---|---|
| `notebooks/02_case_study.ipynb` | case 1: the case study (single source of its page) |
| `notebooks/01_reproduce_official_results.ipynb` | case 1: reproduction appendix, all 18 official contrast x measure values |
| `resumo-pt.qmd` | case 1: one-page summary in Portuguese (numbers computed at render time) |
| `notebooks/04_body_triage_case_study.ipynb` | case 2: the case study |
| `notebooks/03_reproduce_body_triage.ipynb` | case 2: reproduction appendix, every official estimate and descriptive table of the triage |
| `resumo-pt-corpo.qmd` | case 2: one-page summary in Portuguese |
| `explorer/reward.qmd`, `explorer/triage.qmd`, `explorer/paired.js` | interactive explorers (Observable JS, in the browser): the paired estimate and its 95% CI for any subset of owner types and places; exploratory |
| `casestudy/` | shared helpers: DuckDB views, paired contrasts, reading rules (case 1), triage estimates (`triage.py`), exploratory statistics after the results (`explore.py`: TOST, bootstrap, precision arithmetic), chart style |
| `data/lives.parquet`, `data/reference.json` | case 1: the published extract and the official numbers (see `data/SCHEMA.md`) |
| `data/body_triage_lives.parquet`, `data/body_triage_reference.json` | case 2: the published extract and the official numbers, including the earlier study's quoted values |
| `sql/checks.sql`, `sql/checks_body_triage.sql`, `scripts/check_data.py` | integrity checks run before anything else |
| `scripts/reproduce.py` | the one command above |
| `scripts/build_explorer_data.py`, `scripts/check_explorer_js.mjs` | export the explorers' data (`explorer/data/`, not committed) and check, in Python and in the page's own JavaScript, that they reproduce every official value of both references |
| `PROVENANCE.md` | where the published data comes from: checksums, sample sizes, dates and the commit timelines |
| `scripts/build_lives.py`, `scripts/build_reference.py`, `scripts/build_triage_lives.py`, `scripts/build_triage_reference.py` | rebuild the extracts and the references from the private source files (not needed to reproduce) |
| `_quarto.yml`, `index.qmd` | Quarto website config and landing page; the site renders into `docs/` (not committed) |
| `.github/workflows/site.yml` | CI: lint, tests, reproduce everything on Linux, then deploy the site to GitHub Pages from `main` |
| `tests/` | pytest unit tests of the helpers in `casestudy/` and of the explorer's algorithm |
| `.pre-commit-config.yaml` | ruff hooks for pre-commit (not installed by default) |
| `.python-version` | the Python version the lock was built with |
| `scripts/make_cover.py`, `assets/` | the site's social-preview cover (drawn from the two reference files), favicon and stylesheet |
| `CITATION.cff` | how to cite this work (also shown as BibTeX on the site's landing page) |

## License

Code (`casestudy/`, `scripts/`, `sql/`, the notebooks' code cells): MIT. The text, figures, data and rendered site: all rights reserved. Details in [`LICENSE`](LICENSE).

---
title: "Provenance"
---

Where the published data comes from, and when each step happened. The study was run in the project's private research repository; the commit hashes below are from that repository's history.

## The study

- **Sample:** 9,600 simulated lives = 4 arms × 12 cells (4 owner types × 3 places) × 200 paired units; 14 simulated days per life, 1,344 decisions per life (96 a day, one every 15 simulated minutes).
- **Run once,** with 4 processes, on 2026-11-20 (times in UTC−3).

## Source files (sha256)

| file | what it is | sha256 |
|---|---|---|
| `resultado.json` | the official result: arm means, contrasts, breakdowns, reading labels | `97892493ab0b3c5b551e3319351cfd5e62e69b1ac2156668c8d967ac235360ae` |
| `medidas.json` | the per-life measures (uncompressed) | `e8333972cc635f366ef7ae41b1e767adaa192858168d0a44310e3e7e3ad0e413` |
| `medidas.json.gz` | the same, as stored (gzip) | `24bee0aadc553cbd5cc3363af68579d6de2c12420a82a3c68289e190dc2e8452` |
| `vidas.tar.gz` | the event logs of the 9,600 lives (not published) | `3a68a35f411c90ddcbe0b8fb110a8d5d21b836ac17d140a610c0b6007d0fe37a` |

The checksums of `resultado.json`, `medidas.json` and `vidas.tar.gz` are the ones recorded in the run's metadata file, and each was recomputed from the file itself. `scripts/build_reference.py` refuses to build `data/reference.json` unless `resultado.json` matches its checksum, and `scripts/build_lives.py` does the same for `medidas.json` before writing `data/lives.parquet`.

## Timeline (2026-11-20, UTC−3)

| time | event | commit |
|---|---|---|
| 14:06:26 | pre-registration entry committed | `455c6d61` |
| 14:19:51 | analysis plan approved | `5e83e59e` |
| 15:13:35 | simulation code merged; the lives were run on this commit | `82551431` |
| 15:51:02 | run started | |
| 18:36:06 | all 9,600 lives measured and saved; the analysis step that followed crashed (time not recorded) | |
| 18:38:22 | fix committed (the analysis was re-run on this commit) | `56921401` |
| 18:41:21 | re-analysis of the saved measurements finished | |
| 18:44:48 | result written | `daca1efb` |

The commit times are from the repository history; the run times (start, measurements saved, end of the re-analysis) and the two commits the run and the re-analysis used are from the run's metadata file. The case study's [appendix](notebooks/02_case_study.ipynb#appendix-the-pre-registration-entry) quotes the relevant lines of the pre-registration entry as committed in `455c6d61`.

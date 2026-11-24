---
title: "Provenance"
---

Where the published data comes from, and when each step happened. Both studies were run in the project's private research repository; the commit hashes below are from that repository's history.

## Case 1: the reward study {#case-1}

### The study

- **Sample:** 9,600 simulated lives = 4 arms × 12 cells (4 owner types × 3 places) × 200 paired units; 14 simulated days per life, 1,344 decisions per life (96 a day, one every 15 simulated minutes).
- **Run once,** with 4 processes, on 2026-11-20 (times in UTC−3).

### Source files (sha256)

| file | what it is | sha256 |
|---|---|---|
| `resultado.json` | the official result: arm means, contrasts, breakdowns, reading labels | `97892493ab0b3c5b551e3319351cfd5e62e69b1ac2156668c8d967ac235360ae` |
| `medidas.json` | the per-life measures (uncompressed) | `e8333972cc635f366ef7ae41b1e767adaa192858168d0a44310e3e7e3ad0e413` |
| `medidas.json.gz` | the same, as stored (gzip) | `24bee0aadc553cbd5cc3363af68579d6de2c12420a82a3c68289e190dc2e8452` |
| `vidas.tar.gz` | the event logs of the 9,600 lives (not published) | `3a68a35f411c90ddcbe0b8fb110a8d5d21b836ac17d140a610c0b6007d0fe37a` |

The checksums of `resultado.json`, `medidas.json` and `vidas.tar.gz` are the ones recorded in the run's metadata file, and each was recomputed from the file itself. `scripts/build_reference.py` refuses to build `data/reference.json` unless `resultado.json` matches its checksum, and `scripts/build_lives.py` does the same for `medidas.json` before writing `data/lives.parquet`.

### Timeline (2026-11-20, UTC−3)

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

## Case 2: the body-variant triage {#case-2}

### The study

- **Sample:** 480 simulated lives = 2 arms × 12 cells (4 owner types × 3 places) × 20 paired units; 14 simulated days per life, one decision every 15 simulated minutes.
- **Run once,** with 4 processes, on 2026-11-21 (times in UTC−3), on commit `e5d95bfc`, with a clean working tree. That commit carried the approved plan and addendum unchanged: the plan file's checksum recorded by the run equals the file as approved in `d69a2500`.
- **Not run:** the confirmatory study of 200 units the plan describes. No life of it exists.

### Source files (sha256)

| file | what it is | sha256 |
|---|---|---|
| `resultado.json` | the official result of the triage: estimates, descriptive tables, the values quoted from the earlier study | `02a9e2f05d1895264edd36a3ad433509a55f05f63cf5761837c8849a83a62887` |
| `medidas.json` | the per-life measures | `937dad3e7e997e0454191b6f1d0d7b607ac38d7b478ed06ba5b2ca429aa401be` |
| `vidas.tar.gz` | the event logs of the 480 lives (not published) | `8b4d9a3af7209ca1f5523a4542ce1fd02fbbaed93ed45bd4729816022407d491` |
| `meta.json` | the run's metadata; only its start, end, duration and process count are copied into the reference | `7b16e08c74860480d20adb9d89bf684cfa540e885892b36e0760677a0ff71b46` |
| C4 `resultado.json` | the earlier study's result, from which the triage's result quotes its comparison values (not published) | `136c304837710a8bf543c63530ad44b6b898784e1dfc84b4ef574359b7969f2d` |

The checksums of `resultado.json`, `medidas.json` and `vidas.tar.gz` are the ones recorded in the run's metadata file, and each was recomputed from the file itself; the metadata file's own checksum was computed from the file. The C4 checksum is the one the triage's result records next to the quoted values, and it equals the C4 result file in the repository. `scripts/build_triage_reference.py` refuses to build `data/body_triage_reference.json` unless `resultado.json` and `meta.json` match their checksums and the quoted values come from that C4 result, and `scripts/build_triage_lives.py` does the same for `medidas.json` before writing `data/body_triage_lives.parquet`.

### Timeline (UTC−3)

| time | event | commit |
|---|---|---|
| 2026-11-20 14:04:14 | earlier study (C4) result committed | `4e5f4f64` |
| 2026-11-20 15:59:30 | analysis plan proposed, with its prediction ("does not confirm") written down | `51f02fe9` |
| 2026-11-21 00:42:17 | analysis plan approved | `3c223667` |
| 2026-11-21 00:54:27 | simulation code merged | `bc0d3b43` |
| 2026-11-21 11:35:38 | addendum 1 proposed (a 20-unit triage before the 200-unit run) with the code's triage mode | `715f889c` |
| 2026-11-21 11:37:17 | addendum 1 approved | `d69a2500` |
| 2026-11-21 13:49:12 | triage started | `e5d95bfc` |
| 2026-11-21 13:58:24 | triage finished: 480 lives measured and saved, result written (recorded duration 551.7 s, 9 min 11 s) | |
| 2026-11-21 14:01:14 | triage result committed | `f5d6a7cd` |
| 2026-11-21 16:55:16 | question closed without the 200-unit run | `23733ac3` |

The commit times are the commits' commit dates from the repository history (for `715f889c` the author date is earlier, 11:21:35; for the other commits the two dates coincide); the run times, the duration and the commit the run used are from the run's metadata file.

---
pretty_name: "Two experiments on a virtual pet: simulated lives"
license: other
license_name: all-rights-reserved
license_link: https://github.com/matheusmmmp/digilab-reward-case-study/blob/main/LICENSE
language:
  - en
tags:
  - simulation
  - synthetic
  - tabular
  - pre-registration
  - paired-design
  - reproducibility
  - virtual-pet
size_categories:
  - 1K<n<10K
configs:
  - config_name: reward_test
    data_files:
      - split: train
        path: data/lives.parquet
    default: true
  - config_name: body_triage
    data_files:
      - split: train
        path: data/body_triage_lives.parquet
---

# Two experiments on a virtual pet: simulated lives

The per-life data behind two data-science case studies on the same simulated virtual pet. Each row is **one simulated pet life**; there are no humans and no personal data in it.

- Site (the case studies, every official number recomputed from these tables): <https://matheusmmmp.github.io/digilab-reward-case-study/>
- Code and the same files: <https://github.com/matheusmmmp/digilab-reward-case-study>

| config | file | rows | columns | case study |
|---|---|---|---|---|
| `reward_test` | `data/lives.parquet` | 9,600 | 13 | Case 1: does reward keep a virtual pet awake? A pre-registered simulation study |
| `body_triage` | `data/body_triage_lives.parquet` | 480 | 14 | Case 2: the effect that shrank (a 20-unit triage with no formal reading) |

Each config has a single split, `train`, which is simply the whole table: the data was not made for training models, and there is no held-out set.

```python
from datasets import load_dataset

lives = load_dataset("<user>/digilab-reward-case-study", "reward_test", split="train")
triage = load_dataset("<user>/digilab-reward-case-study", "body_triage", split="train")
```

## `reward_test`: the reward study (case 1)

9,600 lives = 4 arms × 12 cells (4 owner types × 3 places) × 200 paired units. Each life lasts 14 simulated days and has 1,344 decisions (96 a day, one every 15 simulated minutes), so a fraction of decisions can be read as a fraction of the pet's day.

- **Arms (4):** what happens when the owner pets the pet right after it eats or plays.
  - `no_petting` (code `R0`): no extra petting.
  - `petting_body_only` (`R-CORPO`): extra petting acts on the pet's body state only; the learning agent receives no reward credit for it.
  - `petting_with_credit` (`R-CB`): extra petting, and the learning agent receives reward credit for it.
  - `petting_with_credit_random_time` (`R-SORT`): the same reward credit, but delivered at a randomly drawn time instead of right after eating or playing.
- **Owners (4):** `attentive`, `neglectful`, `random`, `inconsistent` (how reliably the simulated owner cares for the pet).
- **Places (3):** `at_feeder`, `near`, `far` (where the pet's area lies relative to the feeder).
- **Units:** 200 per cell, numbered 1..200. A unit is paired across arms: the same (unit, owner, place) appears once in each of the 4 arms.

| column | type | unit | meaning |
|---|---|---|---|
| `arm_code` | string | - | Arm code: `R0`, `R-CORPO`, `R-CB`, `R-SORT`. |
| `arm` | string | - | Arm label (see above). |
| `owner` | string | - | Owner type. |
| `place` | string | - | Place type. |
| `unit` | int | - | Paired unit index, 1..200. |
| `awake_frac_d1_14` | float | fraction 0-1 | Fraction of the pet's decisions over days 1-14 that were not "sleep". The primary outcome of the question. |
| `awake_frac_d8_14` | float | fraction 0-1 | The same fraction over days 8-14 only. |
| `time_well` | float | fraction 0-1 | Fraction of the pet's decisions taken while it was neither deprived (e.g. hungry) nor exhausted, with fixed thresholds. The project's primary welfare measure. |
| `episode_rate` | float | fraction 0-1 | Share of hunger episodes the pet closed by eating within the episode's time window (the others expired or the life ended). |
| `eat_decisions` | int | count | Number of times the agent chose to eat. |
| `play_decisions` | int | count | Number of times the agent chose to play. |
| `sleep_decisions` | int | count | Number of times the agent chose to sleep. |
| `extra_pets` | int | count | Petting events added by the study design (arm-dependent; 0 in `no_petting`). |

## `body_triage`: the body-variant triage (case 2)

480 lives = 2 arms × 12 cells (4 owner types × 3 places) × 20 paired units. Each life lasts 14 simulated days of the current version of the pet; the pet takes a decision every 15 simulated minutes.

- **Arms (2):** `control` (the pet as it is) and `body_variant` (the same pet with a variant of its body physiology). The variant is not described further.
- **Owners (4):** `attentive`, `neglectful`, `random`, `inconsistent`. `neglectful` and `random` are the two that let the food run out.
- **Places (3):** where the owner puts the food. `at_feeder`: at the pet's feeder. `far`: far from the pet, at a direction and distance drawn anew at every feeding. `far_fixed`: at one of three fixed spots far from the feeder, drawn once per life; each feeding lands on one of the three at random.
- **Cells:** in every life, (`inconsistent`, `at_feeder`) is identical to (`attentive`, `at_feeder`), so the official result also reports estimates over the 11 distinct cells.
- **Units:** 20 per cell, numbered 1..20. A unit is paired across arms: the same (unit, owner, place) appears once in each arm.

| column | type | unit | meaning |
|---|---|---|---|
| `arm` | string | - | `control` or `body_variant`. |
| `owner` | string | - | Owner type. |
| `place` | string | - | Place type. |
| `unit` | int | - | Paired unit index, 1..20. |
| `time_well` | float | fraction 0-1 | Fraction of the pet's decisions over days 1-14 taken while it was neither deprived nor exhausted (fixed thresholds). The primary measure. |
| `time_well_d8_14` | float | fraction 0-1 | The same over days 8-14 only. |
| `health_d8_14` | float | 0-1 scale | The pet's mean health level over the decisions of days 8-14. |
| `deprivation` | float | fraction 0-1 | Fraction of the decisions over days 1-14 taken while food, hygiene or energy was below the deprivation threshold. |
| `exhaustion` | float | fraction 0-1 | Fraction of the decisions over days 1-14 taken while energy was below the exhaustion threshold. A decision counts in `time_well` exactly when it counts in neither of these two. |
| `episode_rate` | float | fraction 0-1 | Share of hunger episodes the pet closed, within the episode's time window, by eating a ripe ration from the owner that lowered its hunger. Eating a spoiled ration does not close an episode, and an episode in which the pet was sated by other food counts as not closed. |
| `meals_per_day` | float | count per day | Rations from the owner eaten (spoiled ones included), divided by the 14 days. |
| `sleep_frac_ticks` | float | fraction 0-1 | Fraction of the simulation's time steps in which the pet was asleep. |
| `kicks` | int | count | Decisions in which the pet kicked the ball. |
| `play_decisions` | int | count | Decisions in which the pet chose "play" (with or without the ball). |

The data dictionary on the site ([Data schema](https://matheusmmmp.github.io/digilab-reward-case-study/data/SCHEMA.html)) is the reference for both tables; it also describes the official reference numbers (`data/reference.json`, `data/body_triage_reference.json`), which are in the GitHub repository and not mirrored here.

## How it was produced

Both studies were run once each, in the project's private research repository, by a simulator of the virtual pet: the reward study on 2026-11-20 (pre-registered before the run) and the body-variant triage on 2026-11-21 (its plan approved before the run). Each table is an extract of the run's per-life measures, rebuilt by a script that refuses to write it unless the source file matches the checksum the run recorded; the source checksums, sample sizes and commit timelines are on the site's [Provenance](https://matheusmmmp.github.io/digilab-reward-case-study/PROVENANCE.html) page, and the case studies recompute every official number from these two files. The files here are byte-identical to the ones in the repository:

| file | sha256 |
|---|---|
| `data/lives.parquet` | `f4de55cc0f63ca27760eac88b4c7141756ff4441f4644a14ff8d8847ec198df8` |
| `data/body_triage_lives.parquet` | `a76f651fb899ca19eeff27cb9303d739129aa6a777791292d08d97618fbba1fe` |

Internal agent state, per-decision logs, seeds and the body variant's definition are not published.

## License

**All rights reserved.** © 2026 Matheus de Medeiros Pereira. The data is published so that the case studies can be checked: you may read it, download it and load it (for example with `datasets`, pandas or DuckDB) to view or evaluate the case study and its numbers. No license is granted to redistribute it, to publish modified versions or derived datasets, or to use it for other purposes; these terms are the same as for the data in the GitHub repository ([LICENSE](https://github.com/matheusmmmp/digilab-reward-case-study/blob/main/LICENSE): the code there is MIT, the text, figures, data and site are all rights reserved). For any other use, ask through a [GitHub issue](https://github.com/matheusmmmp/digilab-reward-case-study/issues).

## Citation

```bibtex
@misc{demedeirospereira2026virtualpet,
  author = {de Medeiros Pereira, Matheus},
  title  = {Two experiments on a virtual pet},
  year   = {2026},
  month  = nov,
  url    = {https://matheusmmmp.github.io/digilab-reward-case-study/},
  note   = {Code and data: https://github.com/matheusmmmp/digilab-reward-case-study}
}
```

The same metadata is in [`CITATION.cff`](https://github.com/matheusmmmp/digilab-reward-case-study/blob/main/CITATION.cff).

## Limitations

- **Simulated data.** Every row is a life of a simulated virtual pet with simulated owners. Nothing here measures real animals or people, and the results describe this simulator, not the real world.
- **No humans, no personal data.** The owners are four fixed simulated behaviours; no person took part, and the tables contain no personal or identifying information.
- **Extracts, not the full runs.** Only per-life outcome measures are published; the per-decision event logs and the pet's internal state are not, so analyses that need them cannot be done from these tables.
- **Design-bound.** The units are paired across arms within each cell; analyses that ignore the pairing (for example, treating the rows as independent) do not match the studies' design. Case 2 is a 20-unit triage planned only to estimate the size of an effect, with no formal reading.

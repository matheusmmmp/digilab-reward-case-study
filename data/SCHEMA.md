---
title: "Data dictionary"
---

Two published tables, one per case study. Both have one row per simulated pet life.

## Case 1: `data/lives.parquet` {#case-1}

One row per simulated pet life: 9,600 rows, 13 columns. Each life lasts 14 simulated days and has 1,344 decisions (96 a day, one every 15 simulated minutes), so a fraction of decisions can be read as a fraction of the pet's day.

### Design

- **Arms (4):** what happens when the owner pets the pet right after it eats or plays.
  - `no_petting` (code `R0`): no extra petting.
  - `petting_body_only` (`R-CORPO`): extra petting acts on the pet's body state only; the learning agent receives no reward credit for it.
  - `petting_with_credit` (`R-CB`): extra petting, and the learning agent receives reward credit for it.
  - `petting_with_credit_random_time` (`R-SORT`): the same reward credit, but delivered at a randomly drawn time instead of right after eating or playing.
- **Owners (4):** `attentive`, `neglectful`, `random`, `inconsistent` (how reliably the simulated owner cares for the pet).
- **Places (3):** `at_feeder`, `near`, `far` (where the pet's area lies relative to the feeder).
- **Cells:** 4 owners x 3 places = 12 cells.
- **Units:** 200 per cell, numbered 1..200. A unit is paired across arms: the same (unit, owner, place) appears once in each of the 4 arms. 4 arms x 12 cells x 200 units = 9,600 lives.

### Columns

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

### Deliberately not exported

Internal agent state, per-decision logs and seeds are not published. Only the outcome measures above are published. The agent is described only as a learning agent that can receive reward credit.

### Reference numbers

`data/reference.json` holds the official per-arm means and the paired contrasts (D1 = petting_with_credit vs no_petting, D2 = petting_with_credit vs petting_with_credit_random_time, D3 = petting_with_credit vs petting_body_only; mean and confidence interval) computed in the original study, plus the sha256 of the source results file. It also holds the official breakdowns by owner (`by_owner`) and by place (`by_place`) for `awake_frac_d1_14` and `time_well`, the official reading labels (`readings`, with the original wording), the number of pre-registered guards that were not measured, whether the pre-registered dose premise held (`dose_premise_held`), and the pre-registered constants (`preregistered`). `scripts/check_data.py` verifies that the parquet reproduces the arm means to within 1e-9.

## Case 2: `data/body_triage_lives.parquet` {#case-2}

One row per simulated pet life of the body-variant triage: 480 rows, 14 columns. Each life lasts 14 simulated days of the current version of the pet; the pet takes a decision every 15 simulated minutes.

### Design

- **Arms (2):** `control` (the pet as it is) and `body_variant` (the same pet with a variant of its body physiology). The variant is not described further.
- **Owners (4):** `attentive`, `neglectful`, `random`, `inconsistent`. `neglectful` and `random` are the two that let the food run out.
- **Places (3):** where the owner puts the food. `at_feeder`: at the pet's feeder. `far`: far from the pet, at a direction and distance drawn anew at every feeding. `far_fixed`: at one of three fixed spots far from the feeder, drawn once per life; each feeding lands on one of the three at random.
- **Cells:** 4 owners x 3 places = 12 cells. In every life, (`inconsistent`, `at_feeder`) is identical to (`attentive`, `at_feeder`), so the official result also reports estimates over the 11 distinct cells.
- **Units:** 20 per cell, numbered 1..20. A unit is paired across arms: the same (unit, owner, place) appears once in each arm. 2 arms x 12 cells x 20 units = 480 lives.

### Columns

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

### Deliberately not exported

The body variant's definition, the pet's internal state, per-decision logs and seeds are not published. Every source measure whose official numbers this table reproduces is included; no measure that was requested was dropped. Of the earlier study (C4), only the values that the triage's official result quotes are published, in the reference file; none of its per-life data.

### Reference numbers

`data/body_triage_reference.json` holds the triage's official estimates (`estimates`: arm levels, mean, sd and 95% CI of `body_variant − control` over the 20 units, for time well over 12 cells, 11 cells and each place, health over 12 cells, over the 6 neglectful/random cells and in each of them, and the episode rate in `far_fixed`), the time-well estimate divided by the plan's margin (`effect_over_margin`), the descriptive values by set of cells for every published measure plus the share of lives with `time_well` above 0.99 (`by_group`), time well in each cell (`time_well_by_cell`), the per-arm means (`arm_means`), the count behind the 11 distinct cells (`inconsistent_equals_attentive`), the plan's margin, the sizes, `formal_reading: false`, the run's start, end, duration and process count (`run`, from its metadata file), and the earlier study's values as quoted by the official result (`c4_quoted`, with the checksum of the C4 result they come from), plus the sha256 of the source results file. `scripts/check_data.py` verifies that the parquet reproduces the arm means to within 1e-9.

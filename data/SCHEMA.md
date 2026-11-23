# Data dictionary: `data/lives.parquet`

One row per simulated pet life: 9,600 rows, 13 columns. Each life lasts 14 simulated days and has 1,344 decisions (96 a day, one every 15 simulated minutes), so a fraction of decisions can be read as a fraction of the pet's day.

## Design

- **Arms (4):** what happens when the owner pets the pet right after it eats or plays.
  - `no_petting` (code `R0`): no extra petting.
  - `petting_body_only` (`R-CORPO`): extra petting acts on the pet's body state only; the learning agent receives no reward credit for it.
  - `petting_with_credit` (`R-CB`): extra petting, and the learning agent receives reward credit for it.
  - `petting_with_credit_random_time` (`R-SORT`): the same reward credit, but delivered at a randomly drawn time instead of right after eating or playing.
- **Owners (4):** `attentive`, `neglectful`, `random`, `inconsistent` (how reliably the simulated owner cares for the pet).
- **Places (3):** `at_feeder`, `near`, `far` (where the pet's area lies relative to the feeder).
- **Cells:** 4 owners x 3 places = 12 cells.
- **Units:** 200 per cell, numbered 1..200. A unit is paired across arms: the same (unit, owner, place) appears once in each of the 4 arms. 4 arms x 12 cells x 200 units = 9,600 lives.

## Columns

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

## Deliberately not exported

Internal agent state, per-decision logs and seeds are not published. Only the outcome measures above are published. The agent is described only as a learning agent that can receive reward credit.

## Reference numbers

`data/reference.json` holds the official per-arm means and the paired contrasts (D1 = petting_with_credit vs no_petting, D2 = petting_with_credit vs petting_with_credit_random_time, D3 = petting_with_credit vs petting_body_only; mean and confidence interval) computed in the original study, plus the sha256 of the source results file. It also holds the official breakdowns by owner (`by_owner`) and by place (`by_place`) for `awake_frac_d1_14` and `time_well`, the official reading labels (`readings`, with the original wording), the number of pre-registered guards that were not measured, whether the pre-registered dose premise held (`dose_premise_held`), and the pre-registered constants (`preregistered`). `scripts/check_data.py` verifies that the parquet reproduces the arm means to within 1e-9.

-- Case 2 (body-variant triage). Each block returns one boolean (arm_means returns a table). {lives} is replaced by the parquet path.
-- name: rows_480
SELECT count(*) = 480 FROM read_parquet('{lives}');
-- name: rows_240_per_arm
SELECT count(*) = 2 AND min(n) = 240 AND max(n) = 240 FROM (SELECT arm, count(*) n FROM read_parquet('{lives}') GROUP BY 1);
-- name: twelve_cells
SELECT count(*) = 12 FROM (SELECT DISTINCT owner, place FROM read_parquet('{lives}'));
-- name: 20_rows_per_arm_cell
SELECT count(*) = 24 AND min(n) = 20 AND max(n) = 20 FROM (SELECT arm, owner, place, count(*) n FROM read_parquet('{lives}') GROUP BY ALL);
-- name: units_1_to_20
SELECT min(unit) = 1 AND max(unit) = 20 AND count(DISTINCT unit) = 20 FROM read_parquet('{lives}');
-- name: complete_pairing
SELECT count(*) = 240 AND min(arms) = 2 AND max(arms) = 2 AND min(n) = 2 AND max(n) = 2
FROM (SELECT unit, owner, place, count(DISTINCT arm) arms, count(*) n FROM read_parquet('{lives}') GROUP BY ALL);
-- name: no_nulls
SELECT count(*) = 0 FROM read_parquet('{lives}') WHERE COLUMNS(*) IS NULL;
-- name: fractions_in_0_1
SELECT count(*) = 0 FROM read_parquet('{lives}')
WHERE time_well NOT BETWEEN 0 AND 1 OR time_well_d8_14 NOT BETWEEN 0 AND 1 OR health_d8_14 NOT BETWEEN 0 AND 1
   OR deprivation NOT BETWEEN 0 AND 1 OR exhaustion NOT BETWEEN 0 AND 1 OR episode_rate NOT BETWEEN 0 AND 1
   OR sleep_frac_ticks NOT BETWEEN 0 AND 1;
-- name: time_well_is_neither_deprived_nor_exhausted
SELECT count(*) = 0 FROM read_parquet('{lives}') WHERE time_well > 1 - greatest(deprivation, exhaustion) + 1e-12;
-- name: arm_means
SELECT arm, avg(time_well) AS time_well, avg(time_well_d8_14) AS time_well_d8_14, avg(health_d8_14) AS health_d8_14,
       avg(deprivation) AS deprivation, avg(exhaustion) AS exhaustion, avg(episode_rate) AS episode_rate,
       avg(meals_per_day) AS meals_per_day, avg(sleep_frac_ticks) AS sleep_frac_ticks,
       avg(kicks) AS kicks, avg(play_decisions) AS play_decisions
FROM read_parquet('{lives}') GROUP BY arm ORDER BY arm;

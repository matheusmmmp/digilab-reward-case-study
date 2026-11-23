-- Each block returns one boolean (arm_means returns a table). {lives} is replaced by the parquet path.
-- name: rows_9600
SELECT count(*) = 9600 FROM read_parquet('{lives}');
-- name: rows_2400_per_arm
SELECT count(*) = 4 AND min(n) = 2400 AND max(n) = 2400 FROM (SELECT arm_code, count(*) n FROM read_parquet('{lives}') GROUP BY 1);
-- name: twelve_cells
SELECT count(*) = 12 FROM (SELECT DISTINCT owner, place FROM read_parquet('{lives}'));
-- name: 200_rows_per_arm_cell
SELECT count(*) = 48 AND min(n) = 200 AND max(n) = 200 FROM (SELECT arm_code, owner, place, count(*) n FROM read_parquet('{lives}') GROUP BY ALL);
-- name: units_1_to_200
SELECT min(unit) = 1 AND max(unit) = 200 AND count(DISTINCT unit) = 200 FROM read_parquet('{lives}');
-- name: complete_pairing
SELECT count(*) = 2400 AND min(arms) = 4 AND max(arms) = 4 AND min(n) = 4 AND max(n) = 4
FROM (SELECT unit, owner, place, count(DISTINCT arm_code) arms, count(*) n FROM read_parquet('{lives}') GROUP BY ALL);
-- name: no_nulls
SELECT count(*) = 0 FROM read_parquet('{lives}') WHERE COLUMNS(*) IS NULL;
-- name: fractions_in_0_1
SELECT count(*) = 0 FROM read_parquet('{lives}')
WHERE awake_frac_d1_14 NOT BETWEEN 0 AND 1 OR awake_frac_d8_14 NOT BETWEEN 0 AND 1 OR time_well NOT BETWEEN 0 AND 1 OR episode_rate NOT BETWEEN 0 AND 1;
-- name: arm_means
SELECT arm, avg(awake_frac_d1_14) AS awake_frac_d1_14, avg(awake_frac_d8_14) AS awake_frac_d8_14,
       avg(time_well) AS time_well, avg(episode_rate) AS episode_rate,
       avg(eat_decisions) AS eat_decisions, avg(play_decisions) AS play_decisions
FROM read_parquet('{lives}') GROUP BY arm ORDER BY arm;

// Run the explorer's own JavaScript (explorer/paired.js) over the exported JSON and check it
// against the official references, for the same selections as scripts/build_explorer_data.py.
// Usage: node scripts/check_explorer_js.mjs   (run by scripts/reproduce.py when node is on PATH)
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const read = (p) => readFileSync(join(ROOT, p), "utf8");
// loaded as a module from its source, so any Node version treats it as ESM
const src = read("explorer/paired.js");
const { estimate, selectCells, fmt } = await import("data:text/javascript," + encodeURIComponent(src));
const TOL = 1e-9;
let count = 0;
let worst = 0;

function check(got, ref, what) {
  if (got === null) throw new Error(`${what}: no estimate`);
  for (const k of ["mean", "sd", "ci_low", "ci_high"]) {
    if (!(k in ref)) continue;
    const d = Math.abs(got[k] - ref[k]);
    if (!(d <= TOL)) throw new Error(`${what} ${k}: ${got[k]} vs ${ref[k]} (|diff| ${d})`);
    worst = Math.max(worst, d);
  }
  count++;
}

// case 1
{
  const data = JSON.parse(read("explorer/data/reward.json"));
  const ref = JSON.parse(read("data/reference.json"));
  const all = selectCells(data, data.owners, data.places);
  for (const m of Object.keys(data.data))
    for (const c of Object.keys(data.contrasts)) check(estimate(data, m, c, all), ref.contrasts[m][c], `${m} ${c}`);
  for (const [o, byM] of Object.entries(ref.by_owner))
    for (const [m, byC] of Object.entries(byM))
      for (const [c, r] of Object.entries(byC)) check(estimate(data, m, c, selectCells(data, [o], data.places)), r, `${o} ${m} ${c}`);
  for (const [p, byM] of Object.entries(ref.by_place))
    for (const [m, byC] of Object.entries(byM))
      for (const [c, r] of Object.entries(byC)) check(estimate(data, m, c, selectCells(data, data.owners, [p])), r, `${p} ${m} ${c}`);
  if (estimate(data, "awake_frac_d1_14", "D1", selectCells(data, [], data.places)) !== null) throw new Error("empty selection");
  const head = fmt(estimate(data, "awake_frac_d1_14", "D1", all), 4);
  if (head !== "-0.0109 [-0.0113; -0.0105]") throw new Error(`case 1 headline ${head}`);
  console.log(`explorer js: case 1 default shows D1 awake ${head}`);
}

// case 2
{
  const data = JSON.parse(read("explorer/data/triage.json"));
  const ref = JSON.parse(read("data/body_triage_reference.json"));
  const copy = "inconsistent|at_feeder";
  const groups = {
    "12_cells": selectCells(data, data.owners, data.places),
    "11_cells": selectCells(data, data.owners, data.places, [copy]),
    neglectful_and_random: selectCells(data, ["neglectful", "random"], data.places),
  };
  for (const p of data.places) groups[p] = selectCells(data, data.owners, [p]);
  const cellsOf = (g) => groups[g] ?? [g];
  for (const [key, r] of Object.entries(ref.estimates)) {
    const [m, g] = [key.slice(0, key.indexOf("|")), key.slice(key.indexOf("|") + 1)];
    check(estimate(data, m, "V", cellsOf(g)), r, key);
  }
  for (const [g, byM] of Object.entries(ref.by_group))
    for (const [m, r] of Object.entries(byM)) if (m in data.data) check(estimate(data, m, "V", cellsOf(g)), r, `${g} ${m}`);
  for (const [cell, r] of Object.entries(ref.time_well_by_cell)) check(estimate(data, "time_well", "V", [cell]), r, cell);
  if (estimate(data, "time_well", "V", selectCells(data, ["inconsistent"], ["at_feeder"], [copy])) !== null)
    throw new Error("empty selection");
  const head = fmt(estimate(data, "time_well", "V", groups["12_cells"]), 3);
  if (head !== "+0.024 [+0.009; +0.038]") throw new Error(`case 2 headline ${head}`);
  console.log(`explorer js: case 2 default shows time well ${head}`);
}
console.log(`explorer js: ${count} official values reproduced by explorer/paired.js (max |diff| ${worst.toExponential(1)})`);

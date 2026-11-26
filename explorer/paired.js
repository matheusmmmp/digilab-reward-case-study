// The explorer's paired estimate, run in the browser over explorer/data/<case>.json.
// Same algorithm as estimate() in scripts/build_explorer_data.py, which checks it against
// the official references: per unit, the mean over the selected cells of the arm difference;
// estimate = mean over units; sd with ddof = 1; CI = mean +/- t * sd / sqrt(n), with the
// Student-t critical value t975 stored in the JSON (n does not change with the subset).

export function estimate(data, measure, contrast, selectedCells) {
  if (!selectedCells || selectedCells.length === 0) return null;
  const entry = data.data[measure];
  const values = entry[contrast];
  const den = entry.den || 1;
  const ncell = data.cells.length;
  const idx = selectedCells.map((c) => data.cells.indexOf(c));
  if (idx.some((i) => i < 0)) throw new Error("unknown cell");
  const n = data.n_units;
  const diffs = [];
  for (let u = 0; u < n; u++) {
    let s = 0;
    for (const c of idx) s += values[u * ncell + c];
    diffs.push(s / idx.length / den);
  }
  let total = 0;
  for (const x of diffs) total += x;
  const mean = total / n;
  let ss = 0;
  for (const x of diffs) ss += (x - mean) ** 2;
  const sd = Math.sqrt(ss / (n - 1));
  const half = (data.t975 * sd) / Math.sqrt(n);
  return { n, mean, sd, ci_low: mean - half, ci_high: mean + half, diffs, cells: idx.length };
}

export function selectCells(data, owners, places, drop = []) {
  const out = [];
  for (const o of data.owners)
    for (const p of data.places) {
      const c = `${o}|${p}`;
      if (owners.includes(o) && places.includes(p) && !drop.includes(c)) out.push(c);
    }
  return out;
}

// Name a checkbox group for screen readers (Inputs' own label is not tied to the group).
export function group(input, name) {
  input.setAttribute("role", "group");
  input.setAttribute("aria-label", name);
  return input;
}

export function signed(x, digits) {
  const s = Math.abs(x).toFixed(digits);
  return (x < 0 && Number(s) !== 0 ? "-" : "+") + s;
}

export function fmt(r, digits) {
  return `${signed(r.mean, digits)} [${signed(r.ci_low, digits)}; ${signed(r.ci_high, digits)}]`;
}

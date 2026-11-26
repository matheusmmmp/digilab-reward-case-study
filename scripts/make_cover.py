"""Draw the site's social-preview cover (assets/cover.png, 1200 x 630) from the two official references.

The two headline estimates are read from data/reference.json and data/body_triage_reference.json, never typed in.
The PNG carries no timestamp or version metadata, so re-running it leaves the file byte-identical."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import sys  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from casestudy import style  # noqa: E402

OUT = ROOT / "assets" / "cover.png"
W, H, DPI = 1200, 630, 100


def signed(x: float, nd: int) -> str:
    return f"{x:+.{nd}f}".replace("-", "−")


def interval(r: dict, nd: int) -> str:
    return f"{signed(r['mean'], nd)} [{signed(r['ci_low'], nd)}; {signed(r['ci_high'], nd)}]"


def load():
    ref1 = json.loads((ROOT / "data" / "reference.json").read_text(encoding="utf-8"))
    ref2 = json.loads((ROOT / "data" / "body_triage_reference.json").read_text(encoding="utf-8"))
    d1 = ref1["contrasts"]["awake_frac_d1_14"]["D1"]
    tw = ref2["estimates"]["time_well|12_cells"]
    return [
        dict(case="Case 1 · a pre-registered experiment, 9,600 lives",
             measure="D1 on the awake fraction", r=d1, nd=4,
             reading="reward makes the pet sleep slightly more"),
        dict(case="Case 2 · a 20-unit triage, no formal reading",
             measure="body variant on time well", r=tw, nd=3,
             reading="the effect that shrank"),
    ]


def main() -> None:
    style.apply()
    rows = load()
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
    fig.text(0.06, 0.86, "Two experiments on a virtual pet", fontsize=40, fontweight="bold",
             color=style.INK, va="top")
    fig.text(0.06, 0.735, "Two data-science case studies. Every number recomputed from the published data.",
             fontsize=17, color=style.INK_2, va="top")

    lo, hi = -0.025, 0.05  # one shared scale: both measures are fractions of the pet's decisions
    for k, row in enumerate(rows):
        top = 0.56 - k * 0.235
        fig.text(0.06, top, row["case"], fontsize=13, color=style.MUTED, va="top")
        fig.text(0.06, top - 0.05, row["reading"], fontsize=21, fontweight="bold", color=style.INK, va="top")
        fig.text(0.06, top - 0.115, f"{row['measure']}: {interval(row['r'], row['nd'])}",
                 fontsize=15, color=style.INK_2, va="top")
        ax = fig.add_axes([0.665, top - 0.15, 0.275, 0.15])
        r = row["r"]
        ax.axvline(0, color=style.BASELINE, lw=1.5, zorder=1)
        ax.plot([r["ci_low"], r["ci_high"]], [0, 0], color=style.ACCENT, lw=4, zorder=3,
                solid_capstyle="butt")
        ax.plot(r["mean"], 0, "o", ms=13, color=style.ACCENT, mec=style.SURFACE, mew=2.5, zorder=4)
        ax.set_xlim(lo, hi)
        ax.set_ylim(-1, 1)
        ax.set_yticks([])
        ax.set_xticks([-0.02, 0, 0.02, 0.04], ["−0.02", "0", "+0.02", "+0.04"])
        ax.tick_params(axis="x", labelsize=11)
        ax.grid(axis="x", color=style.GRID)
    fig.text(0.94, 0.045, "estimate and 95% interval, difference in fraction of decisions",
             fontsize=11, color=style.MUTED, ha="right", va="bottom")

    OUT.parent.mkdir(exist_ok=True)
    fig.savefig(OUT, dpi=DPI, metadata={"Software": None}, pil_kwargs={"optimize": True})
    plt.close(fig)
    print(f"cover: {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()

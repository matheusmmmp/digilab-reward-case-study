"""One quiet chart style for every figure (light surface, recessive axes, one accent)."""
import matplotlib as mpl

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
WASH = "#f0efec"
ACCENT = "#2a78d6"   # categorical slot 1: the series the story is about
CONTEXT = MUTED      # de-emphasised context marks (validated as a gray, not a category)


def apply() -> None:
    mpl.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE, "figure.dpi": 110,
        "font.family": "DejaVu Sans", "font.size": 10,
        "text.color": INK, "axes.labelcolor": INK_2, "axes.titlecolor": INK,
        "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "xtick.color": MUTED, "ytick.color": INK_2, "xtick.labelsize": 9, "ytick.labelsize": 9,
        "axes.edgecolor": BASELINE, "axes.linewidth": 1,
        "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
        "axes.grid": True, "axes.grid.axis": "x", "grid.color": GRID, "grid.linewidth": 1,
        "grid.linestyle": "-", "axes.axisbelow": True,
        "ytick.major.size": 0, "lines.linewidth": 2, "lines.solid_capstyle": "round",
        "legend.frameon": False, "svg.hashsalt": "casestudy",
    })

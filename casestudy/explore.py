"""Exploratory statistics added after the results (both cases): the equivalence view of a
reading rule, bootstrap intervals and the precision arithmetic of a planned run. Nothing here is
part of an official reading, and no result numbers live here."""

import numpy as np
from scipy import stats


def tost_paired(d: np.ndarray, delta: float) -> dict:
    """Two one-sided t tests (TOST) of the per-unit differences `d` against the band ±delta.
    `p_low` tests H0: mean <= -delta, `p_high` tests H0: mean >= +delta; `p` is the larger
    of the two. Both rejecting at alpha is the same as the (1 - 2 alpha) t interval lying
    strictly inside ±delta."""
    d = np.asarray(d, dtype=float)
    n = len(d)
    mean, se = float(d.mean()), float(d.std(ddof=1)) / np.sqrt(n)
    t_low, t_high = (mean + delta) / se, (mean - delta) / se
    p_low, p_high = float(stats.t.sf(t_low, n - 1)), float(stats.t.cdf(t_high, n - 1))
    return dict(n=n, mean=mean, se=se, t_low=t_low, p_low=p_low, t_high=t_high, p_high=p_high, p=max(p_low, p_high))


def smallest_margin(ci_low: float, ci_high: float) -> float:
    """The smallest band ±delta that contains the interval [ci_low, ci_high]."""
    return max(abs(ci_low), abs(ci_high))


def bootstrap_ci(d: np.ndarray, seed: int, n_resamples: int = 10_000, method: str = "BCa", level: float = 0.95):
    """Bootstrap interval of the mean of the per-unit differences (units resampled with
    replacement), with a fixed seed. Returns (low, high)."""
    res = stats.bootstrap(
        (np.asarray(d, dtype=float),),
        np.mean,
        n_resamples=n_resamples,
        method=method,
        confidence_level=level,
        rng=np.random.default_rng(seed),
    )
    return float(res.confidence_interval.low), float(res.confidence_interval.high)


def prob_ci_inside(mu: float, sd: float, n: int, delta: float, level: float = 0.95) -> float:
    """Probability that an n-unit Student-t interval lies entirely inside ±delta when the true
    mean difference is `mu` and the sd of the unit differences is `sd`. Normal approximation:
    the sample mean is N(mu, sd/sqrt(n)) and the half-width is taken at the true sd."""
    se = sd / np.sqrt(n)
    hw = float(stats.t.ppf(0.5 + level / 2, n - 1)) * se
    if hw >= delta:
        return 0.0
    return float(stats.norm.cdf((delta - hw - mu) / se) - stats.norm.cdf((-delta + hw - mu) / se))


def simulate_prob_ci_inside(mu: float, sd: float, n: int, delta: float, reps: int, seed: int, level: float = 0.95) -> float:
    """The same probability by simulation: `reps` samples of n normal unit differences, each
    with its own sample sd and t interval (fixed seed)."""
    rng = np.random.default_rng(seed)
    t = float(stats.t.ppf(0.5 + level / 2, n - 1))
    inside = 0
    for start in range(0, reps, 10_000):  # in blocks, to keep memory small
        x = rng.normal(mu, sd, size=(min(10_000, reps - start), n))
        m, hw = x.mean(axis=1), t * x.std(axis=1, ddof=1) / np.sqrt(n)
        inside += int(np.sum((m - hw > -delta) & (m + hw < delta)))
    return inside / reps

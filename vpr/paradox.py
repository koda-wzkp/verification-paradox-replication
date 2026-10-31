"""Per-program verification breadth and health, and their rank correlation."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, rankdata, spearmanr

from .mona import ASSESSED


def program_table(hist: dict, years: dict[int, int]) -> pd.DataFrame:
    rows = []
    for (arr, _ct, _k), h in hist.items():
        sts = [s for _r, s in h]
        ev = [s for s in sts if s in ASSESSED]
        rows.append({"arr": arr, "ever": bool(ev), "last": ev[-1] if ev else None,
                     "first": ev[0] if ev else None, "reviews": len(sts),
                     "assessed_reviews": sum(s in ASSESSED for s in sts)})
    c = pd.DataFrame(rows)
    g = c.groupby("arr")
    n_ass = g.ever.sum()
    p = pd.DataFrame({
        "n": g.size(),
        "verification": g.ever.mean(),                                   # breadth
        "verification_freq": g.assessed_reviews.sum() / g.reviews.sum(),  # frequency
        "health": g.apply(lambda q: (q["last"] == "Met").sum()) / n_ass,
        "health_incl_delay": g.apply(lambda q: q["last"].isin(["Met", "Met with delay"]).sum()) / n_ass,
        "baseline": g.apply(lambda q: (q["first"] == "Met").sum()) / n_ass,
    })
    p["year"] = p.index.map(years)
    return p.replace([np.inf, -np.inf], np.nan)


def rho_ci(df: pd.DataFrame, x: str, y: str, n_boot: int = 2000, seed: int = 20261030) -> dict:
    d = df.dropna(subset=[x, y])
    rho = spearmanr(d[x], d[y])[0]
    rng = np.random.default_rng(seed)
    b = []
    for _ in range(n_boot):
        i = rng.integers(0, len(d), len(d))
        b.append(spearmanr(d[x].values[i], d[y].values[i])[0])
    lo, hi = np.nanpercentile(b, [2.5, 97.5])
    return {"rho": float(rho), "ci95": [float(lo), float(hi)], "n": len(d)}


def partial_rho(df: pd.DataFrame, x: str, y: str, controls: list[str]) -> dict:
    d = df.dropna(subset=[x, y] + controls)
    Z = np.column_stack([np.ones(len(d))] + [rankdata(d[c]) for c in controls])
    res = lambda v: rankdata(v) - Z @ np.linalg.lstsq(Z, rankdata(v), rcond=None)[0]  # noqa: E731
    r, p = pearsonr(res(d[x]), res(d[y]))
    return {"rho": float(r), "p": float(p), "n": len(d)}


def composting_curve(hist: dict, t_max: int = 8) -> dict:
    """For conditions first observed unassessed: among those still unassessed after
    t reviews (and observed beyond t), the share assessed later. `threshold_t` is the
    first t at which that share falls below half its t = 0 value."""
    import math
    rows = []
    for (_arr, _ct, _k), h in hist.items():
        if h[0][1] in ASSESSED:
            continue
        t0 = h[0][0]
        ta = next((r - t0 for r, s in h if s in ASSESSED), math.inf)
        rows.append((ta, h[-1][0] - t0))
    curve = []
    for t in range(t_max + 1):
        risk = [ta for ta, last in rows if ta > t and last > t]
        curve.append({"t": t, "n": len(risk), "share": sum(ta < math.inf for ta in risk) / len(risk) if risk else float("nan")})
    base = curve[0]["share"]
    return {"curve": curve, "threshold_t": next((c["t"] for c in curve if c["share"] < base / 2), None)}

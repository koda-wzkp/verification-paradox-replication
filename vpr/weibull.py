"""Interval-censored Weibull for durations observed only at reviews.

A condition seen in a status at review a and in a different status at review b
left that status somewhere in (b_prev, b], not exactly at b. Treating b as the
exact time (right-censored likelihood) biases the shape k upward on data like
MONA's; see tests/test_weibull_synthetic.py.
"""

from __future__ import annotations

import math
from collections import defaultdict

import numpy as np
from scipy.optimize import minimize


def ic_mle(lower, upper, observed) -> tuple[float, float]:
    """Return (k, lambda). Events contribute log[S(lower) - S(upper)]; censored, log S(upper)."""
    lo, up, ev = np.asarray(lower, float), np.asarray(upper, float), np.asarray(observed, bool)
    if up.size == 0 or not ev.any():
        return float("nan"), float("nan")

    def nll(p):
        if not (-10 < p[0] < 10 and -20 < p[1] < 20):  # keep exp() finite
            return 1e300
        k, lam = math.exp(p[0]), math.exp(p[1])
        s_lo, s_up = np.exp(-((lo / lam) ** k)), np.exp(-((up / lam) ** k))
        ll = np.where(ev, np.log(np.maximum(s_lo - s_up, 1e-300)), -((up / lam) ** k))
        return -float(ll.sum())

    res = minimize(nll, [0.0, math.log(max(up.mean(), 1e-6))], method="Nelder-Mead",
                   options={"xatol": 1e-6, "fatol": 1e-8, "maxiter": 4000})
    return math.exp(res.x[0]), math.exp(res.x[1])


def rc_mle(upper, observed) -> tuple[float, float]:
    """Right-censored Weibull treating `upper` as the exact event time (the biased method)."""
    t, ev = np.asarray(upper, float), np.asarray(observed, bool)

    def nll(p):
        if not (-10 < p[0] < 10 and -20 < p[1] < 20):
            return 1e300
        k, lam = math.exp(p[0]), math.exp(p[1])
        z = (t / lam) ** k
        return -float((ev * (np.log(k / lam) + (k - 1) * np.log(t / lam)) - z).sum())

    res = minimize(nll, [0.0, math.log(max(t.mean(), 1e-6))], method="Nelder-Mead",
                   options={"xatol": 1e-6, "fatol": 1e-8, "maxiter": 4000})
    return math.exp(res.x[0]), math.exp(res.x[1])


def spells(hist: dict[tuple, list[tuple[int, str]]], status: str) -> list[dict]:
    """First spell in `status` per condition, as (lower, upper, observed) in reviews."""
    out = []
    for (arr, _ct, _k), h in hist.items():
        st = next((i for i, (_r, s) in enumerate(h) if s == status), None)
        if st is None or st == len(h) - 1:
            continue
        t0 = h[st][0]
        j = next((j for j in range(st + 1, len(h)) if h[j][1] != status), None)
        if j is not None:
            up = max(h[j][0] - t0, 1)
            lo = h[j - 1][0] - t0
            if lo >= up:
                lo = max(0, up - 1)
            obs = True
        else:
            up = max(h[-1][0] - t0, 1)
            lo, obs = up, False
        out.append({"arr": arr, "lower": max(lo, 0), "upper": up, "observed": obs})
    return out


def fit(rows: list[dict], method: str = "ic", n_boot: int = 300, seed: int = 20260925) -> dict:
    """Point estimate plus a 95% interval from a bootstrap over arrangements."""
    lo = np.array([r["lower"] for r in rows], float)
    up = np.array([r["upper"] for r in rows], float)
    ev = np.array([r["observed"] for r in rows], bool)
    est = (lambda i: ic_mle(lo[i], up[i], ev[i])) if method == "ic" else (lambda i: rc_mle(up[i], ev[i]))
    k, lam = est(np.arange(len(rows)))
    by_arr: dict[int, list[int]] = defaultdict(list)
    for i, r in enumerate(rows):
        by_arr[r["arr"]].append(i)
    arrs, rng, ks = list(by_arr), np.random.default_rng(seed), []
    for _ in range(n_boot):
        idx = np.concatenate([by_arr[arrs[p]] for p in rng.integers(0, len(arrs), len(arrs))])
        kb = est(idx)[0]
        if not math.isnan(kb):
            ks.append(kb)
    ci = np.percentile(ks, [2.5, 97.5]) if ks else [float("nan")] * 2
    return {"k": k, "lambda": lam, "ci95": [float(ci[0]), float(ci[1])],
            "n": len(rows), "events": int(ev.sum()), "arrangements": len(arrs)}

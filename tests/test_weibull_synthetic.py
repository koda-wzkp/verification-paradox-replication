"""The estimator must recover a known shape from data observed only at reviews.

Synthetic durations are drawn from a Weibull with known k, observed at integer
reviews with each review skipped with probability 0.2, and right-censored at a
random program end. The interval-censored estimator should recover k; the
right-censored one is expected to overstate it.
"""

import numpy as np
import pytest

from vpr.weibull import ic_mle, rc_mle


def synthetic(k, n=3000, lam=3.0, seed=0):
    rng = np.random.default_rng(seed)
    t = lam * rng.weibull(k, n)
    end = rng.integers(3, 15, n)
    lo, up, ev = [], [], []
    for ti, e in zip(t, end):
        reviews = [r for r in range(1, e + 1) if rng.random() > 0.2] or [e]
        after = [r for r in reviews if r >= ti]
        if after:
            u = after[0]
            before = [r for r in reviews if r < u]
            lo.append(before[-1] if before else 0); up.append(u); ev.append(True)
        else:
            lo.append(reviews[-1]); up.append(reviews[-1]); ev.append(False)
    return np.array(lo, float), np.array(up, float), np.array(ev)


@pytest.mark.parametrize("k", [0.4, 0.9, 1.3])
def test_interval_censored_recovers_k(k):
    lo, up, ev = synthetic(k)
    k_hat, _ = ic_mle(lo, up, ev)
    assert abs(k_hat - k) < 0.1, f"true k={k}, estimated {k_hat:.3f}"


def test_right_censored_overstates_k():
    lo, up, ev = synthetic(0.4)
    k_rc, _ = rc_mle(up, ev)
    assert k_rc > 0.4 + 0.15, f"expected upward bias, got {k_rc:.3f}"

"""Reproduce every figure in the correction notice to The Verification Paradox.

    python reproduce.py                     # downloads Combined.xlsx if missing
    python reproduce.py --data path.xlsx    # use a local copy
    python reproduce.py --combined later    # sensitivity: read R2R3-style codes as the later review

Writes results.json and prints a summary.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from vpr import mona, paradox, weibull


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("data/Combined.xlsx"))
    ap.add_argument("--combined", choices=["zero", "later", "drop"], default="zero")
    ap.add_argument("--boot-k", type=int, default=300)
    ap.add_argument("--boot-rho", type=int, default=2000)
    a = ap.parse_args()

    path = mona.download(a.data)
    digest = mona.sha256(path)
    same = digest == mona.REFERENCE_SHA256
    print(f"Combined.xlsx sha256 {digest[:12]}… {'matches' if same else 'DIFFERS from'} the notice's snapshot")

    rows = mona.load_rows(path, a.combined)
    hist = mona.histories(rows)
    years = mona.approval_years(rows)
    never = np.mean([not any(s in mona.ASSESSED for _r, s in h) for h in hist.values()])
    counts = {"rows": int(len(rows)), "conditions": len(hist), "arrangements": int(rows.arr.nunique()),
              "approval_years": [int(rows.year.min()), int(rows.year.max())],
              "share_never_assessed": round(float(never), 3)}
    print("\nCounts:", counts)

    print("\nWeibull shape by status (interval-censored vs right-censored):")
    shapes = {}
    for s in ["Declared", "Met", "Met with delay", "Not met"]:
        sp = weibull.spells(hist, s)
        ic, rc = weibull.fit(sp, "ic", a.boot_k), weibull.fit(sp, "rc", a.boot_k)
        shapes[s] = {"interval_censored": ic, "right_censored": rc}
        print(f"  {s:15s} n={ic['n']:5d} events={ic['events']:5d}  "
              f"k={ic['k']:.2f} [{ic['ci95'][0]:.2f}, {ic['ci95'][1]:.2f}]   old method k={rc['k']:.2f}")

    p = paradox.program_table(hist, years)
    p["log_n"] = np.log(p.n)
    B = a.boot_rho
    tests = {
        "main": paradox.rho_ci(p, "verification", "health", B),
        "health_incl_delay": paradox.rho_ci(p, "verification", "health_incl_delay", B),
        "frequency_not_breadth": paradox.rho_ci(p, "verification_freq", "health", B),
        "programs_10plus": paradox.rho_ci(p[p.n >= 10], "verification", "health", B),
        "partial_size_year": paradox.partial_rho(p, "verification", "health", ["log_n", "year"]),
        "approved_pre_2009": paradox.rho_ci(p[p.year < 2009], "verification", "health", B),
        "approved_2010_on": paradox.rho_ci(p[p.year >= 2010], "verification", "health", B),
    }
    p["tercile"] = __import__("pandas").qcut(p.baseline, 3, labels=["severe", "moderate", "mild"], duplicates="drop")
    for t in ["severe", "moderate", "mild"]:
        tests[f"baseline_{t}"] = paradox.rho_ci(p[p.tercile == t], "verification", "health", B)
    print("\nVerification paradox (Spearman rho, 95% bootstrap CI):")
    for k, v in tests.items():
        ci = f"[{v['ci95'][0]:+.2f}, {v['ci95'][1]:+.2f}]" if "ci95" in v else f"p={v['p']:.4f}"
        print(f"  {k:24s} n={v['n']:3d}  rho={v['rho']:+.3f}  {ci}")

    out = {"sha256": digest, "matches_reference": same, "combined_codes": a.combined,
           "counts": counts, "weibull": shapes, "paradox": tests}
    Path("results.json").write_text(json.dumps(out, indent=1))
    print("\nWrote results.json")


if __name__ == "__main__":
    main()

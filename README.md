# Verification Paradox: replication and correction

Reproduces every figure in the correction notice to *The Verification Paradox* (SSRN 6444080), from the IMF's public MONA database, with one command.

**The finding that stands:** IMF programs that assess a larger share of their structural conditions report a lower share met (Spearman ρ = −0.28, 95% CI −0.39 to −0.16, 335 programs). This is an association; the data cannot tell whether checking reveals problems or troubled programs get checked more.

**What was corrected:** the original analysis used a derived file that repeated each condition 1–13 times, and fitted Weibull shapes with an estimator that overstates k when status is only seen at reviews. The status-specific shapes are withdrawn.

## Run it

```bash
pip install -r requirements.txt
python reproduce.py            # downloads Combined.xlsx from the IMF, writes results.json
python -m pytest tests         # estimator recovery and unit-of-analysis checks
```

`reproduce.py` prints the MONA file's SHA-256 and says whether it matches the snapshot used for the notice (`305b7370…0bb2`). The IMF updates MONA; on a newer snapshot the numbers will move.

Sensitivity: `python reproduce.py --combined later` reads combined review codes such as `R2R3` as the later review instead of review 0.

## What the code does

| File | Purpose |
| --- | --- |
| `vpr/mona.py` | Download MONA, decode statuses, build one history per condition |
| `vpr/weibull.py` | Interval-censored Weibull (and the biased right-censored version, for comparison) |
| `vpr/paradox.py` | Per-program verification breadth and health; Spearman ρ with bootstrap intervals |
| `tests/test_weibull_synthetic.py` | The estimator must recover known shapes from review-sampled synthetic data |
| `tests/test_units.py` | One history per condition; status and review-code decoding |

**Unit of analysis.** A condition is keyed by arrangement, condition type, and normalized description. Its rows across reviews form one history, with one row per review: an assessment first, then any other status, then a superseded "Modified date" row (MONA keeps the old deadline beside the live one when a deadline is renegotiated). `--all-rows` keeps every row, the first-draft reading.

**Verification** is the share of a program's conditions ever assessed (Met, Met with delay, Partially met, or Not met). **Health** is the share whose last assessment is Met.

**Status mapping.** Codes that reclassify a condition's type (`MOD-SB`, `WMOD-*`, …) are treated as not yet assessed. Modified date, Waived and Cancelled are their own statuses, not assessments.

## Known limitations

- Combined review codes (about 5,500 rows) are read as review 0 by default.
- Assessed statuses are poorly described by a single Weibull shape: most conditions change at the next review or practically never. A two-population model is the planned replacement.
- Causal direction is open.

## Contributing

Issues and pull requests are welcome, especially: a two-population survival model for assessed statuses; a frailty test for the Declared hazard; replication on other conditionality datasets (World Bank, Global Fund).

# Research guardrails

Adopted 2026-10-31, after the correction to *The Verification Paradox*. Every error that correction fixed was mechanical (duplicated rows, a biased estimator, rows tied at the same review) and survived months of reading because nothing checked it automatically. Work done with LLM assistance adds a second risk: a model extends and unifies a framework faster than the evidence supports it. These rules exist to catch both.

## 1. The code is the referee

- **No number enters a paper, notice or product unless a script in a public repository prints it.** Prose cites the script's output, not a remembered value.
- **Assert the unit of analysis** before computing anything (here: one history per condition, one row per condition-review).
- **Pin the data:** record the SHA-256 of every input file; scripts stop on mismatch.
- **Sanity checks travel with every change:** a re-reading of the data must leave invariant quantities invariant (here: the share of conditions never assessed, each condition's last assessment).

## 2. Validate every estimator on known answers

Before an estimator touches real data, it must recover known parameters from simulated data shaped like the real data (sampling, censoring, gaps). The test lives in `tests/` and runs in CI.

## 3. Pre-register

State the question, data, estimator, held-out cell and decision rule, and commit it, before computing the answer. Record what was already seen. A result that misses its rule is reported as missing; a departure is a written ruling, labelled as such.

## 4. The boring explanation first

For every result, write down the strongest mundane explanation and the test that would rule it out, before interpreting it. Examples from this project: survivor selection (frailty) for falling hazards; duplicated rows for inflated counts; estimator bias for shape parameters; changing denominators for population-curve rates; reverse causation for correlations.

## 5. Vocabulary is a warning sign

Words such as *proves*, *ironclad*, *universal*, *inevitable*, *quantum*, *law* appeared exactly where evidence was thinnest. `scripts/flag_claims.py` lists them in a draft; each hit needs a citation to a script's output or a rewrite.

## 6. Separate the builder from the checker

A model reviewing its own work is a weak check. Before publishing, give a fresh session, preferably a different model, only the claims, code and data, and ask it to break them. Treat its output as leads to test, not verdicts.

## 7. Read the field before claiming novelty

Search for prior work on the same data and question first. For IMF conditionality: the IMF Independent Evaluation Office evaluations of structural conditionality (2008, update 2018) and the compliance literature (for example Dreher, 2004).

## 8. One credentialed human reader per paper

Someone with training in the relevant method (here: survival analysis or applied econometrics) reads it before it goes public. No LLM substitutes for this.

## 9. Cooling-off period

Nothing goes public within a week of being written, or before the outside reader has had it.

"""List overclaiming vocabulary in a draft (RESEARCH-GUARDRAILS.md, rule 5).

    python scripts/flag_claims.py draft.md [more files...]

Prints each hit with its line, and exits 1 if any are found, so it can gate a
commit or CI step. A hit is not an error by itself: it needs either a citation
to a script's output or a rewrite.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

WORDS = [
    r"prove[sd]?", r"proof", r"ironclad", r"definitive(ly)?", r"undeniabl[ey]", r"irrefutabl[ey]",
    r"universal(ly)?", r"inevitabl[ey]", r"law of", r"fundamental law", r"always", r"never fails",
    r"quantum", r"entangle(d|ment)", r"coheren(t|ce)", r"thermodynamic", r"phase (change|transition)",
    r"confirm(s|ed)? that", r"establish(es|ed) that", r"demonstrat(es|ed) that", r"cause[sd]?",
    r"revolutionar(y|ize)", r"paradigm", r"unprecedented",
]
PATTERN = re.compile(r"\b(" + "|".join(WORDS) + r")\b", re.IGNORECASE)


def main(paths: list[str]) -> int:
    hits = 0
    for p in paths:
        for i, line in enumerate(Path(p).read_text(encoding="utf-8").splitlines(), 1):
            for m in PATTERN.finditer(line):
                hits += 1
                print(f"{p}:{i}: '{m.group(0)}'  {line.strip()[:120]}")
    print(f"{hits} flag(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1:]))

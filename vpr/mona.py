"""Load IMF MONA structural conditions and build one history per condition.

The unit of analysis is the condition, not the row. Each row of Combined.xlsx is
one condition at one review; a condition is keyed by (arrangement, condition
type, normalized description) and its rows are joined into a history.
"""

from __future__ import annotations

import hashlib
import re
import urllib.request
from collections import defaultdict
from pathlib import Path

import pandas as pd

COMBINED_URL = "https://www.imf.org/external/np/pdr/mona/ArrangementsData/Combined.xlsx"

# SHA-256 of the Combined.xlsx snapshot used for the correction notice.
# The IMF updates the file; a different hash means different data, not an error.
REFERENCE_SHA256 = "305b7370a181e3ecd41b14208ab1559ddd191a5a7b0bd02354a59834c9990bb2"

# PC Status codes. Codes that reclassify a condition's type (MOD-SB etc.) or
# waive-and-reclassify (WMOD-*) are treated as not yet assessed.
STATUS = {
    "M": "Met", "AC": "Met", "NM": "Not met", "MD": "Met with delay",
    "PM": "Partially met", "MOD-DATE": "Modified date", "MOD-CRIT": "Modified criteria",
    "W": "Waived", "CAN": "Cancelled", "WC": "Cancelled",
}
CONDITION_TYPES = {"SB", "SPC", "PC", "PA"}  # a type code in PC Status = not yet assessed
ASSESSED = {"Met", "Met with delay", "Partially met", "Not met"}


def download(dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        urllib.request.urlretrieve(COMBINED_URL, dest)
    return dest


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode_status(raw) -> str:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return "Declared"
    s = str(raw).strip()
    if not s or s.upper() in CONDITION_TYPES or s.startswith(("MOD-SB", "MOD-SPC", "MOD-PA", "WMOD")):
        return "Declared"
    return STATUS.get(s, s)


def review_number(raw, combined: str = "zero") -> int | None:
    """R0 -> 0, R3 -> 3. Combined codes such as R2R3 are ambiguous.

    combined="zero" reads them as review 0 (the reading used for the correction
    notice); "later" takes the later review; "drop" returns None.
    """
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return 0
    s = str(raw).strip().upper()
    if re.fullmatch(r"R\d+", s):
        return int(s[1:])
    nums = re.findall(r"R(\d+)", s)
    if len(nums) > 1:
        return {"zero": 0, "later": max(map(int, nums)), "drop": None}[combined]
    return 0


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", re.sub(r"\s+", " ", text.lower())).strip()


def load_rows(path: Path, combined: str = "zero") -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="MonaData")
    out = pd.DataFrame({
        "arr": pd.to_numeric(df["Arrangement Number"], errors="coerce"),
        "ctype": df["Key Code"].fillna("SB").astype(str).str.strip(),
        "desc": df["Description"],
        "review": df["Review Type"].map(lambda r: review_number(r, combined)),
        "status": df["PC Status"].map(decode_status),
        "year": pd.to_numeric(df["Approval Year"], errors="coerce"),
    })
    out = out[out.arr.notna() & out.desc.notna() & (out.desc.astype(str).str.strip() != "")]
    out = out[out.review.notna()]
    out["arr"] = out.arr.astype(int)
    out["key"] = out.desc.astype(str).map(normalize)
    return out


def histories(rows: pd.DataFrame) -> dict[tuple, list[tuple[int, str]]]:
    """{(arr, ctype, normalized description): [(review, status), ...] sorted by review}."""
    h: dict[tuple, list] = defaultdict(list)
    for arr, ct, key, rv, st in rows[["arr", "ctype", "key", "review", "status"]].itertuples(index=False):
        h[(arr, ct, key)].append((int(rv), st))
    for k in h:
        h[k].sort(key=lambda x: x[0])
    return dict(h)


def approval_years(rows: pd.DataFrame) -> dict[int, int]:
    y = rows.dropna(subset=["year"]).groupby("arr").year.first()
    return y.astype(int).to_dict()

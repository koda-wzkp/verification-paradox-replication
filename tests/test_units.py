"""The unit of analysis is the condition. These checks guard against the
duplication that affected the original paper: one history per condition, no
repeated (condition, review) rows."""

from pathlib import Path

import pandas as pd
import pytest

from vpr import mona

DATA = Path(__file__).resolve().parent.parent / "data" / "Combined.xlsx"
needs_data = pytest.mark.skipif(not DATA.exists(), reason="run reproduce.py first to download Combined.xlsx")


def test_status_decoding():
    assert mona.decode_status("M") == "Met"
    assert mona.decode_status("NM") == "Not met"
    assert mona.decode_status("SB") == "Declared"
    assert mona.decode_status("MOD-PASB") == "Declared"
    assert mona.decode_status("MOD-DATE") == "Modified date"
    assert mona.decode_status(None) == "Declared"


def test_review_codes():
    assert mona.review_number("R3") == 3
    assert mona.review_number("R2R3") == 0
    assert mona.review_number("R2R3", "later") == 3
    assert mona.review_number("R2R3", "drop") is None


@needs_data
def test_one_history_per_condition():
    rows = mona.load_rows(DATA)
    hist = mona.histories(rows)
    assert len(hist) == rows.groupby(["arr", "ctype", "key"]).ngroups
    assert len(hist) < len(rows), "histories must collapse repeated reviews of a condition"


@needs_data
def test_reference_snapshot_counts():
    if mona.sha256(DATA) != mona.REFERENCE_SHA256:
        pytest.skip("different MONA snapshot; reference counts do not apply")
    rows = mona.load_rows(DATA)
    assert len(mona.histories(rows)) == 11_860
    assert rows.arr.nunique() == 339


@needs_data
def test_collapse_leaves_one_row_per_review():
    rows = mona.load_rows(DATA)
    hist = mona.histories(rows, collapse=True)
    assert all(len(h) == len({r for r, _ in h}) for h in hist.values())
    assert len(hist) == len(mona.histories(rows))


def test_collapse_keeps_live_row():
    import pandas as pd
    rows = pd.DataFrame({
        "arr": [1, 1], "ctype": ["SB", "SB"], "key": ["k", "k"], "review": [2, 2],
        "status": ["Modified date", "Met"],
        "test_date": pd.to_datetime(["2007-03-31", "2007-09-30"]), "year": [2006, 2006], "desc": ["d", "d"]})
    out = mona.collapse_reviews(rows)
    assert list(out.status) == ["Met"] and bool(out.renegotiated.iloc[0])

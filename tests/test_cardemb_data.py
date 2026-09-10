"""Phase 1a unit gate (v7 plan §2): every ladder card round-trips through the
printed channel; number bucketing and the split are deterministic.

Needs rl/artifacts/cards_v1 (committed) — skipped if it is absent.
"""
import os
import sys

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO, "rl", "cardemb"))
sys.path.insert(0, os.path.join(REPO, "rl", "cards"))

import data as D                                    # noqa: E402
from build_index import deck_files, parse_deck     # noqa: E402
from cardguru.dataset import norm_name              # noqa: E402

pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(D.CARDS_V1, "fields.jsonl.gz")),
    reason="rl/artifacts/cards_v1 not built")


@pytest.fixture(scope="module")
def cards():
    return D.load_cards()


def test_bucket_number():
    assert D.bucket_number(0) == "[N0]"
    assert D.bucket_number(8) == "[N8]"
    assert D.bucket_number(9) == "[N9_10]"
    assert D.bucket_number(10) == "[N9_10]"
    assert D.bucket_number(15) == "[N11_15]"
    assert D.bucket_number(20) == "[N16_20]"
    assert D.bucket_number(9999) == "[N21P]"


def test_text_channel_has_no_raw_numbers_or_self_name(cards):
    recs, names = cards
    import re
    for r in recs[:5000]:
        assert not re.search(r"(?<![\[\w])\d+(?![\]\w])", r.text), (r.name, r.text)
        if r.kind == "card" and len(r.name) >= 4:
            body = r.text.split(" . ", 1)[1] if " . " in r.text else ""
            assert not re.search(r"(?<!\w)" + re.escape(r.name) + r"(?!\w)", body), (r.name, body)
    k = recs[names["kaito, bane of nightmares"]]
    assert "CARDNAME" in k.text and "Kaito" not in k.text.split(" . ", 1)[1]
    assert "[M1][MU][MB]" in k.text and "[LOYP1]" in k.text and "[LOYM2]" in k.text


def test_ladder_cards_round_trip_printed(cards):
    recs, names = cards
    seen = 0
    for path in deck_files():
        for name in parse_deck(path):
            cid = names[norm_name(name)]
            f = recs[cid].fields
            assert D.printed_decode(D.printed_encode(f)) == D.printed_expected(f), name
            seen += 1
    assert seen > 300           # distinct deck lines, not card copies


def test_all_faces_round_trip_printed(cards):
    recs, _ = cards
    bad = [r.name for r in recs if D.printed_decode(r.printed) != D.printed_expected(r.fields)]
    assert not bad, bad[:10]


def test_split_is_deterministic_and_about_ten_percent(cards):
    recs, _ = cards
    held = {r.id for r in recs if D.is_heldout(r)}
    held2 = {r.id for r in recs if D.is_heldout(r)}
    assert held == held2
    frac = len(held) / len(recs)
    assert 0.09 < frac < 0.11, frac
    by_file = {}
    for r in recs:
        by_file.setdefault(r.file, set()).add(r.id in held)
    assert all(len(v) == 1 for v in by_file.values()), "faces of one script straddle the split"

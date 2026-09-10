"""Meta Lab meta-deck mode: snapshot loading, ranking, and greedy selection.

The fixture is a real MetaSurf export (2025-05-01..2025-06-09 Modern, two
archetypes with their centroid-representative decklists and the matching slice
of the play-rate prior) — not a hand-written toy. The engine-dependent tests
skip when the Forge dataset is absent, matching the rest of this suite.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru.metagame import (  # noqa: E402
    analyze_meta,
    greedy_sideboard,
    load_snapshot,
    rank_answers,
)

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "meta-modern-sample.json")
DATASET = os.environ.get("CARDGURU_DATASET", "data/dataset.jsonl.gz")


def test_loads_real_snapshot():
    snap = load_snapshot(FIXTURE)
    assert snap["format"] == "modern"
    assert len(snap["archetypes"]) == 2
    assert snap["play_rates"]
    for entry in snap["archetypes"]:
        assert entry["representative"]["mainboard"]
        assert 0.0 < entry["meta_share"] < 1.0


def test_rejects_non_snapshot(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"nope": 1}), encoding="utf-8")
    with pytest.raises(ValueError, match="not a metagame snapshot"):
        load_snapshot(str(bad))


def test_rejects_snapshot_with_empty_decklist(tmp_path):
    snap = json.load(open(FIXTURE, encoding="utf-8"))
    snap["archetypes"][0]["representative"]["mainboard"] = []
    path = tmp_path / "empty.json"
    path.write_text(json.dumps(snap), encoding="utf-8")
    with pytest.raises(ValueError, match="empty mainboard"):
        load_snapshot(str(path))


def _analysis(colors=None, played_only=True):
    from cardguru.answers import load_token_scripts
    from cardguru.index import SearchIndex

    idx = SearchIndex.load(DATASET)
    by_name = {}
    for r in idx.records:
        by_name.setdefault(r.get("name"), r)
    return analyze_meta(
        idx,
        by_name,
        load_snapshot(FIXTURE),
        colors,
        token_scripts=load_token_scripts(),
        played_only=played_only,
    )


needs_dataset = pytest.mark.skipif(
    not os.path.exists(DATASET), reason="Forge dataset not built"
)


@needs_dataset
def test_played_only_requires_the_prior(tmp_path):
    """Ranking without a play-rate prior is mechanically valid but degenerate;
    the failure must be loud rather than a silently empty ranking."""
    snap = json.load(open(FIXTURE, encoding="utf-8"))
    del snap["play_rates"]
    path = tmp_path / "noprior.json"
    path.write_text(json.dumps(snap), encoding="utf-8")

    from cardguru.index import SearchIndex

    idx = SearchIndex.load(DATASET)
    by_name = {r.get("name"): r for r in idx.records}
    with pytest.raises(ValueError, match="no play_rates"):
        analyze_meta(idx, by_name, load_snapshot(str(path)), None, played_only=True)


@needs_dataset
def test_prior_filters_out_unplayed_cards():
    """The whole point of the prior: mechanically every bounce spell answers a
    creature, so the unfiltered candidate set is much larger and full of cards
    the format does not play."""
    played = _analysis(colors={"W", "U"}, played_only=True)
    everything = _analysis(colors={"W", "U"}, played_only=False)
    assert len(everything["answers"]) > len(played["answers"])
    rates = load_snapshot(FIXTURE)["play_rates"]
    assert all(card in rates for card in played["answers"])


@needs_dataset
def test_ranking_uses_untruncated_answer_sets():
    """Regression: analyze_meta must consume `all_answers`, not the 5-card
    `answers` display list, which is pre-sorted by cheapness and would bias
    every ranking toward one-mana filler."""
    analysis = _analysis(colors={"W", "U"})
    for arch in analysis["archetypes"]:
        for detail in arch["threat_detail"]:
            assert detail["answers"] >= 0
    # Consign to Memory is a real WU answer in this field and is far from the
    # cheapest option for every threat, so it only survives an untruncated scan.
    assert "Consign to Memory" in analysis["answers"]


@needs_dataset
def test_every_answer_carries_a_reason_and_class():
    analysis = _analysis(colors={"W", "U"})
    for rec in analysis["answers"].values():
        assert rec["classes"]
        assert rec["weighted_coverage"] > 0
        for threats in rec["detail"].values():
            for reason in threats.values():
                assert isinstance(reason, str)


@needs_dataset
def test_on_board_filter_drops_stack_only_answers():
    analysis = _analysis(colors={"W", "U"})
    everything = rank_answers(analysis, limit=100)
    on_board = rank_answers(analysis, limit=100, on_board_only=True)
    assert any(r.get("stack_only") for r in everything)
    assert not any(r.get("stack_only") for r in on_board)


@needs_dataset
def test_greedy_coverage_is_monotone_and_bounded():
    analysis = _analysis(colors={"W", "U"})
    picks = greedy_sideboard(analysis, slots=5)
    assert picks
    gains = [p["marginal_gain"] for p in picks]
    assert gains == sorted(gains, reverse=True)  # greedy: non-increasing
    cumulative = [p["cumulative_coverage"] for p in picks]
    assert cumulative == sorted(cumulative)
    assert cumulative[-1] <= 1.0 + 1e-9


@needs_dataset
def test_is_deterministic():
    a, b = _analysis(colors={"W", "U"}), _analysis(colors={"W", "U"})
    assert rank_answers(a, limit=20) == rank_answers(b, limit=20)
    assert greedy_sideboard(a, slots=5) == greedy_sideboard(b, slots=5)

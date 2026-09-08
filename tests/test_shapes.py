"""Param-shape mining: derive what a mode MEANS, don't hand-write it.

Motivating failure chain, all one root cause — the ontology lists 1,206 param
keys and 138 static modes as flat frequency tables, with nothing linking them:

  "creatures that stop opponents casting"     -> wrapped a static in a chain
  "...can't cast at instant speed"            -> guessed a param that does not
                                                 exist (SorcerySpeed), because
                                                 OnlySorcerySpeed is 3 of 139
                                                 CantBeCast nodes

Each was patched by hand in the compiler prompt. This module derives the same
information from the dataset instead, so a new set's mechanics appear on the
next rebuild with nobody editing prose.
"""
import gzip
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru import shapes as sh  # noqa: E402

# One mode carrying three distinct meanings, separated only by params —
# the real CantBeCast situation in miniature.
FACES = (
    [{"name": f"Tax{i}", "nodes": [{"id": "s", "kind": "S", "params": {
        "Mode": "CantBeCast", "Caster": "Opponent", "ValidCard": "Card",
        "Description": "prose"}}], "edges": []} for i in range(12)]
    + [{"name": f"OnePerTurn{i}", "nodes": [{"id": "s", "kind": "S", "params": {
        "Mode": "CantBeCast", "Caster": "Player", "NumLimitEachTurn": "1",
        "ValidCard": "Card"}}], "edges": []} for i in range(5)]
    # The rare, decisive shape: 2 of 24.
    + [{"name": f"Teferi{i}", "nodes": [{"id": "s", "kind": "S", "params": {
        "Mode": "CantBeCast", "Caster": "Opponent", "OnlySorcerySpeed": "True",
        "ValidCard": "Card"}}], "edges": []} for i in range(2)]
    # Symmetric prohibitions carry no Caster at all — which is what keeps
    # Caster below the ubiquity cutoff and therefore discriminating, exactly
    # as in the real data (106 of 139).
    + [{"name": f"Bare{i}", "nodes": [{"id": "s", "kind": "S", "params": {
        "Mode": "CantBeCast", "ValidCard": "Card"}}], "edges": []} for i in range(5)]
)


@pytest.fixture(scope="module")
def mined(tmp_path_factory):
    d = tmp_path_factory.mktemp("shapes")
    path = os.path.join(d, "dataset.jsonl.gz")
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write(json.dumps({"_meta": {"source_pin": "abc123", "format": 1}}) + "\n")
        for rec in FACES:
            f.write(json.dumps(rec) + "\n")
    return sh.mine(path, min_total=4)


def test_splits_one_mode_into_its_meanings(mined):
    info = mined["mode"]["CantBeCast"]
    assert info["total"] == 24
    by_params = {"+".join(s["params"]): s["n"] for s in info["shapes"]}
    assert by_params["Caster"] == 12
    assert by_params["Caster+NumLimitEachTurn"] == 5
    assert by_params["Caster+OnlySorcerySpeed"] == 2
    assert by_params[""] == 5            # symmetric: no Caster


def test_ubiquitous_params_are_dropped(mined):
    """ValidCard is on every node, so it discriminates nothing and would only
    add noise to every shape."""
    for s in mined["mode"]["CantBeCast"]["shapes"]:
        assert "ValidCard" not in s["params"]


def test_prose_params_are_dropped(mined):
    for s in mined["mode"]["CantBeCast"]["shapes"]:
        assert "Description" not in s["params"] and "Mode" not in s["params"]


def test_digest_keeps_the_rare_discriminating_shape(mined):
    """The bug this test exists for: truncating the digest to the most common
    shapes dropped OnlySorcerySpeed (the whole answer) and the compiler
    invented a param name instead."""
    text = sh.digest(mined)
    assert "OnlySorcerySpeed" in text
    assert "NumLimitEachTurn" in text


def test_digest_is_prompt_sized(mined):
    """The full artifact is ~94k tokens and cannot go in a prompt; the digest
    must stay small enough to."""
    assert len(sh.digest(mined)) < 2000


def test_single_shape_facets_are_omitted(mined):
    """A mode with one shape means exactly what its name says — including it
    would spend prompt tokens to say nothing."""
    assert "Continuous" not in mined["mode"]


def test_meta_stamps_the_source_pin(mined):
    """Shapes are only valid for the dataset they were mined from."""
    assert mined["_meta"]["forge_pin"] == "abc123"
    assert mined["_meta"]["faces"] == len(FACES)


def test_load_missing_artifact_returns_none(tmp_path):
    assert sh.load(str(tmp_path / "nope.json")) is None


def test_load_corrupt_artifact_returns_none(tmp_path):
    p = tmp_path / "shapes.json"
    p.write_text("{ not json")
    assert sh.load(str(p)) is None


def test_prompt_degrades_without_the_artifact(monkeypatch):
    """Nothing hard-depends on shapes.json: absent it, the prompt is simply
    the old one."""
    from cardguru import nl_compiler

    monkeypatch.setenv("CARDGURU_SHAPES", "/no/such/shapes.json")
    assert nl_compiler._shape_block() == ""


def test_prompt_includes_shapes_when_present(tmp_path, monkeypatch, mined):
    from cardguru import nl_compiler

    p = tmp_path / "shapes.json"
    p.write_text(json.dumps(mined))
    monkeypatch.setenv("CARDGURU_SHAPES", str(p))
    block = nl_compiler._shape_block()
    assert "CantBeCast:" in block and "OnlySorcerySpeed" in block


# --- card-anchored similarity --------------------------------------------
# "Cards like Reprieve" returned 2,027 bounce spells because nothing in the
# pipeline looked at Reprieve: the compiler kept Destination=Hand and dropped
# Origin=Stack, which is the entire difference between a soft counter and an
# Unsummon. Signatures are derived from the card's own graph instead.

from cardguru import similar as sim  # noqa: E402
from cardguru.index import SearchIndex  # noqa: E402

REPRIEVE = {"name": "Reprieve", "manaCost": "1 W", "types": "Instant", "edges": [],
            "nodes": [{"id": "a0", "kind": "A", "api": "ChangeZone", "params": {
                "ValidTgts": "Card.inZoneStack", "TgtZone": "Stack",
                "Origin": "Stack", "Destination": "Hand"}}]}
UNSUMMON = {"name": "Unsummon", "manaCost": "U", "types": "Instant", "edges": [],
            "nodes": [{"id": "a0", "kind": "A", "api": "ChangeZone", "params": {
                "ValidTgts": "Creature", "Origin": "Battlefield",
                "Destination": "Hand"}}]}
NARSET = {"name": "Narset's Reversal", "manaCost": "1 U", "types": "Instant",
          "edges": [],
          "nodes": [{"id": "a0", "kind": "A", "api": "ChangeZone", "params": {
              "ValidTgts": "Card.inZoneStack", "Origin": "Stack",
              "Destination": "Hand"}}]}

SIM_SHAPES = {"api": {"ChangeZone": {
    "total": 3, "shapes": [], "key_params": ["Origin", "Destination"],
    "values": {"Origin": ["Battlefield", "Stack"],
               "Destination": ["Hand", "Exile"]}}}, "mode": {}}


@pytest.fixture
def sim_index():
    return SearchIndex([REPRIEVE, UNSUMMON, NARSET])


def test_signature_keeps_the_value_discriminating_params():
    sig = sim.signature(REPRIEVE, SIM_SHAPES)
    assert sig["node"]["api"] == "ChangeZone"
    assert sig["node"]["params"] == {"Origin": "Stack", "Destination": "Hand"}


def test_signature_separates_a_soft_counter_from_a_bounce_spell(sim_index):
    """The actual bug: Destination alone conflates them; Origin is decisive."""
    sig = sim.signature(REPRIEVE, SIM_SHAPES)
    names = [h["record"]["name"] for h in sim_index.search(sig)]
    assert "Narset's Reversal" in names
    assert "Unsummon" not in names


def test_bespoke_param_values_are_not_used_as_signature():
    """A one-off selector string would match the source card and nothing
    else, which is a useless 'similar' result."""
    rec = {"name": "X", "edges": [], "nodes": [
        {"id": "a", "kind": "A", "api": "ChangeZone",
         "params": {"Origin": "Stack", "Destination": "SomeNeverSeenZone"}}]}
    sig = sim.signature(rec, SIM_SHAPES)
    assert sig["node"]["params"] == {"Origin": "Stack"}


def test_find_is_case_insensitive(sim_index):
    rec, exact = sim.find(sim_index, "rEpRiEvE")
    assert rec["name"] == "Reprieve" and exact is True


def test_find_corrects_a_near_miss_name(sim_index):
    """The Aven Interrupter/Interruptor bug: an exact-only lookup returned
    nothing, the router fell through to the NL compiler, and the user got a
    confident answer to a different question."""
    rec, exact = sim.find(sim_index, "Repreive")     # transposed letters
    assert rec["name"] == "Reprieve"
    assert exact is False, "must report that it corrected the name"


def test_find_rejects_a_name_that_is_not_close(sim_index):
    """'like a cheap counterspell' is not a typo for a card — it must fall
    through to the compiler rather than being silently 'corrected'."""
    rec, exact = sim.find(sim_index, "a cheap counterspell")
    assert rec is None and exact is False


def test_unknown_card_fails_loudly(sim_index, tmp_path, monkeypatch):
    p = tmp_path / "shapes.json"
    p.write_text(json.dumps(SIM_SHAPES))
    with pytest.raises(SystemExit):
        sim.similar(sim_index, "No Such Card", shapes_path=str(p))


def test_missing_shapes_artifact_fails_loudly(sim_index):
    with pytest.raises(SystemExit):
        sim.similar(sim_index, "Reprieve", shapes_path="/no/such/shapes.json")


def test_source_card_is_excluded(sim_index, tmp_path):
    p = tmp_path / "shapes.json"
    p.write_text(json.dumps(SIM_SHAPES))
    _rec, _q, hits, exact, _opts = sim.similar(sim_index, "Reprieve", shapes_path=str(p))
    assert [h["name"] for h in hits] == ["Narset's Reversal"]
    assert exact is True


def test_signature_ranks_by_selectivity_not_param_count():
    """Spellstutter Sprite bug: the generic "when this enters" trigger carries
    three matching params and sits on 4,471 cards, while the card's identity
    (a param-less api: Counter on 514) carried none. Ranking by param count
    picked the useless one and returned 4,470 matches.

    The index has to be big enough for "broad" to mean something — with a
    handful of cards every spec is equally selective.
    """
    def etb_node():
        return {"id": "etb", "kind": "T", "params": {
            "Mode": "ChangesZone", "Origin": "Any", "Destination": "Battlefield"}}

    # 60 cards share the generic ETB; only 12 of them also counter.
    corpus = [{"name": f"Etb{i}", "edges": [], "nodes": [etb_node()]}
              for i in range(60)]
    counterers = [{"name": f"Counterer{i}", "edges": [],
                   "nodes": [etb_node(), {"id": "eff", "kind": "SVar",
                                          "api": "Counter"}]}
                  for i in range(12)]
    sprite = {"name": "Sprite", "edges": [],
              "nodes": [etb_node(), {"id": "eff", "kind": "SVar",
                                     "api": "Counter"}]}
    idx = SearchIndex([sprite] + corpus + counterers)
    shapes = {"api": {"Counter": {"total": 13, "shapes": [], "values": {}}},
              "mode": {"ChangesZone": {"total": 73, "shapes": [], "values": {
                  "Origin": ["Any"], "Destination": ["Battlefield"]}}}}

    sig = sim.signature(sprite, shapes, index=idx)
    assert "Counter" in json.dumps(sig), \
        "must keep the distinctive node over the ubiquitous ETB trigger"
    matched = [h["record"]["name"] for h in idx.search(sig)]
    assert len(matched) < 20, "signature must not degenerate to the whole corpus"


def test_bookkeeping_nodes_are_never_a_signature():
    shapes = {"api": {"Cleanup": {"total": 9, "shapes": [], "values": {}}}, "mode": {}}
    rec = {"name": "X", "edges": [],
           "nodes": [{"id": "c", "kind": "SVar", "api": "Cleanup"}]}
    assert sim.signature(rec, shapes) is None


def test_abilities_lists_every_option_with_reach(sim_index, tmp_path):
    """A multi-ability card is genuinely ambiguous — Aven Interrupter both
    exiles a spell and taxes opponents — so the options are exposed instead
    of one being chosen silently."""
    opts = sim.abilities(sim_index, REPRIEVE, SIM_SHAPES)
    assert opts and all("reaches" in o and "spec" in o for o in opts)
    assert opts == sorted(opts, key=lambda o: o["reaches"])

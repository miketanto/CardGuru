"""Zero-hit diagnosis: name the clause that killed the query.

The motivating bug: an LLM-compiled query filtered colors with
{"card": {"types": {"contains": "White"}}}. Forge's `types` field is only the
type line ("Instant"), never a color, so that clause matched 0 cards — and
because it sat inside an `all`, the whole query returned 0 while every other
clause was healthy. The result was an empty page with no way to tell why.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru.diagnose import diagnose, render  # noqa: E402
from cardguru.index import SearchIndex  # noqa: E402

# Three faces is enough to make clauses hit and miss deterministically.
RECORDS = [
    {"name": "Counterspell", "types": "Instant", "manaCost": "U U",
     "nodes": [{"id": "a0", "kind": "A", "api": "Counter", "apiKind": "SP"}],
     "edges": []},
    {"name": "Mana Leak", "types": "Instant", "manaCost": "1 U",
     "nodes": [{"id": "a0", "kind": "A", "api": "Counter", "apiKind": "SP"}],
     "edges": []},
    {"name": "Grizzly Bears", "types": "Creature Bear", "manaCost": "1 G",
     "nodes": [], "edges": []},
]


@pytest.fixture(scope="module")
def index():
    return SearchIndex(list(RECORDS))


def _by_label(tree, needle):
    if needle in tree["label"]:
        return tree
    for child in tree.get("children", []):
        found = _by_label(child, needle)
        if found:
            return found
    return None


def test_names_the_single_killer_clause(index):
    """The reported bug, in miniature: a healthy clause AND-ed with a clause
    that matches nothing."""
    query = {"all": [
        {"node": {"api": "Counter"}},                      # 2 cards
        {"card": {"types": {"contains": "Blue"}}},         # 0 — the killer
    ]}
    tree = diagnose(index, query)
    assert tree["hits"] == 0
    assert tree["killers"] == ['card types contains "Blue"']
    assert _by_label(tree, 'api="Counter"')["hits"] == 2


def test_reports_every_killer_not_just_the_first(index):
    query = {"all": [
        {"card": {"types": {"contains": "Blue"}}},
        {"card": {"types": {"contains": "White"}}},
        {"node": {"api": "Counter"}},
    ]}
    assert len(diagnose(index, query)["killers"]) == 2


def test_healthy_clauses_that_simply_never_co_occur(index):
    """No single clause is empty — they just never describe the same card.
    That must NOT be reported as a killer; it's a different diagnosis."""
    query = {"all": [
        {"node": {"api": "Counter"}},                    # the two instants
        {"card": {"types": {"contains": "Creature"}}},   # the bear
    ]}
    tree = diagnose(index, query)
    assert tree["hits"] == 0
    assert tree["killers"] == []
    assert all(c["hits"] > 0 for c in tree["children"])


def test_zero_branch_under_any_is_not_a_killer(index):
    """Inside an `any`, an empty branch is harmless — the others can carry it."""
    query = {"any": [
        {"card": {"types": {"contains": "Blue"}}},   # 0, but irrelevant
        {"node": {"api": "Counter"}},                # 2
    ]}
    tree = diagnose(index, query)
    assert tree["hits"] == 2
    assert tree["killers"] == []


def test_nested_all_inside_any(index):
    query = {"any": [{"all": [
        {"node": {"api": "Counter"}},
        {"card": {"types": {"contains": "Blue"}}},
    ]}]}
    assert diagnose(index, query)["killers"] == ['card types contains "Blue"']


def test_branch_budget_is_bounded(index):
    """Each branch is a full scan, so a huge query must not fan out forever."""
    query = {"all": [{"node": {"api": "Counter"}} for _ in range(50)]}
    tree = diagnose(index, query, limit_branches=5)
    assert len(tree["children"]) <= 5
    assert tree.get("truncated")


def test_malformed_branch_does_not_abort_diagnosis(index):
    """A bad clause should be reported as an error row, not raise."""
    tree = diagnose(index, {"all": [{"node": {"nope": "x"}},
                                    {"node": {"api": "Counter"}}]})
    assert tree["children"][0]["hits"] == -1
    assert tree["children"][1]["hits"] == 2


def test_render_is_aligned_text(index):
    lines = render(diagnose(index, {"all": [
        {"node": {"api": "Counter"}},
        {"card": {"types": {"contains": "Blue"}}},
    ]}))
    assert any("KILLER" in ln for ln in lines)
    assert lines[0].startswith("all")
    assert lines[1].startswith("  ")      # children are indented


def test_labels_are_readable(index):
    """The label is what the user reads; it must describe the clause."""
    tree = diagnose(index, {"chain": {"from": {"kind": "T"},
                                      "to": {"api": "Token"}}})
    assert tree["label"] == "chain kind=\"T\" -> api=\"Token\""


# --- disrupts_spells hook -------------------------------------------------
# Motivating recall gap: "white or blue <=3 mana that counters or disrupts
# opponents' spells" compiled to {"node": {"api": "Counter"}} and missed both
# Aven Interrupter (exiles a spell off the stack + taxes opponents) and
# Aang, Swift Savior (Airbend). "Disruption" is a functional class with no
# single structural signature, so it lives in a detector, not a prompt.

from cardguru.recommend import _detect_disrupts_spells  # noqa: E402


def _rec(*nodes):
    return {"name": "x", "nodes": list(nodes), "edges": []}


def test_detects_classic_counterspell():
    assert _detect_disrupts_spells(_rec({"id": "a0", "kind": "A", "api": "Counter"}))


def test_detects_airbend():
    """Airbend only exists because the Avatar set invented it — the reason
    this is a detector and not a hand-written list in a prompt."""
    assert _detect_disrupts_spells(_rec({"id": "a0", "kind": "SVar", "api": "Airbend"}))


def test_detects_exile_off_the_stack():
    """Aven Interrupter's ETB: exile target spell."""
    assert _detect_disrupts_spells(_rec(
        {"id": "TrigExile", "kind": "SVar", "api": "ChangeZone",
         "params": {"TargetType": "Spell", "Origin": "Stack", "Destination": "Exile"}}))


def test_detects_opponent_facing_cost_tax():
    """Aven Interrupter's static half."""
    assert _detect_disrupts_spells(_rec(
        {"id": "ab1", "kind": "S",
         "params": {"Mode": "RaiseCost", "Activator": "Opponent", "Type": "Spell"}}))


def test_cost_tax_must_target_an_opponent():
    """Plenty of statics raise costs for everyone or for their controller;
    those are not disruption and must not inflate the hook."""
    assert not _detect_disrupts_spells(_rec(
        {"id": "ab0", "kind": "S",
         "params": {"Mode": "RaiseCost", "Activator": "You"}}))


def test_ordinary_zone_change_is_not_disruption():
    """Exiling a creature from the battlefield is removal, not spell
    disruption — the Stack is what makes it disruption."""
    assert not _detect_disrupts_spells(_rec(
        {"id": "a0", "kind": "A", "api": "ChangeZone",
         "params": {"Origin": "Battlefield", "Destination": "Exile"}}))


def test_vanilla_creature_is_not_disruption():
    assert not _detect_disrupts_spells(_rec({"id": "k0", "kind": "K",
                                             "keyword": "Flying"}))


def test_hook_is_registered_and_reachable():
    """It must be in HOOKS (so detect_hooks reports it) and accepted by the
    validator (so a compiled query can actually use it)."""
    from cardguru.recommend import HOOKS
    from cardguru.validate import Ontology, validate

    assert "disrupts_spells" in HOOKS
    onto_path = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "research", "data", "ontology.json")
    if os.path.exists(onto_path):
        assert validate({"hook": "disrupts_spells"}, Ontology.load(onto_path)) == []


def test_compiler_prompt_lists_the_hooks():
    """The prompt tells the model to prefer hooks; that only works if the
    available hook names are actually in the prompt."""
    import json as _json
    from cardguru.nl_compiler import build_system_prompt

    onto_path = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "research", "data", "ontology.json")
    if not os.path.exists(onto_path):
        pytest.skip("ontology not built")
    with open(onto_path, encoding="utf-8") as f:
        prompt = build_system_prompt(_json.load(f))
    assert "disrupts_spells" in prompt
    assert "card_draw" in prompt      # roles listed too

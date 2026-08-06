import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru.forge_parser import _parse_face  # noqa: E402
from cardguru.querydsl import (CardGraph, QueryError, evaluate,  # noqa: E402
                               match_value, required_token_groups)
from tests.test_parser import RAGAVAN  # noqa: E402


@pytest.fixture()
def ragavan():
    return CardGraph(_parse_face(RAGAVAN, "r/ragavan.txt", 0).to_record())


def test_match_value_forms():
    assert match_value("x", "x") and not match_value("x", "y")
    assert match_value({"contains": "layer"}, "Player")
    assert match_value({"icontains": "PLAYER"}, "player stuff")
    assert match_value({"regex": "Sac<[^>]*Creature"}, "Sac<1/Creature>")
    assert match_value({"any": ["a", {"contains": "b"}]}, "zzb")
    assert match_value(True, "anything") and not match_value(True, None)


def test_node_query(ragavan):
    ok, ev = evaluate({"node": {"api": "Token"}}, ragavan)
    assert ok and {"node": "TrigTreasure"} in ev


def test_chain_query(ragavan):
    q = {"chain": {"from": {"kind": "T", "mode": "DamageDone"},
                   "to": {"api": "Token"}}}
    ok, ev = evaluate(q, ragavan)
    assert ok
    assert ev[0]["path"][0] == "ab0" and ev[0]["path"][-1] == "TrigTreasure"


def test_chain_multi_target_same_root(ragavan):
    q = {"chain": {"from": {"kind": "T"},
                   "to": [{"api": "Dig", "params": {"DestinationZone": {"contains": "Exile"}}},
                          {"mode": "Continuous", "params": {"MayPlay": "True"}}]}}
    ok, ev = evaluate(q, ragavan)
    assert ok and len(ev) == 2


def test_chain_respects_via(ragavan):
    q = {"chain": {"from": {"kind": "T"}, "to": {"api": "Dig"},
                   "via": ["Execute"]}}       # Dig is behind SubAbility, not Execute
    ok, _ = evaluate(q, ragavan)
    assert not ok


def test_keyword_and_not(ragavan):
    ok, _ = evaluate({"keyword": "Dash"}, ragavan)
    assert ok
    ok, _ = evaluate({"not": {"keyword": "Flying"}}, ragavan)
    assert ok


def test_card_fields(ragavan):
    ok, _ = evaluate({"card": {"types": {"contains": "Monkey"}}}, ragavan)
    assert ok


def test_bad_queries_raise(ragavan):
    with pytest.raises(QueryError):
        evaluate({"nope": 1}, ragavan)
    with pytest.raises(QueryError):
        evaluate({"node": {"bogus_field": 1}}, ragavan)
    with pytest.raises(QueryError):
        evaluate({"chain": {"from": {"kind": "T"}}}, ragavan)


def test_token_groups_prune_conservatively():
    q = {"all": [{"node": {"api": "Token"}},
                 {"chain": {"from": {"kind": "T", "mode": "DamageDone"},
                            "to": {"api": "Token"}}}]}
    groups = required_token_groups(q)
    assert {"api:Token"} in groups and {"mode:DamageDone"} in groups
    # un-indexable branches must disable pruning, not wrongly prune
    assert required_token_groups({"not": {"node": {"api": "Token"}}}) == []
    assert required_token_groups(
        {"any": [{"node": {"api": "Token"}}, {"card": {"types": "Land"}}]}) == []

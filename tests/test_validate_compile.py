import json
import os
import sys
import types

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru.nl_compiler import (CompileResult, build_system_prompt,  # noqa: E402
                                  compile_question, extract_json)
from cardguru.validate import Ontology, validate  # noqa: E402

ONTO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "research", "data", "ontology.json")

pytestmark = pytest.mark.skipif(
    not os.path.exists(ONTO_PATH), reason="ontology not built")


@pytest.fixture(scope="module")
def onto():
    return Ontology.load(ONTO_PATH)


# ------------------------------------------------------------------ validator

def test_valid_queries_pass(onto):
    for path in os.listdir("queries"):
        with open(os.path.join("queries", path), encoding="utf-8") as f:
            spec = json.load(f)
        assert validate(spec["query"], onto) == [], path
    with open("benchmark/benchmark.json", encoding="utf-8") as f:
        for e in json.load(f):
            assert validate(e["query"], onto) == [], e["id"]


def test_unknown_api_rejected(onto):
    errs = validate({"node": {"api": "SummonDragon"}}, onto)
    assert any("SummonDragon" in e for e in errs)


def test_unknown_mode_and_param_rejected(onto):
    errs = validate({"chain": {"from": {"kind": "T", "mode": "WhenPigsFly"},
                               "to": {"api": "Token", "params": {"Bogus": "1"}}}}, onto)
    assert any("WhenPigsFly" in e for e in errs)
    assert any("Bogus" in e for e in errs)


def test_structural_errors(onto):
    assert validate({"frobnicate": 1}, onto)
    assert validate({"all": []}, onto)
    assert validate({"chain": {"from": {"kind": "T"}}}, onto)
    assert validate({"card": {"cmc": "3"}}, onto)


def test_any_value_pred_checked(onto):
    errs = validate({"node": {"api": {"any": ["Token", "NotAnApi"]}}}, onto)
    assert any("NotAnApi" in e for e in errs)
    assert not any("Token" in e for e in errs)


def test_contains_regex_not_vocab_checked(onto):
    assert validate({"node": {"params": {"Cost": {"regex": "Sac<[^>]*Creature"}}}}, onto) == []


# ------------------------------------------------------------------ compiler

class StubClient:
    """Returns queued response texts in order."""

    def __init__(self, texts):
        self._texts = list(texts)
        self.requests = []
        self.messages = types.SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.requests.append(kwargs)
        text = self._texts.pop(0)
        block = types.SimpleNamespace(type="text", text=text)
        return types.SimpleNamespace(content=[block], stop_reason="end_turn")


def test_extract_json_handles_fences_and_prose():
    assert extract_json('{"node": {"api": "Token"}}') == {"node": {"api": "Token"}}
    assert extract_json('```json\n{"node": {"api": "Token"}}\n```')["node"]["api"] == "Token"
    assert extract_json('Here it is: {"a": {"b": 1}} done')["a"]["b"] == 1


def test_compile_success_first_try():
    good = json.dumps({"node": {"api": "Token"}})
    client = StubClient([good])
    result = compile_question("token makers", ONTO_PATH, client=client, use_cache=False)
    assert result.ok and result.query == {"node": {"api": "Token"}}
    assert len(result.attempts) == 1
    # system prompt embeds the vocabulary and is cached
    sys_blocks = client.requests[0]["system"]
    assert sys_blocks[0]["cache_control"] == {"type": "ephemeral"}
    assert "ChangeZone" in sys_blocks[0]["text"]


def test_compile_retries_on_validation_error():
    bad = json.dumps({"node": {"api": "SummonDragon"}})
    good = json.dumps({"node": {"api": "Token"}})
    client = StubClient([bad, good])
    result = compile_question("token makers", ONTO_PATH, client=client, use_cache=False)
    assert result.ok and len(result.attempts) == 2
    # the retry message carries the validation error back to the model
    retry_user_msg = client.requests[1]["messages"][-1]["content"]
    assert "SummonDragon" in retry_user_msg


def test_compile_gives_up_after_retries():
    bad = json.dumps({"node": {"api": "SummonDragon"}})
    client = StubClient([bad, bad, bad])
    result = compile_question("token makers", ONTO_PATH, client=client, max_retries=2, use_cache=False)
    assert not result.ok and len(result.attempts) == 3
    assert result.errors


def test_system_prompt_builds():
    with open(ONTO_PATH, encoding="utf-8") as f:
        text = build_system_prompt(json.load(f))
    assert "DamageDone" in text and "Respond with ONLY" in text
    assert isinstance(CompileResult(None, [], ["x"]).ok, bool)


# --- semantic facets reachable through the validator ---------------------
# `hook` and `role` were implemented in querydsl but missing from QUERY_OPS,
# so every validated query using them was rejected before it could run.

def test_hook_facet_is_accepted(onto):
    assert validate({"hook": "sac_outlet"}, onto) == []


def test_unknown_hook_is_rejected(onto):
    errors = validate({"hook": "not_a_real_hook"}, onto)
    assert errors and "unknown hook" in errors[0]


def test_role_facet_is_accepted(onto):
    assert validate({"role": "card_draw"}, onto) == []
    assert validate({"role": "card_draw:engine"}, onto) == []


def test_unknown_role_is_rejected(onto):
    errors = validate({"role": "not_a_role"}, onto)
    assert errors and "unknown role" in errors[0]


def test_unknown_role_repeatability_is_rejected(onto):
    errors = validate({"role": "card_draw:sometimes"}, onto)
    assert errors and "unknown repeatability" in errors[0]


def test_facet_args_must_be_strings(onto):
    assert validate({"hook": ["sac_outlet"]}, onto)
    assert validate({"role": {"name": "card_draw"}}, onto)


# --- SVarValue.value -----------------------------------------------------
# The arithmetic operator (double vs +1) lives only in an SVarValue's raw
# value. Without this field, Doubling Season and Hardened Scales are
# indistinguishable and the query has to fall back to an oracle-text regex.

def test_svarvalue_value_field_validates(onto):
    q = {"node": {"kind": "SVarValue", "value": {"contains": "/Twice"}}}
    assert validate(q, onto) == []


def test_unknown_nodespec_field_still_rejected(onto):
    errors = validate({"node": {"kind": "SVarValue", "nope": "x"}}, onto)
    assert errors and "unknown NodeSpec fields" in errors[0]


# --- compile cache -------------------------------------------------------
# The cache is the real cost control at this prompt size: the system prompt is
# ~2.7k tokens and Haiku 4.5 needs a 4096-token prefix before prompt caching
# creates an entry, so a repeated question would otherwise be billed in full.

def test_cache_prevents_second_api_call(tmp_path, monkeypatch):
    import cardguru.nl_compiler as nl

    monkeypatch.setattr(nl, "CACHE_DIR", str(tmp_path / "cache"))
    good = json.dumps({"node": {"api": "Token"}})

    first_client = StubClient([good])
    first = nl.compile_question("token makers", ONTO_PATH, client=first_client)
    assert first.ok and len(first_client.requests) == 1

    # A stub with no responses left: any API call would raise IndexError.
    second_client = StubClient([])
    second = nl.compile_question("token makers", ONTO_PATH, client=second_client)
    assert second.ok
    assert second.query == first.query
    assert second_client.requests == [], "second compile should be served from cache"


def test_cache_key_changes_with_model(tmp_path, monkeypatch):
    """A different model can compile the same question differently, so the
    cache must not serve one model's answer for another."""
    import cardguru.nl_compiler as nl

    monkeypatch.setattr(nl, "CACHE_DIR", str(tmp_path / "cache"))
    system = "irrelevant"
    a = nl._cache_key("token makers", "claude-haiku-4-5", system)
    b = nl._cache_key("token makers", "claude-opus-5", system)
    assert a != b


def test_cache_key_ignores_case_and_whitespace():
    import cardguru.nl_compiler as nl

    assert (nl._cache_key("  Token Makers ", "m", "s")
            == nl._cache_key("token makers", "m", "s"))


def test_corrupt_cache_entry_falls_back_to_api(tmp_path, monkeypatch):
    import cardguru.nl_compiler as nl

    cache = tmp_path / "cache"
    cache.mkdir()
    monkeypatch.setattr(nl, "CACHE_DIR", str(cache))
    key = nl._cache_key("token makers", nl.MODEL, "x")
    (cache / f"{key}.json").write_text("{ not json")
    assert nl._cache_read(key) is None

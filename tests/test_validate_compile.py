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
    result = compile_question("token makers", ONTO_PATH, client=client)
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
    result = compile_question("token makers", ONTO_PATH, client=client)
    assert result.ok and len(result.attempts) == 2
    # the retry message carries the validation error back to the model
    retry_user_msg = client.requests[1]["messages"][-1]["content"]
    assert "SummonDragon" in retry_user_msg


def test_compile_gives_up_after_retries():
    bad = json.dumps({"node": {"api": "SummonDragon"}})
    client = StubClient([bad, bad, bad])
    result = compile_question("token makers", ONTO_PATH, client=client, max_retries=2)
    assert not result.ok and len(result.attempts) == 3
    assert result.errors


def test_system_prompt_builds():
    with open(ONTO_PATH, encoding="utf-8") as f:
        text = build_system_prompt(json.load(f))
    assert "DamageDone" in text and "Respond with ONLY" in text
    assert isinstance(CompileResult(None, [], ["x"]).ok, bool)

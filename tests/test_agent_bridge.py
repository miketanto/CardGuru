"""In-session agents as the model turn.

The property that makes an agent run comparable to an API run is that the loop
is IDENTICAL — same system prompt, same validator gate, same execution
feedback, same message turns — with only the model swapped out. These tests pin
that: the bridge must reuse `compile_question` rather than reimplement it, and
replaying prior turns must reach exactly the state the API run reached.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru.agent_bridge import OutOfAnswers, ReplayClient, RunDir, step  # noqa: E402
from cardguru.index import SearchIndex  # noqa: E402
from cardguru.repair import make_checker  # noqa: E402
from tests.test_repair import RECORDS  # noqa: E402

ONTO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "research", "data", "ontology.json")

ZERO_Q = {"all": [{"node": {"api": "Counter"}},
                  {"card": {"types": {"contains": "Blue"}}}]}
GOOD_Q = {"node": {"api": "Counter"}}


@pytest.fixture(scope="module")
def index():
    return SearchIndex(list(RECORDS))


def test_first_round_asks_for_a_turn_and_carries_the_request():
    res, request = step("counterspells", "q1", [], ONTO_PATH)
    assert res is None
    assert request["messages"] == [{"role": "user", "content": "counterspells"}]
    # the agent must get the real compiler spec, not a summary of it
    assert "ChangeZone" in request["system"][0]["text"]


def test_an_answer_completes_the_compile():
    res, request = step("counterspells", "q1", [json.dumps(GOOD_Q)], ONTO_PATH)
    assert request is None and res.ok and res.query == GOOD_Q


def test_replay_reaches_the_same_state_the_api_run_would(index):
    """Turn 1 returns a zero-hit query. Replaying it must re-run the checker
    and produce the execution feedback as the next request — not skip it."""
    res, request = step("counterspells", "q1", [json.dumps(ZERO_Q)], ONTO_PATH,
                        checker=make_checker(index, "zero"))
    assert res is None
    last = request["messages"][-1]
    assert last["role"] == "user" and "KILLER" in last["content"]
    # the model's own earlier turn is in the transcript, as the API would see it
    assert request["messages"][1]["role"] == "assistant"


def test_two_replayed_turns_finish_the_repair(index):
    res, request = step("counterspells", "q1",
                        [json.dumps(ZERO_Q), json.dumps(GOOD_Q)], ONTO_PATH,
                        checker=make_checker(index, "zero"))
    assert request is None and res.ok and res.query == GOOD_Q
    assert res.checks == ["zero", "ok"] and res.repaired


def test_validation_errors_replay_too():
    """A vocabulary error costs a turn in an agent run exactly as it does
    against the API; hiding it would flatter the agent score."""
    bad = json.dumps({"node": {"api": "SummonDragon"}})
    res, request = step("q", "q1", [bad], ONTO_PATH)
    assert res is None and "SummonDragon" in request["messages"][-1]["content"]


def test_replay_client_raises_rather_than_inventing_a_turn():
    client = ReplayClient([])
    with pytest.raises(OutOfAnswers):
        client.messages.create(model="m", max_tokens=1,
                               system=[{"type": "text", "text": "s"}],
                               messages=[{"role": "user", "content": "hi"}])


def test_retry_budget_is_the_same_as_the_api_path(index):
    """Three zero-hit answers exhaust max_retries=2 and stop, rather than
    letting the agent run get unlimited attempts the API run did not have."""
    res, request = step("q", "q1", [json.dumps(ZERO_Q)] * 3, ONTO_PATH,
                        checker=make_checker(index, "zero"), max_retries=2)
    assert request is None and res.exhausted and len(res.attempts) == 3


# --- run directory --------------------------------------------------------

def test_answers_are_folded_in_and_the_round_is_cleared(tmp_path):
    run = RunDir(str(tmp_path))
    run.write_task("q1", "counterspells",
                   {"system": [{"type": "text", "text": "S"}],
                    "messages": [{"role": "user", "content": "counterspells"}]},
                   turn=1)
    assert run.pending_ids() == ["q1"]
    with open(tmp_path / "answers" / "q1.txt", "w") as f:
        f.write(json.dumps(GOOD_Q))

    state = run.load_state()
    assert run.collect_answers(state) == 1
    assert state == {"q1": [json.dumps(GOOD_Q)]}
    assert run.pending_ids() == []          # the answered task is retired
    run.save_state(state)
    assert run.load_state() == state


def test_answers_are_not_cleaned_up_before_replay(tmp_path):
    """Fenced or chatty output is what a model produces too; `extract_json`
    handles it. Stripping it here would make the agent's job easier than the
    model's and break comparability."""
    run = RunDir(str(tmp_path))
    raw = '```json\n{"node": {"api": "Counter"}}\n```'
    with open(tmp_path / "answers" / "q1.txt", "w") as f:
        f.write(raw)
    state = {}
    run.collect_answers(state)
    assert state["q1"] == [raw]
    res, _ = step("counterspells", "q1", state["q1"], ONTO_PATH)
    assert res.ok and res.query == GOOD_Q


def test_task_file_carries_the_whole_conversation(tmp_path, index):
    run = RunDir(str(tmp_path))
    _res, request = step("counterspells", "q1", [json.dumps(ZERO_Q)], ONTO_PATH,
                         checker=make_checker(index, "zero"))
    run.write_task("q1", "counterspells", request, turn=2)
    text = (tmp_path / "pending" / "q1.md").read_text()
    assert "counterspells" in text          # the original question
    assert "KILLER" in text                 # the execution feedback
    assert "answers/q1.txt" in text         # where to write the answer
    # and it must tell the agent not to peek at the goldens
    assert "goldens" in text

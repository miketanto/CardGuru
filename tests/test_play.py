"""Unit tests for the interactive match client (no JVM required).

The spool protocol and message shapes are exercised with a FAKE driver thread
that mimics what CardGuruScenarioRunner's interactive mode does -- write
request/<n>.json, block for response/<n>.json, finally write result.json --
so the Python match loop and the policies are tested end to end without paying
for maven or the card database. (Same discipline as adjudicate's
validate_scenario tests: the JVM is verified separately by an actual game.)
"""
import json
import os
import tempfile
import threading
import time

from cardguru.play import MatchClient, dumb_policy, pass_policy


# --------------------------------------------------------------- policies

def test_dumb_policy_mulligan_keeps():
    assert dumb_policy({"kind": "mulligan", "hand_count": 7}) == {"mulligan": False}


def test_dumb_policy_priority_takes_first_activate():
    req = {"kind": "priority", "options": [
        {"index": 0, "action": "pass", "text": "pass priority"},
        {"index": 1, "action": "activate", "text": "Play Mountain"},
        {"index": 2, "action": "activate", "text": "Cast Goblin"},
    ]}
    assert dumb_policy(req) == {"choice": 1}


def test_dumb_policy_priority_passes_when_no_play():
    req = {"kind": "priority", "options": [
        {"index": 0, "action": "pass", "text": "pass priority"}]}
    assert dumb_policy(req) == {"choice": 0}


def test_dumb_policy_attacks_with_everything():
    req = {"kind": "attackers", "options": [
        {"index": 0, "name": "Goblin", "power": 1, "toughness": 1},
        {"index": 1, "name": "Ogre", "power": 3, "toughness": 3},
    ]}
    assert dumb_policy(req) == {"attackers": [0, 1]}


def test_dumb_policy_never_blocks():
    req = {"kind": "blockers", "blockers": [{"index": 0, "name": "Bear"}],
           "attackers": [{"index": 0, "name": "Ogre"}]}
    assert dumb_policy(req) == {"blocks": []}


def test_pass_policy_does_nothing():
    assert pass_policy({"kind": "mulligan"}) == {"mulligan": False}
    assert pass_policy({"kind": "priority", "options": []}) == {"choice": 0}
    assert pass_policy({"kind": "attackers", "options": []}) == {"attackers": []}
    assert pass_policy({"kind": "blockers"}) == {"blocks": []}


# --------------------------------------------------------------- the loop

class _FakeProc:
    """Stands in for the maven Popen: stays 'alive' until told to stop."""

    def __init__(self):
        self._alive = True
        self.returncode = 0

    def poll(self):
        return None if self._alive else self.returncode


def _client_on(spool):
    """A MatchClient wired to an existing spool, without launching a JVM."""
    m = MatchClient.__new__(MatchClient)
    m.spool = spool
    m.proc = _FakeProc()
    m.mage_repo = spool
    return m


def _atomic_write(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    os.replace(tmp, path)


def _fake_driver(spool, requests, result, received):
    """Emit each request in order, block for its response, then write result.

    Mirrors the driver's guarantee that request n+1 is never written before the
    response to n exists (the game thread is parked in the callback), which is
    exactly the invariant the client's sequential loop relies on.
    """
    reqdir = os.path.join(spool, "request")
    respdir = os.path.join(spool, "response")
    for seq, req in enumerate(requests, 1):
        _atomic_write(os.path.join(reqdir, f"{seq}.json"), req)
        resp_path = os.path.join(respdir, f"{seq}.json")
        deadline = time.time() + 5
        while not os.path.exists(resp_path):
            if time.time() > deadline:
                raise AssertionError(f"fake driver: no response for {seq}")
            time.sleep(0.005)
        with open(resp_path, encoding="utf-8") as f:
            received.append(json.load(f))
    _atomic_write(os.path.join(spool, "result.json"), result)


def test_match_loop_serves_decisions_in_order_and_returns_result():
    with tempfile.TemporaryDirectory(prefix="cg-play-test-") as spool:
        os.makedirs(os.path.join(spool, "request"))
        os.makedirs(os.path.join(spool, "response"))
        requests = [
            {"kind": "mulligan", "seq": 1, "hand_count": 7},
            {"kind": "priority", "seq": 2, "options": [
                {"index": 0, "action": "pass", "text": "pass priority"},
                {"index": 1, "action": "activate", "text": "Play Mountain"}]},
            {"kind": "attackers", "seq": 3, "options": [
                {"index": 0, "name": "Goblin", "power": 1, "toughness": 1}]},
        ]
        result = {"status": "completed", "winner": "A", "turns": 6}
        received = []
        driver = threading.Thread(target=_fake_driver,
                                  args=(spool, requests, result, received))
        driver.start()
        try:
            out = _client_on(spool).play(dumb_policy, decision_timeout=5)
        finally:
            driver.join(timeout=5)

        assert out == result
        # The policy's answers reached the driver, in order.
        assert received == [
            {"mulligan": False},
            {"choice": 1},
            {"attackers": [0]},
        ]


def test_match_loop_returns_when_result_appears_with_no_requests():
    """A game that ends immediately (e.g. error) still returns a result."""
    with tempfile.TemporaryDirectory(prefix="cg-play-test-") as spool:
        os.makedirs(os.path.join(spool, "request"))
        os.makedirs(os.path.join(spool, "response"))
        result = {"status": "error", "error": "boom", "turns": 0}
        _atomic_write(os.path.join(spool, "result.json"), result)
        out = _client_on(spool).play(dumb_policy, decision_timeout=5)
        assert out == result


def test_match_loop_raises_if_driver_dies_without_result():
    with tempfile.TemporaryDirectory(prefix="cg-play-test-") as spool:
        os.makedirs(os.path.join(spool, "request"))
        os.makedirs(os.path.join(spool, "response"))
        m = _client_on(spool)
        m.proc._alive = False  # simulate a crashed JVM, no result.json
        try:
            m.play(dumb_policy, decision_timeout=5)
            assert False, "expected RuntimeError"
        except RuntimeError as e:
            assert "died mid-match" in str(e)

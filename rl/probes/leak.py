"""Phase 0d (v7 plan §2): the leak gate, generalised from rl/oracle_gate.py
levels 1-3 to ANY hidden channel.

The oracle gate asks one question about one channel ("oe"): can the
policy see what only the critic may see?  v7 adds channels that are
hidden information by construction — the opponent's true hand behind
the knowledge tracker (design §8), the belief module's labels (§8a),
the value trunk's privileged rows (4e).  Every one of them needs the
same three assertions, so this module takes the channel as a parameter:

  LEVEL 1 - the wire.   The policy-path parse of a message is identical
            with and without the hidden keys.
  LEVEL 2 - the net.    The policy's logits are byte-identical when the
            hidden content is swapped for different hidden content
            (not merely present/absent: a tracker that copied one bit of
            the true hand into a "legal" field would pass absent/present
            and fail swap).
  LEVEL 3 - the consumer. The privileged consumer's output (critic value,
            belief log-likelihood) MOVES under the same swap, so the
            channel is live as well as contained.

Usage as a library:

    gate = LeakGate(hidden_keys=["oe", "v7_oe_hand"],
                    parse=lambda msg: policy_path_obs(msg),           # level 1
                    logits=lambda msg: policy_logits(msg),           # level 2
                    consumer=lambda msg: critic_value(msg))          # level 3
    report = gate.run(messages, swap=swap_hidden)                     # swap(msg) -> msg with different hidden content
    assert report["pass"], report

`swap` must change the hidden content and NOTHING else.  Default
tolerances: level 1 exact equality, level 2 max |Δlogit| <= 1e-6, level 3
max |Δ| >= 1e-4 on at least one message.

Self-test (`python3 rl/probes/leak.py`): a synthetic policy that ignores
the hidden channel passes; a synthetic policy that reads one hidden
bit — a planted leak — is refused at level 2 with the max |Δlogit|
reported; a consumer that ignores the channel is refused at level 3.
"""
import copy
import json
import math


def _strip(msg, hidden_keys):
    m = {k: v for k, v in msg.items() if k not in hidden_keys}
    return m


def _maxdiff(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b))
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            return math.inf
        return max((_maxdiff(x, y) for x, y in zip(a, b)), default=0.0)
    return 0.0 if a == b else math.inf


class LeakGate:
    def __init__(self, hidden_keys, parse, logits, consumer=None, tol_logits=1e-6, min_move=1e-4):
        self.hidden = set(hidden_keys)
        self.parse, self.logits, self.consumer = parse, logits, consumer
        self.tol_logits, self.min_move = tol_logits, min_move

    def level1(self, msgs):
        worst = None
        for i, m in enumerate(msgs):
            a = self.parse(copy.deepcopy(m))
            b = self.parse(_strip(copy.deepcopy(m), self.hidden))
            if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
                worst = i
                break
        return {"level": 1, "pass": worst is None, "first_bad": worst,
                "note": "policy-path parse identical with and without the hidden keys"}

    def level2(self, msgs, swap):
        worst, where = 0.0, None
        for i, m in enumerate(msgs):
            a = self.logits(copy.deepcopy(m))
            b = self.logits(swap(copy.deepcopy(m)))
            d = _maxdiff(a, b)
            if d > worst:
                worst, where = d, i
        return {"level": 2, "pass": worst <= self.tol_logits, "max_abs_dlogit": worst, "at": where,
                "note": f"policy logits under a hidden-content swap; tol {self.tol_logits}"}

    def level3(self, msgs, swap):
        if self.consumer is None:
            return {"level": 3, "pass": None, "note": "no privileged consumer given"}
        best, where = 0.0, None
        for i, m in enumerate(msgs):
            a = self.consumer(copy.deepcopy(m))
            b = self.consumer(swap(copy.deepcopy(m)))
            d = _maxdiff(a, b)
            if d > best:
                best, where = d, i
        return {"level": 3, "pass": best >= self.min_move, "max_abs_dconsumer": best, "at": where,
                "note": f"privileged consumer must move under the swap; min {self.min_move}"}

    def run(self, msgs, swap):
        r1, r2, r3 = self.level1(msgs), self.level2(msgs, swap), self.level3(msgs, swap)
        return {"pass": bool(r1["pass"] and r2["pass"] and (r3["pass"] is not False)), "levels": [r1, r2, r3]}


# --- self-test -------------------------------------------------------------------

def _synthetic_msgs(n=20, seed=0):
    import random
    g = random.Random(seed)
    out = []
    for _ in range(n):
        out.append({"t": "consult", "legal": [g.random() for _ in range(8)],
                    "hidden": [float(g.randint(0, 1)) for _ in range(4)]})
    return out


def _swap(msg):
    msg["hidden"] = [1.0 - x for x in msg["hidden"]]
    return msg


def self_test():
    msgs = _synthetic_msgs()

    def parse(m):                                    # policy path: legal only
        return {"legal": m["legal"]}

    def clean_logits(m):
        return [sum(m["legal"][:4]), sum(m["legal"][4:]), m["legal"][0] * 2.0]

    def leaky_logits(m):                             # planted leak: one hidden bit reaches a logit
        base = clean_logits(m)
        base[1] += 0.5 * m["hidden"][2]
        return base

    def critic(m):
        return sum(m["legal"]) + 0.3 * sum(m["hidden"])

    def deaf_critic(m):
        return sum(m["legal"])

    ok = LeakGate(["hidden"], parse, clean_logits, critic).run(msgs, _swap)
    leak = LeakGate(["hidden"], parse, leaky_logits, critic).run(msgs, _swap)
    deaf = LeakGate(["hidden"], parse, clean_logits, deaf_critic).run(msgs, _swap)
    print("clean policy + live critic :", ok["pass"], [l.get("max_abs_dlogit", l.get("max_abs_dconsumer")) for l in ok["levels"]])
    print("planted leak               :", leak["pass"], "level 2 max|dlogit| =", leak["levels"][1]["max_abs_dlogit"])
    print("deaf consumer              :", deaf["pass"], "level 3 max|dconsumer| =", deaf["levels"][2]["max_abs_dconsumer"])
    good = ok["pass"] and (not leak["pass"]) and leak["levels"][1]["max_abs_dlogit"] > 0.1 and (not deaf["pass"])
    print(f"SELFTEST|clean_passes={ok['pass']}|leak_refused={not leak['pass']}|deaf_refused={not deaf['pass']}")
    return good


if __name__ == "__main__":
    import sys
    sys.exit(0 if self_test() else 1)

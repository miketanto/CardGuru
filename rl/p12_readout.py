#!/usr/bin/env python3
"""Phase 12 Amendment 4 (2): the argmax-over-classes readout on recorded census consults.

Rescores each recorded consult with the snapshot that played it (CPU, net run unbounded, the
lane's bound 5 applied as B*tanh(x/B), as rl/probes/cardswap.score), recomputes the server's
--argmax-classes choice (policy_server._argmax_classes: probability summed over candidates with
the same (type, afterstate row, referent names), first candidate of the heaviest class) and counts:
  pass_despite_majority : consults offering PASS and >= 1 non-PASS candidate where the chosen
                          class is PASS while the summed probability of non-PASS candidates > 0.5;
  noncreature_despite_creature_mass : consults offering >= 1 creature spell (SPELL candidate whose
                          referent entity has is-creature [29]) where the choice is not a creature
                          spell while the summed probability of the creature spells > the chosen
                          class's mass;
plus the sampled policy's act / creature rates on the same states (mean summed probability) vs
the argmax readout's, and the agreement of the recomputed choice with the recorded one.
  python3 rl/p12_readout.py NAME=CKPT=REC.jsonl [...]
"""
import math
import sys

import torch

sys.path.insert(0, "/home/user/CardGuru/rl")
sys.path.insert(0, "/home/user/CardGuru/rl/probes")
import v7_obs as V          # noqa: E402
import v7_policy as P       # noqa: E402
from cardswap import score  # noqa: E402
import json                 # noqa: E402

PASS, SPELL = 0, 2


def wil(k, n, z=1.96):
    if not n:
        return "NA"
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return f"{k}/{n} = {p:.3f} [{max(0, c - h):.3f},{min(1, c + h):.3f}]"


def pairs(path):
    hello, last, out = None, None, []
    for raw in open(path, "rb"):
        if not raw.strip():
            continue
        m = json.loads(raw)
        t = m.get("t")
        if t == "hello":
            hello = hello or m
        elif t == "consult" and "v7_ent" in m:
            last = m
        elif t is None and "a" in m and last is not None:
            out.append((last, int(m["a"])))
            last = None
    return hello, out


def classes(msg, pr):
    t, rows = msg["v7_cand_type"], msg["v7_cand"]
    refs = msg.get("v7_cand_refers") or [[] for _ in t]
    names = msg.get("v7_ent_name") or []
    mass, first, cls = {}, {}, []
    for k in range(len(t)):
        nm = tuple((names[r - 3] if 0 <= r - 3 < len(names) else r) for r in refs[k])
        key = (t[k], tuple(round(float(x), 4) for x in rows[k]), nm)
        mass[key] = mass.get(key, 0.0) + float(pr[k])
        first.setdefault(key, k)
        cls.append(key)
    best = max(mass, key=mass.get)
    return first[best], mass[best], cls


def is_creature_spell(msg, k):
    if msg["v7_cand_type"][k] != SPELL:
        return False
    refs = (msg.get("v7_cand_refers") or [[]] * len(msg["v7_cand_type"]))[k]
    if not refs:
        return False
    i = refs[0] - 3
    ents = msg["v7_ent"]
    return 0 <= i < len(ents) and float(ents[i][29]) > 0.5


def run(name, ck, rec):
    hello, pr_list = pairs(rec)
    ids = V.CardIds()
    obs = [V.parse_consult(m, ids, hello) for m, _ in pr_list]
    net = P.V7Policy.load(ck, device="cpu").eval()
    res = score(net, obs, "cpu", bound=5.0)
    S = dict(n=0, match=0, poff=0, ppass=0, pdm=0, pact_sum=0.0, pact_when_pass=0.0,
             coff=0, ccre=0, cdm=0, ccre_sum=0.0)
    for (m, a), (probs, _, _, _) in zip(pr_list, res):
        T = m["v7_cand_type"]
        pr = probs.tolist()
        ch, chmass, _ = classes(m, pr)
        S["n"] += 1
        S["match"] += int(ch == a)
        if PASS in T and any(x != PASS for x in T):
            S["poff"] += 1
            pact = sum(p for p, x in zip(pr, T) if x != PASS)
            S["pact_sum"] += pact
            if T[ch] == PASS:
                S["ppass"] += 1
                S["pact_when_pass"] += pact
                S["pdm"] += int(pact > 0.5)
        cre = [k for k in range(len(T)) if is_creature_spell(m, k)]
        if cre:
            S["coff"] += 1
            pc = sum(pr[k] for k in cre)
            S["ccre_sum"] += pc
            if ch in cre:
                S["ccre"] += 1
            elif pc > chmass:
                S["cdm"] += 1
    po, co = S["poff"], S["coff"]
    print("|".join([
        "READOUT", name, f"ckpt_episodes={getattr(net, 'episodes', '-')}", f"consults={S['n']}",
        f"choice_match={wil(S['match'], S['n'])}",
        f"pass_offered={po}", f"argmax_pass={wil(S['ppass'], po)}",
        f"pass_despite_majority={wil(S['pdm'], po)}",
        f"of_pass_choices={wil(S['pdm'], S['ppass'])}",
        f"mean_P_act_when_pass={S['pact_when_pass'] / S['ppass']:.3f}" if S["ppass"] else "mean_P_act_when_pass=NA",
        f"act_rate_sampled={S['pact_sum'] / po:.3f}" if po else "act_rate_sampled=NA",
        f"act_rate_argmax={(po - S['ppass']) / po:.3f}" if po else "act_rate_argmax=NA",
        f"creature_offered={co}", f"argmax_creature={wil(S['ccre'], co)}",
        f"noncreature_despite_creature_mass={wil(S['cdm'], co)}",
        f"creature_rate_sampled={S['ccre_sum'] / co:.3f}" if co else "creature_rate_sampled=NA",
    ]), flush=True)


if __name__ == "__main__":
    for spec in sys.argv[1:]:
        nm, ck, rec = spec.split("=", 2)
        run(nm, ck, rec)

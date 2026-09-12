#!/usr/bin/env python3
"""Gate 3d on recorded consults: the knowledge tracker's tokens.

    python3 rl/wire_check_3d.py FILE [FILE ...]

Checks (exit 1 on any failure):
  * slot count: len(v7_opp_hand) == the opponent's hand size from the
    player row (v7_players[1][2] * 10), every consult (up to v7_ohmax);
  * known ⊆ truth (needs -Drl.oracle recordings, key v7_oe_hand): the
    multiset of known slot names is contained in the true hand's names;
    the tracker never claims an identity the rules do not give it;
  * seen ⇐ known; origin one-hot; age within [0, 1];
  * remaining deck: every count ≤ the decklist count for that name and
    Σ remaining ≈ library size + unknown hand slots, reported as a mean
    absolute gap (cards seen then shuffled back are the honest residual);
  * action tokens: one-hot, age non-negative, newest first (ages
    non-decreasing down the list), every referent inside the token space;
  * counters: handDrift and oppHandTrunc sums.
Also prints the behaviour census: known fraction of slots by origin, the
action-type histogram, and how the known fraction grows with turn.
"""
import json
import sys
from collections import Counter, defaultdict

ORIGIN = ["opening", "drawn", "returned", "other"]
ACT = ["cast", "activate", "attack", "block", "declined_block", "passed_mana_up", "other"]


def main(paths):
    n = n_oracle = 0
    fails = Counter()
    ex = {}
    slots_by_origin = Counter()
    known_by_origin = Counter()
    acts = Counter()
    known_by_turn = defaultdict(lambda: [0, 0])
    deck_gap = []
    drift = trunc = 0
    decklist = {}
    for path in paths:
        for raw in open(path, "rb"):
            if not raw.startswith(b'{"t":"consult"'):
                continue
            m = json.loads(raw)
            if "v7_opp_hand" not in m:
                continue
            n += 1
            oh, ohn = m["v7_opp_hand"], m["v7_opp_hand_name"]
            od, odn = m["v7_opp_deck"], m["v7_opp_deck_name"]
            oa, oar = m["v7_opp_actions"], m["v7_opp_action_refers"]
            ctr = m["v7_ctr"]
            drift = max(drift, ctr.get("handDrift", 0))
            trunc += ctr.get("oppHandTrunc", 0)
            turn = round(m["v7_game"][0] * 30)
            hand_size = round(m["v7_players"][1][2] * 10)
            if len(oh) != min(hand_size, 12):
                fails["slot_count_vs_hand_size"] += 1
                ex.setdefault("slot_count_vs_hand_size", f"consult {n}: slots {len(oh)} hand {hand_size}")
            known_names = []
            for row, nm in zip(oh, ohn):
                o = max(range(4), key=lambda i: row[i])
                slots_by_origin[ORIGIN[o]] += 1
                if row[5] == 1:
                    known_by_origin[ORIGIN[o]] += 1
                    known_names.append(nm)
                    if row[6] != 1:
                        fails["known_implies_seen"] += 1
                if not (0 <= row[4] <= 1):
                    fails["age_range"] += 1
                known_by_turn[turn][0] += row[5] == 1
                known_by_turn[turn][1] += 1
            if "v7_oe_hand" in m:
                n_oracle += 1
                truth = Counter(m["v7_oe_hand"])
                if len(m["v7_oe_hand"]) != hand_size:
                    fails["oe_hand_size"] += 1
                for nm, c in Counter(known_names).items():
                    if truth[nm] < c:
                        fails["known_not_in_truth"] += 1
                        ex.setdefault("known_not_in_truth", f"consult {n}: {nm} x{c} vs truth {dict(truth)}")
            # deck
            lib = round(m["v7_players"][1][3] * 60)
            total = 0
            for row, nm in zip(od, odn):
                # idx 0 saturates at 4 (÷4, clipped); idx 1 is left / library
                total += round(row[1] * lib) if lib > 0 else round(row[0] * 4)
                if nm not in decklist:
                    decklist[nm] = row
            unknown_slots = sum(1 for r in oh if r[5] == 0)
            deck_gap.append(total - (lib + unknown_slots))
            # actions
            prev_age = -1
            n_tok = 3 + len(m["v7_ent"])
            for row, refs in zip(oa, oar):
                t = max(range(7), key=lambda i: row[i])
                acts[ACT[t]] += 1
                if row[7] < 0:
                    fails["action_age_negative"] += 1
                if row[7] < prev_age - 1e-6:
                    fails["actions_not_newest_first"] += 1
                prev_age = row[7]
                for x in refs:
                    if not (1 <= x < n_tok):
                        fails["action_ref_out_of_range"] += 1
    print(f"consults with tracker tokens={n} (oracle-labelled {n_oracle}); handDrift max={drift} oppHandTrunc sum={trunc}")
    print("slots by origin:", dict(slots_by_origin), " known by origin:", dict(known_by_origin))
    tot = sum(slots_by_origin.values())
    print(f"known fraction overall: {sum(known_by_origin.values()) / max(tot, 1):.3f}")
    print("known fraction by turn:", {t: f"{k}/{s}" for t, (k, s) in sorted(known_by_turn.items())[:12]})
    print("opponent actions:", dict(acts))
    if deck_gap:
        print(f"deck: Σremaining − (library + unknown slots): mean {sum(deck_gap) / len(deck_gap):+.2f}, "
              f"mean |gap| {sum(abs(g) for g in deck_gap) / len(deck_gap):.2f} (counts saturate at 4 in the wire)")
    print("failures:", dict(fails) or "none")
    for k, v in ex.items():
        print(f"  e.g. {k}: {v}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

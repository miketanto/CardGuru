#!/usr/bin/env python3
"""Gate 3b: per-field checks of the v7 entity row and candidate afterstates
on RECORDED consults (wire_echo_server.py output from real games).

    python3 rl/wire_check_3b.py FILE [FILE ...]

Two kinds of evidence, per field:
  * agreement with the v6 row of the same entity on the same consult
    (v6 row i+2 <-> v7 row i), for every field v6 also carries — power,
    toughness, damage, mv, tapped, sick, attacking, blocking, can-attack,
    can-block, entered-this-turn, token, creature, land, stack depth,
    instant/sorcery, and the 14 keyword bits v6 reads off the printed
    table (v7 reads them off the object's abilities now, so a mismatch is
    a granted or lost ability, listed by name);
  * an internal identity for the fields v6 does not carry — toughness
    remaining = toughness − damage, lethal-as-is ⇒ toughness remaining
    ≤ 0, castable only on my hand, attack afterstate: opp life after =
    opp life − damage dealt, block afterstate: life after = life − damage
    taken, target afterstate: player xor object.
Every field also reports how many rows EXERCISE it (non-zero); a field
with 0 exercised rows is "not exercised on these decks", not "pass".
Exit 1 on any failed identity or v6 disagreement outside the stated
keyword exception.
"""
import json
import sys
from collections import Counter, defaultdict

# v7 idx -> (v6 idx, name)
V6_PAIRS = {10: (8, "power"), 11: (9, "toughness"), 12: (10, "damage"), 13: (11, "tough_left"),
            17: (15, "mv"), 22: (16, "tapped"), 23: (17, "sick"), 24: (18, "attacking"),
            25: (19, "blocking"), 26: (22, "entered_this_turn"), 27: (23, "token"),
            29: (12, "creature"), 30: (13, "land"), 55: (20, "can_attack"), 56: (21, "can_block"),
            31: (39, "instant(stack)"), 32: (40, "sorcery(stack)")}
# v6 keyword columns (StateEncoder.KW_COL order, KW_BASE 24) -> v7 keyword idx (34 + KEYWORDS order)
KW_V6_TO_V7 = {24: 34, 25: 44, 26: 38, 27: 39, 28: 36, 29: 40, 30: 41, 31: 43, 32: 45, 33: 37,
               35: 46, 36: 47, 37: 49}
KW_NAMES = ["flying", "haste", "deathtouch", "lifelink", "first_strike", "double_strike", "trample",
            "vigilance", "flash", "menace", "reach", "defender", "ward", "hexproof", "shroud",
            "protection", "prowess", "ninjutsu"]
CT = ["PASS", "LAND", "SPELL", "ACTIVATE", "TARGET", "ATTACK", "BLOCK", "OTHER"]


def close(a, b, tol=1e-3):
    return abs(a - b) <= tol


def main(paths):
    exercised = Counter()
    fails = Counter()
    kw_mismatch = Counter()
    fail_examples = {}
    n = 0
    for path in paths:
        for raw in open(path, "rb"):
            if not raw.startswith(b'{"t":"consult"'):
                continue
            m = json.loads(raw)
            n += 1
            e6, e7, names = m["e"], m["v7_ent"], m["v7_ent_name"]
            stack_zone = [r[2] == 1 for r in e7]
            for i, r in enumerate(e7):
                v6 = e6[i + 2]
                for c in range(10, 64):
                    if r[c] != 0:
                        exercised[c] += 1
                for c7, (c6, nm) in V6_PAIRS.items():
                    if nm.endswith("(stack)") and not stack_zone[i]:
                        continue
                    if nm.endswith("(stack)") is False and stack_zone[i] and c7 in (10, 11, 12, 13, 29, 30):
                        continue          # v6 stack rows carry no body or type; v7 reads the source card
                    if not close(r[c7], v6[c6]):
                        fails[nm] += 1
                        fail_examples.setdefault(nm, f"{names[i]} v7={r[c7]:.3f} v6={v6[c6]:.3f} line-ent {n}/{i}")
                for c6, c7 in KW_V6_TO_V7.items():
                    if not close(r[c7], v6[c6]):
                        kw_mismatch[f"{KW_NAMES[c7 - 34]}:{names[i]}"] += 1
                # identities
                if not close(r[13], r[11] - r[12]):
                    fails["tough_left=tough-dmg"] += 1
                if r[57] == 1 and not (r[13] <= 0 or r[29] == 0):
                    fails["lethal_as_is"] += 1
                if r[52] == 1 and not (r[1] == 1 and r[7] == 1):
                    fails["castable_only_my_hand"] += 1
                if r[9] > 0 and not stack_zone[i]:
                    fails["stackpos_only_on_stack"] += 1
            # candidates
            p_me, p_opp = m["v7_players"][0][0], m["v7_players"][1][0]
            for t, row in zip(m["v7_cand_type"], m["v7_cand"]):
                a = row[8:]
                for j, v in enumerate(a):
                    if v != 0:
                        exercised[f"cand.{CT[t]}[{8 + j}]"] += 1
                if CT[t] == "TARGET":
                    if a[0] == 1 and (a[3] != 0 or a[4] != 0 or a[5] != 0):
                        fails["target_player_xor_object"] += 1
                if CT[t] == "ATTACK" and any(a):
                    if not close(a[5], p_opp - a[0]):
                        fails["attack_opp_life_after"] += 1
                        fail_examples.setdefault("attack_opp_life_after", f"a0={a[0]:.3f} a5={a[5]:.3f} opp={p_opp:.3f}")
                    if not close(a[10], p_me - a[9]):
                        fails["attack_my_life_after"] += 1
                if CT[t] == "BLOCK" and any(a):
                    if not close(a[7], p_me - a[0]):
                        fails["block_life_after"] += 1
                        fail_examples.setdefault("block_life_after", f"a0={a[0]:.3f} a7={a[7]:.3f} me={p_me:.3f}")
                if CT[t] in ("LAND", "SPELL", "ACTIVATE") and any(a):
                    if not (a[2] + a[3] == 1):
                        fails["speed_onehot"] += 1
                if CT[t] == "LAND" and a[2] != 0:
                    fails["land_play_is_sorcery_speed"] += 1
                if CT[t] in ("PASS", "OTHER") and any(a):
                    fails["pass_afterstate_reserved"] += 1
    print(f"consults={n}")
    ent_names = {10: "power", 11: "toughness", 12: "damage", 13: "tough_left", 14: "printed_power",
                 15: "printed_tough", 16: "loyalty", 17: "mv", 18: "ctr_p1p1", 19: "ctr_m1m1",
                 20: "ctr_loyalty", 21: "ctr_other", 22: "tapped", 23: "sick", 24: "attacking",
                 25: "blocking", 26: "entered", 27: "token", 28: "turns_on_bf", 29: "creature",
                 30: "land", 31: "instant", 32: "sorcery", 33: "other_perm", 52: "castable",
                 53: "mana_left_if_cast", 54: "legal_targets", 55: "can_attack", 56: "can_block",
                 57: "lethal_as_is", 58: "stack_X", 59: "stack_modes", 60: "stack_mine",
                 61: "stack_is_ability"}
    for i, k in enumerate(KW_NAMES):
        ent_names[34 + i] = "kw_" + k
    print("exercised (rows with a non-zero value):")
    for c in sorted(ent_names):
        print(f"  ent[{c:2d}] {ent_names[c]:20s} {exercised.get(c, 0)}")
    cand_ex = {k: v for k, v in exercised.items() if isinstance(k, str)}
    for k in sorted(cand_ex):
        print(f"  {k:24s} {cand_ex[k]}")
    print("v6 disagreements / failed identities:", dict(fails) or "none")
    for k, v in fail_examples.items():
        print(f"  e.g. {k}: {v}")
    print("keyword bits differing from the printed table (v7 = live abilities):",
          dict(kw_mismatch.most_common(12)) or "none")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

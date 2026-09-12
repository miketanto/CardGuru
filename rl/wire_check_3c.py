#!/usr/bin/env python3
"""Gate 3c on recorded consults: edge endpoints, the two v7 edge types, and
referent coverage.

    python3 rl/wire_check_3c.py FILE [FILE ...]

Checks (exit 1 on any failure):
  * every edge endpoint is inside the token space (the validator's check,
    repeated here with the count);
  * can_block (6) edges appear only in declare-blockers consults where I am
    not the active player; src is my untapped creature, dst an attacking
    creature; and EVERY BLOCK candidate's (blocker, attacker) referent pair
    is a can_block edge of the same consult - the candidate builder and the
    edge emitter agree on legality;
  * stack_above (7): src and dst are stack-zone entities and dst is exactly
    one position deeper (idx 9 differs by 1/4); the chain has n-1 edges for
    n emitted stack objects;
  * referent coverage: non-PASS candidates with an entity or player
    referent / all non-PASS, plus the wire's own refersFallback sum.
"""
import json
import sys
from collections import Counter

CT = ["PASS", "LAND", "SPELL", "ACTIVATE", "TARGET", "ATTACK", "BLOCK", "OTHER"]


def main(paths):
    n = 0
    fails = Counter()
    seen = Counter()
    nonpass = covered = fallback = 0
    for path in paths:
        for raw in open(path, "rb"):
            if not raw.startswith(b'{"t":"consult"'):
                continue
            m = json.loads(raw)
            n += 1
            e7, g = m["v7_ent"], m["v7_game"]
            n_tok = 3 + len(e7)
            edges = m["v7_edges"]
            e6 = [e for e in edges if e[2] == 6]
            e7s = [e for e in edges if e[2] == 7]
            seen["edges"] += len(edges)
            seen["can_block"] += len(e6)
            seen["stack_above"] += len(e7s)
            for s, d, t in edges:
                if not (0 <= s < n_tok and 0 <= d < n_tok):
                    fails["endpoint_out_of_range"] += 1
            declare_blockers_defending = g[6] == 1 and g[1] == 0
            if e6 and not declare_blockers_defending:
                fails["can_block_outside_declare_blockers"] += 1
            if declare_blockers_defending:
                seen["declare_blockers_consults"] += 1
            pairs = set()
            for s, d, t in e6:
                src, dst = e7[s - 3], e7[d - 3]
                if not (src[7] == 1 and src[22] == 0 and src[29] == 1):
                    fails["can_block_src_not_my_untapped_creature"] += 1
                if not (dst[24] == 1 and dst[29] == 1):
                    fails["can_block_dst_not_attacking_creature"] += 1
                pairs.add((s, d))
            for t, refs in zip(m["v7_cand_type"], m["v7_cand_refers"]):
                if t != 0:
                    nonpass += 1
                    if refs:
                        covered += 1
                if CT[t] == "BLOCK":
                    seen["block_candidates"] += 1
                    for b, a in zip(refs[0::2], refs[1::2]):
                        if (b, a) not in pairs:
                            fails["block_candidate_pair_not_a_can_block_edge"] += 1
            stack_rows = [i for i, r in enumerate(e7) if r[2] == 1]
            if len(stack_rows) >= 2:
                seen["consults_with_stack_depth_ge_2"] += 1
                if len(e7s) != len(stack_rows) - 1:
                    fails["stack_above_chain_length"] += 1
            for s, d, t in e7s:
                src, dst = e7[s - 3], e7[d - 3]
                if not (src[2] == 1 and dst[2] == 1 and abs((dst[9] - src[9]) - 0.25) < 1e-3):
                    fails["stack_above_not_one_deeper"] += 1
            fallback += m["v7_ctr"].get("refersFallback", 0)
    print(f"consults={n} edges={seen['edges']} can_block={seen['can_block']} "
          f"(in {seen['declare_blockers_consults']} defending declare-blockers consults, "
          f"{seen['block_candidates']} BLOCK candidates) stack_above={seen['stack_above']} "
          f"(consults with >=2 stack objects: {seen['consults_with_stack_depth_ge_2']})")
    print(f"referent coverage: {covered}/{nonpass} = {covered / max(nonpass, 1):.4f}; refersFallback sum={fallback}")
    print("failures:", dict(fails) or "none")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

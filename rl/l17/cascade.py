"""L17 cloud step 3a (first half): does the replay fail an action before the
state visibly diverges?

  python3 rl/l17/cascade.py SPEC.tsv OUT.tsv [--tag TAG]

A forced logged action that the engine refuses ("attacker absent", "cast whose
card is not in hand") can mean two different things:

  * the replay had ALREADY drifted, in state the check does not compare
    (library, graveyard, exile, counters, tapped status), and the refusal is
    the first visible symptom -- cascading divergence; or
  * the refusal itself is what breaks the state, and everything matched up to
    that point.

The two are told apart by which comes first. For every game with a mismatch,
this compares the game turn of the FIRST failed forced action with the game
turn of the FIRST state mismatch. Output is the share of mismatched games whose
first failure strictly precedes the first mismatch, broken down by the kind of
the first failure. `analyze.py` is untouched, so the reproduction run's numbers
are not re-derived here -- this reads the same OUT.tsv.
"""
import collections
import csv
import gzip
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'l17_dsk')
sys.path.insert(0, HERE)
from build_specs import turn_exists, game_turn, on_play  # noqa: E402
from analyze import parse_out, logged_state, diff, FIELDS, wilson  # noqa: E402

# guided-mode bookkeeping records, not refusals of a logged action
NOT_A_REFUSAL = {'rescued_from_graveyard'}


def main():
    spec_path, out_path = sys.argv[1], sys.argv[2]
    tag = sys.argv[sys.argv.index('--tag') + 1] if '--tag' in sys.argv else 'run'
    cards = json.load(open(os.path.join(DATA, 'DSK_top2000.cards.json'), encoding='utf-8'))
    games = [json.loads(l) for l in gzip.open(os.path.join(DATA, 'DSK_top2000.jsonl.gz'))]
    sel = [int(l.split('\t')[1]) for l in open(spec_path, encoding='utf-8') if l.startswith('G\t')]
    R, F, T, X, Z = parse_out(out_path)
    rows = []
    for gi in sel:
        if gi not in Z:
            continue
        g = games[gi]
        nt = int(g['num_turns'])
        uisa = on_play(g)
        a_side = 'user' if uisa else 'oppo'
        seq = sorted((game_turn(side, n, uisa), side, n)
                     for n in range(1, nt + 1) for side in (a_side, 'oppo' if a_side == 'user' else 'user')
                     if turn_exists(g, side, n))
        snaps = R.get(gi, {})
        over_at = min((t for t, s in snaps.items() if s['over']), default=None)
        first_t = None
        for t, side, n in seq:
            eng = snaps.get(t)
            if eng is None:
                if over_at is not None and over_at < t:
                    first_t = t
                break
            log = logged_state(g, side, n, cards)
            if any(diff(f, log[f], eng[f]) for f in FIELDS):
                first_t = t
                break
        fails = sorted((f for f in F.get(gi, []) if f[4].split('@')[0] not in NOT_A_REFUSAL), key=lambda f: f[0])
        rows.append(dict(game=gi, first_mismatch_turn=first_t if first_t is not None else '',
                         first_fail_turn=fails[0][0] if fails else '',
                         first_fail_seat=fails[0][1] if fails else '',
                         first_fail_kind=fails[0][2] if fails else '',
                         first_fail_why=fails[0][4].split('@')[0] if fails else '',
                         n_fails=len(fails)))
    csv_path = os.path.join(DATA, f'cascade_{tag}.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    mis = [r for r in rows if r['first_mismatch_turn'] != '']
    with_fail = [r for r in mis if r['first_fail_turn'] != '']
    before = [r for r in with_fail if r['first_fail_turn'] < r['first_mismatch_turn']]
    same = [r for r in with_fail if r['first_fail_turn'] == r['first_mismatch_turn']]
    after = [r for r in with_fail if r['first_fail_turn'] > r['first_mismatch_turn']]
    nofail = [r for r in mis if r['first_fail_turn'] == '']
    lo, hi = wilson(len(before), len(mis))
    print(f'CASCADE|tag={tag}|games={len(rows)}|mismatched={len(mis)}|out={csv_path}')
    print(f'CASCADE|first_failed_action_BEFORE_first_mismatch={len(before)}/{len(mis)}='
          f'{len(before) / max(1, len(mis)):.3f} wilson95=[{lo:.3f},{hi:.3f}]')
    print(f'CASCADE|same_turn={len(same)}|after={len(after)}|no_failed_action_at_all={len(nofail)}')
    print(f'CASCADE|kind_of_first_failure_when_before={collections.Counter((r["first_fail_seat"], r["first_fail_kind"], r["first_fail_why"]) for r in before).most_common(8)}')
    lead = [r['first_mismatch_turn'] - r['first_fail_turn'] for r in before]
    if lead:
        lead.sort()
        print(f'CASCADE|lead_side_turns_median={lead[len(lead) // 2]}|mean={sum(lead) / len(lead):.2f}|max={lead[-1]}')


if __name__ == '__main__':
    main()

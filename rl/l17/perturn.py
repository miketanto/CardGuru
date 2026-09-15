"""L17 cloud step 3a (second half): per-turn fidelity of the `resync` variant.

  python3 rl/l17/perturn.py SPEC.tsv OUT.tsv --tag TAG

Under `-Dl17.variant=resync` the engine state is pushed to the logged
end-of-side-turn state at the start of every turn, so each side-turn is replayed
from a correct start. "Turns matched before the first mismatch" is meaningless
under that regime and is NOT computed here. What is computed is

    per-turn fidelity = share of side-turns whose END state matches the log,
                        given a correct START,

over the same compared fields as `analyze.py` (user life, opponent life, user
lands / creatures / non-creatures / hand, opponent hand count).

A side-turn counts as having a correct start when the resync that preceded it
left nothing unmet (`RS` line, column 4 = 0). Side-turns whose start could not
be fully rebuilt -- a token or a [Face-Down Card] the engine did not already
have, which the log does not describe well enough to recreate -- are reported
separately rather than silently pooled in.
"""
import collections
import csv
import gzip
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'l17_dsk')
sys.path.insert(0, HERE)
from build_specs import turn_exists, game_turn, on_play  # noqa: E402
from analyze import parse_out, logged_state, diff, FIELDS, wilson  # noqa: E402


def parse_rs(path):
    rs = collections.defaultdict(dict)
    for line in open(path, encoding='utf-8'):
        if not line.startswith('RS\t'):
            continue
        f = line.rstrip('\n').split('\t')
        rs[int(f[1])][int(f[2])] = dict(unmet=int(f[3]), removed=int(f[4]), added=int(f[5]), handfix=int(f[6]))
    return rs


def main():
    spec_path, out_path = sys.argv[1], sys.argv[2]
    tag = sys.argv[sys.argv.index('--tag') + 1] if '--tag' in sys.argv else 'resync'
    cards = json.load(open(os.path.join(DATA, 'DSK_top2000.cards.json'), encoding='utf-8'))
    games = [json.loads(l) for l in gzip.open(os.path.join(DATA, 'DSK_top2000.jsonl.gz'))]
    sel = [int(l.split('\t')[1]) for l in open(spec_path, encoding='utf-8') if l.startswith('G\t')]
    R, F, T, X, Z = parse_out(out_path)
    RS = parse_rs(out_path)
    rows = []
    fieldmiss = collections.Counter()
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
        rsg = RS.get(gi, {})
        for t, side, n in seq:
            eng = snaps.get(t)
            if eng is None:
                rows.append(dict(game=gi, turn=t, side=f'{side}_{n}', evaluated=0, clean_start=0,
                                 matched=0, fields=''))
                continue
            # the start of side-turn t is the resync written for t-1 (turn 1 starts from
            # the built opening state, which is exact for the user seat by construction)
            prev = rsg.get(t - 1)
            clean = 1 if (t == 1 or (prev is not None and prev['unmet'] == 0)) else 0
            log = logged_state(g, side, n, cards)
            bad = [f for f in FIELDS if diff(f, log[f], eng[f])]
            for f in bad:
                fieldmiss[f] += 1
            rows.append(dict(game=gi, turn=t, side=f'{side}_{n}', evaluated=1, clean_start=clean,
                             matched=int(not bad), fields=' '.join(bad)))
    csv_path = os.path.join(DATA, f'perturn_{tag}.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    ev = [r for r in rows if r['evaluated']]
    clean = [r for r in ev if r['clean_start']]
    m_all = sum(r['matched'] for r in ev)
    m_cl = sum(r['matched'] for r in clean)
    lo, hi = wilson(m_all, len(ev))
    lo2, hi2 = wilson(m_cl, len(clean))
    ngames = len({r['game'] for r in rows})
    print(f'PERTURN|tag={tag}|games={ngames}|side_turns={len(rows)}|evaluated={len(ev)}|out={csv_path}')
    print(f'PERTURN|matched_all_evaluated={m_all}/{len(ev)}={m_all / max(1, len(ev)):.3f} wilson95=[{lo:.3f},{hi:.3f}]')
    print(f'PERTURN|matched_given_clean_start={m_cl}/{len(clean)}={m_cl / max(1, len(clean)):.3f} wilson95=[{lo2:.3f},{hi2:.3f}]')
    print(f'PERTURN|clean_start_share={len(clean)}/{len(ev)}={len(clean) / max(1, len(ev)):.3f}')
    print(f'PERTURN|mismatching_field_counts={fieldmiss.most_common()}')
    allrs = [x for gv in RS.values() for x in gv.values()]
    if allrs:
        print(f'PERTURN|resyncs={len(allrs)}|unmet_items={sum(x["unmet"] for x in allrs)}'
              f'|permanents_removed={sum(x["removed"] for x in allrs)}'
              f'|permanents_added={sum(x["added"] for x in allrs)}'
              f'|hand_cards_moved={sum(x["handfix"] for x in allrs)}')
    # per-turn fidelity by how far into the game the side-turn is
    byt = collections.defaultdict(lambda: [0, 0])
    for r in clean:
        b = byt[min(r['turn'], 21)]
        b[0] += r['matched']
        b[1] += 1
    print('PERTURN|by_game_turn=' + ' '.join(f'{k}:{v[0]}/{v[1]}' for k, v in sorted(byt.items())))


if __name__ == '__main__':
    main()

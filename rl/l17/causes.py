"""L17: classify the first mismatch of each game and compare base vs guided runs.

  python3 rl/l17/causes.py BASE_TAG [GUIDED_TAG] --out-base OUT.tsv [--out-guided OUT.tsv]

Reads rl/l17_dsk/fidelity_games_<tag>.csv (written by analyze.py) and the F
lines of the base run. One cause per game, first rule that applies:
  1. forced_<kind>_<reason>: a forced logged action failed (F line) on the
     mismatching game turn or the one before (cast not in hand / not playable,
     land not in hand, attacker absent, ...), i.e. an earlier divergence surfaced;
  2. hidden_choice: the guided run (log-guided targets, manifest dread, library
     searches, draws rescued from the graveyard) matched more turns;
  3. ability_logged: the mismatching side-turn logs an activated/triggered
     ability id for the seat whose field broke (ability ids are unmapped, so
     activated abilities other than fetch lands are not replayed);
  4. otherwise the field itself (life / hand / creatures / lands / ...).
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
from build_specs import game_turn, on_play  # noqa: E402


def rows(tag):
    return {int(r['game']): r for r in csv.DictReader(open(os.path.join(DATA, f'fidelity_games_{tag}.csv'), encoding='utf-8'))}


def fails(path):
    F = collections.defaultdict(list)
    for line in open(path, encoding='utf-8'):
        f = line.rstrip('\n').split('\t')
        if f[0] == 'F':
            F[int(f[1])].append((int(f[2]), f[3], f[4], f[5], f[6].split('@')[0]))
    return F


def main():
    base = sys.argv[1]
    guided = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else None
    outb = sys.argv[sys.argv.index('--out-base') + 1]
    B = rows(base)
    G = rows(guided) if guided else {}
    F = fails(outb)
    games = [json.loads(l) for l in gzip.open(os.path.join(DATA, 'DSK_top2000.jsonl.gz'))]
    cause = collections.Counter()
    examples = collections.defaultdict(list)
    per = {}
    for gi, r in B.items():
        if not r['first_mismatch_field']:
            continue
        side, n = r['first_mismatch_side_turn'].rsplit('_', 1)
        n = int(n)
        g = games[gi]
        t = game_turn(side, n, on_play(g))
        fld = r['first_mismatch_field']
        c = None
        near = [f for f in F.get(gi, []) if t - 1 <= f[0] <= t and f[2] != 'CASTI' and f[4] != 'rescued_from_graveyard']
        if near:
            f = near[0]
            c = f'forced_{f[2]}_{f[4]}'
        elif gi in G and int(G[gi]['turns_matched']) > int(r['turns_matched']):
            c = 'hidden_choice'
        else:
            who = 'oppo' if fld.startswith('oppo') else 'user'
            if g.get(f'{side}_turn_{n}_{who}_abilities'):
                c = 'ability_logged'
            else:
                c = 'field_' + fld
        cause[c] += 1
        per[gi] = c
        if len(examples[c]) < 3:
            examples[c].append(f"game={gi} {r['first_mismatch_side_turn']} {fld}: {r['mismatch_detail'][:160]}")
    n = sum(cause.values())
    print(f'CAUSES|base={base}|guided={guided}|games_with_mismatch={n}')
    for c, k in cause.most_common():
        print(f'CAUSE|{c}|{k}|{k / n:.3f}')
        for e in examples[c]:
            print(f'   EX|{e}')
    if G:
        both = [gi for gi in B if gi in G]
        gain = sum(1 for gi in both if int(G[gi]['turns_matched']) > int(B[gi]['turns_matched']))
        loss = sum(1 for gi in both if int(G[gi]['turns_matched']) < int(B[gi]['turns_matched']))
        print(f'GUIDED_VS_BASE|games={len(both)}|guided_longer={gain}|guided_shorter={loss}')
    with open(os.path.join(DATA, f'causes_{base}.csv'), 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['game', 'cause'])
        for gi in sorted(per):
            w.writerow([gi, per[gi]])


if __name__ == '__main__':
    main()

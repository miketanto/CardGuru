"""L17 step 2: XMage coverage of the DSK top-2000 17Lands sample.

Usage (inside WSL):
  grep -ohE 'new SetCardInfo\\("[^"]+"' /home/user/mage/Mage.Sets/src/mage/sets/*.java \
      | sed 's/new SetCardInfo("//; s/"$//' | sort -u > xmage_names.txt
  python3 rl/l17/coverage.py xmage_names.txt

The name list is every card name registered in any Mage.Sets set class at the
pin (7554968c); CardRepository is built by scanning exactly these classes.
Writes rl/l17_dsk/coverage_games.csv and prints the summary block that goes
into rl/L17-FIDELITY.md.
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

OPP_KEYS_OPP_TURN = ('lands_played', 'creatures_cast', 'non_creatures_cast',
                     'oppo_instants_sorceries_cast')
OPP_KEYS_USER_TURN = ('user_oppo_instants_sorceries_cast',)


def wilson(k, n, z=1.96):
    if n == 0:
        return (float('nan'), float('nan'))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def norm(s):
    return s.replace('’', "'").strip().lower()


def xmage_names(path):
    """path = a names file (one per line) or the Mage.Sets/src/mage/sets dir."""
    import re
    if os.path.isdir(path):
        pat = re.compile(r'new SetCardInfo\("([^"]+)"')
        out = set()
        for fn in os.listdir(path):
            if fn.endswith('.java'):
                out.update(pat.findall(open(os.path.join(path, fn), encoding='utf-8', errors='replace').read()))
        return sorted(out)
    return [l.strip() for l in open(path, encoding='utf-8')]


def load_xmage(path):
    names = set()
    for line in xmage_names(path):
        if not line:
            continue
        names.add(norm(line))
        if ' // ' in line:
            for half in line.split(' // '):
                names.add(norm(half))
    return names


def in_xmage(name, xm):
    if norm(name) in xm:
        return True
    if ' // ' in name:
        return all(norm(h) in xm for h in name.split(' // ')) or norm(name.split(' // ')[0]) in xm
    return False


def opp_cards(g):
    out = []
    for k, v in g.items():
        if not isinstance(v, str):
            continue
        parts = k.split('_', 3)
        if len(parts) < 4 or parts[1] != 'turn':
            continue
        side, rest = parts[0], parts[3]
        if (side == 'oppo' and rest in OPP_KEYS_OPP_TURN) or (side == 'user' and rest in OPP_KEYS_USER_TURN):
            out.extend(x for x in v.split('|') if x)
    return out


def main():
    xm = load_xmage(sys.argv[1])
    cards = json.load(open(os.path.join(DATA, 'DSK_top2000.cards.json'), encoding='utf-8'))
    games = [json.loads(l) for l in gzip.open(os.path.join(DATA, 'DSK_top2000.jsonl.gz'))]
    miss_user = collections.Counter()
    miss_opp = collections.Counter()
    rows = []
    n_user_ok = n_both_ok = 0
    for i, g in enumerate(games):
        deck = g.get('deck') or {}
        if isinstance(deck, str):
            deck = json.loads(deck)
        mu = sorted({c for c in deck if not in_xmage(c, xm)})
        ids = opp_cards(g)
        onames = {cards[x]['name'] for x in ids if x in cards}
        mo = sorted({c for c in onames if not in_xmage(c, xm)})
        for c in mu:
            miss_user[c] += 1
        for c in mo:
            miss_opp[c] += 1
        u_ok = not mu
        b_ok = u_ok and not mo
        n_user_ok += u_ok
        n_both_ok += b_ok
        rows.append((i, int(u_ok), int(not mo), int(b_ok), len(deck), sum(deck.values()),
                     '|'.join(mu), '|'.join(mo)))
    with open(os.path.join(DATA, 'coverage_games.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['game', 'user_deck_covered', 'opp_logged_covered', 'both_covered',
                    'deck_distinct', 'deck_cards', 'user_missing', 'opp_missing'])
        w.writerows(rows)
    n = len(games)
    lo, hi = wilson(n_user_ok, n)
    lo2, hi2 = wilson(n_both_ok, n)
    print(f'COVERAGE|games={n}|xmage_names={len(xm)}')
    print(f'COVERAGE|user_deck_full={n_user_ok}/{n}={n_user_ok/n:.3f} wilson95=[{lo:.3f},{hi:.3f}]')
    print(f'COVERAGE|user_and_opp_logged_full={n_both_ok}/{n}={n_both_ok/n:.3f} wilson95=[{lo2:.3f},{hi2:.3f}]')
    all_deck = collections.Counter()
    for g in games:
        d = g.get('deck') or {}
        if isinstance(d, str):
            d = json.loads(d)
        all_deck.update(d.keys())
    print(f'COVERAGE|distinct_user_deck_names={len(all_deck)} missing={len(miss_user)}')
    print('MISSING_USER|' + '; '.join(f'{c}={k}' for c, k in miss_user.most_common()))
    print('MISSING_OPP|' + '; '.join(f'{c}={k}' for c, k in miss_opp.most_common()))
    deck_sizes = collections.Counter(sum((g.get('deck') or {}).values()) for g in games)
    print('DECK_SIZES|' + str(sorted(deck_sizes.items())))


if __name__ == '__main__':
    main()

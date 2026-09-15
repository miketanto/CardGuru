"""L17 cloud step 3b: infer which card owns each logged 17Lands ability id.

  python3 rl/l17/ability_map.py [OUT.csv]

The `*_abilities` columns hold Arena ability ids, and the abilities table is a
separate 17Lands download this instance cannot reach. But an ability can only be
used by a card its controller has, so the owner can be inferred from
co-occurrence over the whole 2,000-game sample:

  for every (game, side-turn, seat) that logs ability ids, the candidate set is
  every card name that seat could have used an ability of -- its permanents at
  end of turn AND at the end of the previous side-turn (a card that sacrifices
  itself, like Terramorphic Expanse, or dies to its own ability is in neither
  the one nor the other), the cards it cast that turn, the creatures of its the
  log records dying that turn, and (user seat only, whose hand is logged) the
  cards in its hand at the end of this and the previous side-turn.

For each ability id, rank candidates by coverage (share of that id's
occurrences whose candidate set holds the card) times lift (coverage divided by
the card's base rate over all occurrence sets, capped at 50 so a rare card that
appears in 60% of occurrences does not beat the true owner at 100%). The top
candidate is accepted when coverage >= MIN_COV and occurrences >= MIN_OCC.

What this cannot do: it maps an id to a CARD, not to WHICH ability of that card.
For a card with one non-mana activated ability that is exact; otherwise the
rebuilder has to pick. It also cannot tell an activated ability from a triggered
one -- the column logs both -- so ids whose card has no activated ability are
simply dropped by the rebuilder.
"""
import collections
import csv
import gzip
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'l17_dsk')

MIN_OCC = 5
MIN_COV = 0.90
LIFT_CAP = 50.0
BASICS = {'Plains', 'Island', 'Swamp', 'Mountain', 'Forest'}


def ids(g, key):
    v = g.get(key)
    return [x for x in v.split('|') if x] if isinstance(v, str) and v else []


def occurrences(games, cards):
    """-> (ability id -> [candidate name set], all candidate sets)."""
    def nm(i):
        c = cards.get(i)
        return c['name'] if c else None

    def visible(g, p, who):
        """Cards `who` had at the end of side-turn with prefix p."""
        s = set()
        for key in ('eot_%s_lands_in_play', 'eot_%s_creatures_in_play', 'eot_%s_non_creatures_in_play'):
            s |= {nm(i) for i in ids(g, p + key % who)}
        if who == 'user':
            s |= {nm(i) for i in ids(g, p + 'eot_user_cards_in_hand')}
        return s

    occ = collections.defaultdict(list)
    allsets = []
    for g in games:
        nt = int(g['num_turns'])
        prefixes = [f'{side}_turn_{n}_' for n in range(1, nt + 1) for side in ('user', 'oppo')]
        for k, p in enumerate(prefixes):
            side = 'user' if p.startswith('user') else 'oppo'
            prev = prefixes[k - 1] if k else None
            for who in ('user', 'oppo'):
                a = ids(g, p + f'{who}_abilities')
                if not a:
                    continue
                cand = visible(g, p, who)
                if prev:
                    cand |= visible(g, prev, who)
                if who == side:
                    for key in ('lands_played', 'creatures_cast', 'non_creatures_cast'):
                        cand |= {nm(i) for i in ids(g, p + key)}
                cand |= {nm(i) for i in ids(g, p + f'{who}_instants_sorceries_cast')}
                for key in (f'{who}_creatures_killed_combat', f'{who}_creatures_killed_non_combat'):
                    cand |= {nm(i) for i in ids(g, p + key)}
                cand.discard(None)
                allsets.append(cand)
                for x in a:
                    occ[x].append(cand)
    return occ, allsets


def infer(occ, allsets):
    base = collections.Counter()
    for s in allsets:
        base.update(s)
    total = max(1, len(allsets))
    rows = []
    for k, v in occ.items():
        cnt = collections.Counter()
        for s in v:
            cnt.update(s)
        n = len(v)
        scored = []
        for c, hits in cnt.items():
            cov = hits / n
            lift = cov / max(1e-9, base[c] / total)
            scored.append((cov * min(lift, LIFT_CAP), cov, lift, c))
        scored.sort(reverse=True)
        top = scored[0] if scored else (0, 0, 0, '')
        second = scored[1] if len(scored) > 1 else (0, 0, 0, '')
        ok = n >= MIN_OCC and top[1] >= MIN_COV
        rows.append(dict(ability_id=k, occurrences=n, card=top[3] if ok else '',
                         coverage=round(top[1], 4), lift=round(min(top[2], 999), 2),
                         accepted=int(ok), is_basic_land=int(top[3] in BASICS),
                         runner_up=second[3], runner_up_coverage=round(second[1], 4)))
    rows.sort(key=lambda r: -r['occurrences'])
    return rows


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DATA, 'ability_map_cloud.csv')
    cards = json.load(open(os.path.join(DATA, 'DSK_top2000.cards.json'), encoding='utf-8'))
    games = [json.loads(l) for l in gzip.open(os.path.join(DATA, 'DSK_top2000.jsonl.gz'))]
    occ, allsets = occurrences(games, cards)
    rows = infer(occ, allsets)
    with open(out, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    acc = [r for r in rows if r['accepted']]
    nonland = [r for r in acc if not r['is_basic_land']]
    tot_occ = sum(r['occurrences'] for r in rows)
    acc_occ = sum(r['occurrences'] for r in acc)
    nl_occ = sum(r['occurrences'] for r in nonland)
    print(f'ABILMAP|ids={len(rows)}|accepted={len(acc)}|non_basic_land={len(nonland)}|out={out}')
    print(f'ABILMAP|occurrences={tot_occ}|accepted={acc_occ}={acc_occ / tot_occ:.3f}|non_basic_land={nl_occ}={nl_occ / tot_occ:.3f}')


if __name__ == '__main__':
    main()

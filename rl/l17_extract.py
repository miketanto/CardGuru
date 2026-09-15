#!/usr/bin/env python3
"""Compact a 17Lands replay_data CSV into a seeded game sample for the cloud trial (rl/L17-CLOUD.md).

Streams the gzipped CSV row by row (constant memory, CPU only). Keeps games from strong
players (user_game_win_rate_bucket >= --min-wr and user_n_games_bucket >= --min-games),
reservoir-samples --n of them with --seed, and writes one JSON object per game holding every
non-empty column except the per-card deck/sideboard count columns, which become
{"deck": {name: n}, "sideboard": {name: n}}. Card ids in the per-turn fields stay as the raw
pipe-separated Arena ids; the id -> name/type/mana-value map for every id seen is written next
to it (from cards.csv). Ability ids (e.g. *_abilities) are not in cards.csv and are left raw.

Output: <out>.jsonl.gz, <out>.cards.json, <out>.stats.txt
"""
import argparse, csv, gzip, json, random, re, collections

ap = argparse.ArgumentParser()
ap.add_argument('--replay', required=True)
ap.add_argument('--cards', required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--n', type=int, default=2000)
ap.add_argument('--seed', type=int, default=17)
ap.add_argument('--min-wr', type=float, default=0.58)
ap.add_argument('--min-games', type=int, default=50)
ap.add_argument('--event', default='PremierDraft')
a = ap.parse_args()

csv.field_size_limit(10**8)
rng = random.Random(a.seed)
res, seen, kept = [], 0, 0
wr_hist = collections.Counter()
with gzip.open(a.replay, 'rt', newline='') as f:
    r = csv.reader(f)
    h = next(r)
    deck_i = [(i, c[5:].replace('  ', ', ')) for i, c in enumerate(h) if c.startswith('deck_')]
    side_i = [(i, c[10:].replace('  ', ', ')) for i, c in enumerate(h) if c.startswith('sideboard_')]
    other_i = [(i, c) for i, c in enumerate(h) if not c.startswith(('deck_', 'sideboard_'))]
    ix = {c: i for i, c in enumerate(h)}
    for row in r:
        seen += 1
        try:
            wr = float(row[ix['user_game_win_rate_bucket']] or 0)
            ng = float(row[ix['user_n_games_bucket']] or 0)
        except ValueError:
            continue
        wr_hist[round(wr, 2)] += 1
        if row[ix['event_type']] != a.event or wr < a.min_wr or ng < a.min_games:
            continue
        kept += 1
        if len(res) < a.n:
            res.append(row)
        else:
            j = rng.randrange(kept)
            if j < a.n:
                res[j] = row

ids, games = set(), []
for row in res:
    g = {c: row[i] for i, c in other_i if row[i] not in ('', 'None')}
    g['deck'] = {n: int(float(row[i])) for i, n in deck_i if row[i] not in ('', '0', '0.0')}
    g['sideboard'] = {n: int(float(row[i])) for i, n in side_i if row[i] not in ('', '0', '0.0')}
    for c, v in g.items():
        if isinstance(v, str) and ('turn_' in c or c.startswith(('opening_hand', 'candidate_hand'))) and 'abilities' not in c:
            ids.update(t for t in v.split('|') if t.isdigit())
    games.append(g)

cards = {}
with open(a.cards, newline='') as f:
    for row in csv.DictReader(f):
        if row['id'] in ids:
            cards[row['id']] = {k: row[k] for k in ('name', 'expansion', 'types', 'mana_value', 'rarity')}
miss = sorted(i for i in ids if i not in cards)

with gzip.open(a.out + '.jsonl.gz', 'wt') as f:
    for g in games:
        f.write(json.dumps(g, separators=(',', ':')) + '\n')
with open(a.out + '.cards.json', 'w') as f:
    json.dump(cards, f, indent=0, sort_keys=True)
turns = [int(float(g.get('num_turns', 0))) for g in games]
with open(a.out + '.stats.txt', 'w') as f:
    f.write(f"rows_read={seen} eligible={kept} sampled={len(games)} seed={a.seed} min_wr={a.min_wr} min_games={a.min_games} event={a.event}\n")
    f.write(f"turns_median={sorted(turns)[len(turns)//2] if turns else 0} turns_ge8={sum(t >= 8 for t in turns)}\n")
    f.write(f"card_ids={len(ids)} mapped={len(cards)} unmapped={len(miss)} unmapped_examples={miss[:20]}\n")
    f.write(f"won_share={sum(g.get('won') == 'True' for g in games) / max(1, len(games)):.3f}\n")
    f.write("win_rate_bucket_hist=" + json.dumps(dict(sorted(wr_hist.items()))) + "\n")
print(open(a.out + '.stats.txt').read())

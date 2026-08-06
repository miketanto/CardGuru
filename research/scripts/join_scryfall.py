#!/usr/bin/env python3
"""Join Forge card faces to the canonical card DB (MTGJSON-derived index from
taw/magic-search-engine) and measure coverage in both directions."""
import json, re, unicodedata
from collections import Counter

INDEX = '/home/user/mse/index/index.json'
CARDS = '/home/user/CardGuru/research/data/cards.jsonl'

def norm(name):
    s = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()
    return s.lower().strip()

db = json.load(open(INDEX))['cards']
db_names = {norm(n): n for n in db}
print("canonical cards:", len(db))

forge = [json.loads(l) for l in open(CARDS)]
forge_names = {}
for c in forge:
    if c['name']:
        forge_names.setdefault(norm(c['name']), c)
print("forge faces:", len(forge), "unique names:", len(forge_names))

matched = set(forge_names) & set(db_names)
forge_only = set(forge_names) - set(db_names)
db_only = set(db_names) - set(forge_names)
print(f"matched: {len(matched)}")
print(f"forge-only (not in canonical db): {len(forge_only)}")
print(f"db-only (not scripted in Forge): {len(db_only)}")

# What kind of cards are missing from Forge?
missing_by_layout = Counter()
missing_sample = []
funny = 0
for n in db_only:
    rec = db[db_names[n]]
    lay = rec.get('l', '?')
    missing_by_layout[lay] += 1
    # un-set / acorn detection: printings only in funny sets
    sets_ = [p[0] for p in rec.get('*', [])]
    FUNNY = {'ugl','unh','ust','und','unf','hho','h17','htr','ptg','cmb1','cmb2','mb2','past','pastx','30a'}
    if sets_ and all(s in FUNNY for s in sets_):
        funny += 1
    elif len(missing_sample) < 40:
        missing_sample.append(db_names[n])
print("missing by layout:", dict(missing_by_layout.most_common()))
print("missing but funny/acorn-only:", funny)
print("sample of real missing cards:", missing_sample[:40])

# forge-only sample (naming mismatches vs genuinely extra)
print("forge-only sample:", [forge_names[n]['name'] for n in list(forge_only)[:30]])
EOF_MARKER = None

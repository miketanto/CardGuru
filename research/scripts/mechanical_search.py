#!/usr/bin/env python3
"""Prototype mechanical search over the Forge-derived ability graph.

Three demo queries Scryfall's syntax cannot express structurally:

Q1  Cards with a combat-damage-to-a-player trigger whose effect chain creates
    a token (subgraph: T[DamageDone, CombatDamage, ValidTarget~Player]
    -Execute->...-SubAbility->* reaches api=Token).

Q2  "Impulse exile": an effect chain that exiles card(s) from the top of the
    library AND grants a may-play/may-cast continuous effect for them
    (chain reaches a Dig/DigUntil/Mill node with DestinationZone Exile, and a
    Continuous MayPlay static hangs off the same chain).

Q3  Cost-structure query: activated abilities whose COST includes sacrificing
    a creature and whose effect ADDS MANA (api=Mana or ManaReflected).
    Scryfall cannot separate cost text from effect text.
"""
import json
from collections import defaultdict

CARDS = '/home/user/CardGuru/research/data/cards.jsonl'

def load():
    for line in open(CARDS):
        yield json.loads(line)

def adjacency(card):
    adj = defaultdict(list)
    for e in card['edges']:
        adj[e['src']].append((e['dst'], e['type']))
    return adj

def reachable(card, start_id, adj=None):
    """All node ids reachable from start following any edge."""
    adj = adj or adjacency(card)
    seen, stack = set(), [start_id]
    while stack:
        cur = stack.pop()
        if cur in seen: continue
        seen.add(cur)
        for dst, _ in adj.get(cur, []):
            stack.append(dst)
    return seen

def nodes_by_id(card):
    return {n['id']: n for n in card['nodes']}

# ---------------------------------------------------------------- Q1
def q1(card):
    nid = nodes_by_id(card)
    adj = adjacency(card)
    for n in card['nodes']:
        if n['kind'] != 'T': continue
        p = n.get('params', {})
        if p.get('Mode') not in ('DamageDone', 'DamageDoneOnce'): continue
        if p.get('CombatDamage') != 'True': continue
        if 'Player' not in str(p.get('ValidTarget', '')): continue
        for rid in reachable(card, n['id'], adj):
            t = nid.get(rid, {})
            if t.get('api') == 'Token':
                return True
    return False

# ---------------------------------------------------------------- Q2
def q2(card):
    nid = nodes_by_id(card)
    adj = adjacency(card)
    # roots: any ability-line node or triggered/activated entry point
    roots = [n['id'] for n in card['nodes'] if n['kind'] in ('A', 'T', 'S', 'R')]
    for r in roots:
        reach = reachable(card, r, adj)
        has_exile_from_lib = False
        has_mayplay = False
        for rid in reach:
            n = nid.get(rid, {})
            p = n.get('params', {})
            api = n.get('api')
            if api in ('Dig', 'DigUntil', 'Mill', 'ChangeZone'):
                dest = str(p.get('DestinationZone', p.get('Destination', '')))
                origin = str(p.get('Origin', 'Library' if api in ('Dig','DigUntil','Mill') else ''))
                if 'Exile' in dest and 'Library' in (origin or 'Library'):
                    has_exile_from_lib = True
            if p.get('MayPlay') == 'True' and p.get('Mode') == 'Continuous':
                has_mayplay = True
        if has_exile_from_lib and has_mayplay:
            return True
    return False

# ---------------------------------------------------------------- Q3
def q3(card):
    for n in card['nodes']:
        if n.get('apiKind') != 'AB': continue
        if n.get('api') not in ('Mana', 'ManaReflected'): continue
        cost = str(n.get('params', {}).get('Cost', ''))
        if 'Sac<' in cost and ('Creature' in cost or 'CARDNAME' in cost and 'Creature' in str(card.get('types',''))):
            return True
    return False

def run(name, pred, expect=()):
    hits = []
    for card in load():
        try:
            if pred(card):
                hits.append(card['name'])
        except Exception:
            pass
    hits = sorted(set(hits))
    print(f"\n=== {name}: {len(hits)} cards")
    print(hits[:50])
    for e in expect:
        print(f"  expect '{e}':", 'HIT' if e in hits else 'MISS')
    return hits

if __name__ == '__main__':
    r1 = run("Q1 combat-damage-to-player trigger that creates a token", q1,
             expect=('Ragavan, Nimble Pilferer', 'Brazen Freebooter', 'Old Gnawbone'))
    r2 = run("Q2 impulse exile: exile from library + may play/cast it", q2,
             expect=('Ragavan, Nimble Pilferer', 'Light Up the Stage', 'Outpost Siege'))
    r3 = run("Q3 activated ability: sacrifice-a-creature cost that adds mana", q3,
             expect=('Phyrexian Altar', 'Ashnod\'s Altar', 'Thermopod'))
    json.dump({'q1': r1, 'q2': r2, 'q3': r3},
              open('/home/user/CardGuru/research/data/mech_search_results.json', 'w'), indent=1)

"""L17 step 3a: turn 17Lands DSK games into rebuild specs for L17Rebuild.java.

  python3 rl/l17/build_specs.py OUT.tsv [--games 0-19 | --sample 200 --seed 17 | --all]

Spec format (tab separated, one block per game, seats: U = logged user, O = opponent):
  G  idx  userIsA(1/0)  lastGameTurn
  H  U|O  name|name|...           starting hand
  L  U|O  name|name|...           library, TOP FIRST
  A  turn seat STEP KIND name      forced play; KIND = LAND or CAST (in list order)
  K  turn seat name|name           attackers the seat declares on that game turn
  B  turn defSeat blockers blocked killedDef killedAtk   (combat, '|' lists)
  D  turn U name|name              logged draws of that turn, stacked on top at upkeep
  E
Player A always starts (XMage test framework); game turn 1 = A's first turn.
Order rule within a turn (not logged): land first, then casts by ascending mana
value (ties by name). Instants: DECLARE_BLOCKERS if the active seat attacked
that turn, else PRECOMBAT_MAIN (own turn) / END_TURN (other seat's turn).
"""
import gzip
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'l17_dsk')
BASIC = {'W': 'Plains', 'U': 'Island', 'B': 'Swamp', 'R': 'Mountain', 'G': 'Forest'}
DECK_SIZE = 40


def load():
    cards = json.load(open(os.path.join(DATA, 'DSK_top2000.cards.json'), encoding='utf-8'))
    games = [json.loads(l) for l in gzip.open(os.path.join(DATA, 'DSK_top2000.jsonl.gz'))]
    return cards, games


def ids(g, key):
    v = g.get(key)
    if not v or not isinstance(v, str):
        return []
    return [x for x in v.split('|') if x]


class Namer:
    def __init__(self, cards):
        self.cards = cards

    def name(self, i):
        c = self.cards.get(i)
        return c['name'] if c else None

    def mv(self, i):
        c = self.cards.get(i)
        try:
            return float(c['mana_value']) if c else 0.0
        except ValueError:
            return 0.0

    def is_token(self, i):
        c = self.cards.get(i)
        return c is None or c.get('rarity') == 'token'

    def is_instant(self, i):
        c = self.cards.get(i)
        return bool(c) and 'Instant' in c['types']

    def names(self, lst):
        return [n for n in (self.name(i) for i in lst) if n]


LIST_KEYS = ('eot_user_lands_in_play', 'eot_oppo_lands_in_play', 'eot_user_cards_in_hand',
             'eot_user_creatures_in_play', 'eot_oppo_creatures_in_play', 'lands_played', 'cards_drawn')


def turn_exists(g, side, n):
    """Numeric columns (life, mana, damage) are filled for all 30 turns; a side-turn
    that did not happen has eot life 0.0/0.0 and no card lists (checked on the data)."""
    if n > int(g['num_turns']):
        return False
    p = f'{side}_turn_{n}_'
    if any(p + k in g for k in LIST_KEYS):
        return True
    try:
        return not (float(g.get(p + 'eot_user_life', 0)) == 0 and float(g.get(p + 'eot_oppo_life', 0)) == 0)
    except ValueError:
        return False


def game_turn(side, n, user_is_a):
    a_side = 'user' if user_is_a else 'oppo'
    return 2 * n - 1 if side == a_side else 2 * n


def on_play(g):
    """on_play is stored as the string 'True'/'False' (bool('False') is True)."""
    v = g.get('on_play')
    return v is True or str(v).strip().lower() in ('true', '1', '1.0')


def build(idx, g, nm, rng):
    user_is_a = on_play(g)
    seat = {'user': 'U', 'oppo': 'O'}
    nt = int(g['num_turns'])
    lines = []
    acts, atks, blocks, draws, eots, eotc, kills, seen = [], [], [], [], [], [], [], []
    prev_perm = {}
    opp_seq = []  # opponent card instances in play order (for its hand/library)
    last = 0
    for n in range(1, 31):
        for side in ('user', 'oppo'):
            p = f'{side}_turn_{n}_'
            if not turn_exists(g, side, n):
                continue
            t = game_turn(side, n, user_is_a)
            last = max(last, t)
            other = 'oppo' if side == 'user' else 'user'
            attackers = ids(g, p + 'creatures_attacked')
            # active seat plays
            own = []
            for i in ids(g, p + 'lands_played'):
                own.append((0, 0.0, 'PRECOMBAT_MAIN', 'LAND', i))
            for key in ('creatures_cast', 'non_creatures_cast', f'{side}_instants_sorceries_cast'):
                for i in ids(g, p + key):
                    step = 'PRECOMBAT_MAIN'
                    if nm.is_instant(i) and attackers:
                        step = 'DECLARE_BLOCKERS'
                    own.append((1, nm.mv(i), step, 'CAST', i))
            order = {'PRECOMBAT_MAIN': 0, 'DECLARE_BLOCKERS': 1, 'END_TURN': 2}
            own.sort(key=lambda x: (order[x[2]], x[0], x[1], nm.name(x[4]) or ''))
            for _, _, step, kind, i in own:
                if not nm.is_token(i):
                    acts.append((t, seat[side], step, kind, nm.name(i)))
                    if side == 'oppo':
                        opp_seq.append(nm.name(i))
            # the other seat's instants on this turn
            for i in ids(g, p + f'{other}_instants_sorceries_cast'):
                if not nm.is_token(i):
                    step = 'DECLARE_BLOCKERS' if attackers else 'END_TURN'
                    acts.append((t, seat[other], step, 'CAST', nm.name(i)))
                    if other == 'oppo':
                        opp_seq.append(nm.name(i))
            if attackers:
                atks.append((t, seat[side], [n_ or 'TOKEN' for n_ in (nm.name(i) for i in attackers)]))
            blockers = ids(g, p + 'creatures_blocking')
            if blockers:
                blocked = ids(g, p + 'creatures_blocked')
                k_def = ids(g, p + f'{other}_creatures_killed_combat')
                k_atk = ids(g, p + f'{side}_creatures_killed_combat')
                f = lambda l: '|'.join(nm.name(i) or 'TOKEN' for i in l)
                blocks.append((t, seat[other], f(blockers), f(blocked), f(k_def), f(k_atk)))
            # logged end-of-turn lands per seat (used to replay fetch-land sacrifices)
            for who, seat_ in (('user', 'U'), ('oppo', 'O')):
                ln = [nm.name(i) or 'TOKEN' for i in ids(g, p + f'eot_{who}_lands_in_play')]
                eots.append((t, seat_, ln))
                cr = [nm.name(i) for i in ids(g, p + f'eot_{who}_creatures_in_play') if nm.name(i)]
                eotc.append((t, seat_, cr))
                kn = [nm.name(i) for i in ids(g, p + f'{who}_creatures_killed_non_combat') if nm.name(i)]
                if kn:
                    kills.append((t, seat_, kn))
            # everything of the user's the log can see at end of turn (hand + permanents),
            # used by guided mode to steer library searches
            vis = []
            for key in ('eot_user_cards_in_hand', 'eot_user_lands_in_play', 'eot_user_creatures_in_play',
                        'eot_user_non_creatures_in_play'):
                vis += [nm.name(i) for i in ids(g, p + key) if not nm.is_token(i)]
            seen.append((t, vis))
            # permanents that appeared for the NON-active seat without a logged cast:
            # flash casts on the other seat's turn are not logged as casts (only
            # instants/sorceries are). Cast them (Java checks the card has flash).
            prev = prev_perm.get(other)
            now = []
            for key in ('creatures_in_play', 'non_creatures_in_play'):
                now += [i for i in ids(g, p + f'eot_{other}_{key}') if not nm.is_token(i)]
            if prev is not None:
                new = list(now)
                for i in prev:
                    if i in new:
                        new.remove(i)
                for i in new:
                    step = 'DECLARE_BLOCKERS' if attackers else 'END_TURN'
                    acts.append((t, seat[other], step, 'CASTI', nm.name(i)))
                    if other == 'oppo':
                        opp_seq.append(nm.name(i))
            for who in ('user', 'oppo'):
                cur_ = []
                for key in ('creatures_in_play', 'non_creatures_in_play'):
                    cur_ += [i for i in ids(g, p + f'eot_{who}_{key}') if not nm.is_token(i)]
                prev_perm[who] = cur_
            if side == 'user':  # includes turn 1 on the draw
                d = nm.names(ids(g, p + 'cards_drawn'))
                if d:
                    draws.append((t, d))
    # ---- user seat: hand + library (logged draws on top, rest seeded-random, mulligan bottoms last)
    deck = []
    for c, k in (g.get('deck') or {}).items():
        deck += [c] * int(k)
    hand = nm.names(ids(g, 'opening_hand'))
    mull = int(g.get('num_mulligans') or 0)
    cand = nm.names(ids(g, f'candidate_hand_{mull + 1}')) if mull else []
    pool = list(deck)
    for c in hand:
        if c in pool:
            pool.remove(c)
    bottoms = list(cand)
    for c in hand:
        if c in bottoms:
            bottoms.remove(c)
    for c in bottoms:
        if c in pool:
            pool.remove(c)
    top = []
    for t, d in sorted(draws):
        for c in d:
            top.append(c)
            if c in pool:
                pool.remove(c)
    rng.shuffle(pool)
    ulib = top + pool + bottoms
    # ---- opponent seat: its logged cards + basics in its colours as filler
    cols = [BASIC[c] for c in (g.get('opp_colors') or '') if c in BASIC] or ['Plains']
    oh_size = 7 - int(g.get('opp_num_mulligans') or 0)
    filler_n = max(0, DECK_SIZE - len(opp_seq))
    filler = [cols[j % len(cols)] for j in range(filler_n)]
    ohand = opp_seq[:oh_size]
    rest = opp_seq[oh_size:]
    fi = 0
    while len(ohand) < oh_size and fi < len(filler):
        ohand.append(filler[fi]); fi += 1
    olib = rest + filler[fi:]
    lines.append(f'G\t{idx}\t{int(user_is_a)}\t{last}')
    lines.append('H\tU\t' + '|'.join(hand))
    lines.append('L\tU\t' + '|'.join(ulib))
    lines.append('H\tO\t' + '|'.join(ohand))
    lines.append('L\tO\t' + '|'.join(olib))
    for t, s, step, kind, name in sorted(acts, key=lambda a: a[0]):
        lines.append(f'A\t{t}\t{s}\t{step}\t{kind}\t{name}')
    for t, s, names in atks:
        lines.append(f'K\t{t}\t{s}\t' + '|'.join(names))
    for b in blocks:
        lines.append('B\t' + '\t'.join(str(x) for x in b))
    for t, d in draws:
        lines.append(f'D\t{t}\tU\t' + '|'.join(d))
    for t, s, ln in eots:
        lines.append(f'P\t{t}\t{s}\t' + '|'.join(ln))
    for t, s, cr in eotc:
        lines.append(f'Q\t{t}\t{s}\t' + '|'.join(cr))
    for t, s, kn in kills:
        lines.append(f'N\t{t}\t{s}\t' + '|'.join(kn))
    for t, vis in seen:
        lines.append(f'W\t{t}\tU\t' + '|'.join(vis))
    lines.append('E')
    return lines


def select(games, argv):
    if '--all' in argv:
        return list(range(len(games)))
    if '--games' in argv:
        a, b = argv[argv.index('--games') + 1].split('-')
        return list(range(int(a), int(b) + 1))
    if '--sample' in argv:
        k = int(argv[argv.index('--sample') + 1])
        seed = int(argv[argv.index('--seed') + 1]) if '--seed' in argv else 17
        return sorted(random.Random(seed).sample(range(len(games)), k))
    if '--list' in argv:
        return [int(x) for x in argv[argv.index('--list') + 1].split(',')]
    return list(range(20))


def main():
    out = sys.argv[1]
    cards, games = load()
    nm = Namer(cards)
    sel = select(games, sys.argv)
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        for i in sel:
            for line in build(i, games[i], nm, random.Random(1000 + i)):
                f.write(line + '\n')
    print(f'SPECS|games={len(sel)}|out={out}')


if __name__ == '__main__':
    main()

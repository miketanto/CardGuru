"""L17 step 3c/4: compare rebuilt end-of-turn states with the 17Lands log.

  python3 rl/l17/analyze.py SPEC.tsv OUT.tsv --tag TAG [--detail N] [--csv PATH]

Per game: the side-turns of the log in game order; at each, the engine
snapshot (R line) is compared field by field with the logged end-of-turn
state. turns_matched = n-1 where (side, n) is the first side-turn with any
mismatch (num_turns if none). Decisions are counted as labels only in
side-turns strictly before the first mismatch.
Writes rl/l17_dsk/fidelity_games[_TAG].csv and prints the summary.
"""
import collections
import csv
import gzip
import json
import math
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'l17_dsk')
sys.path.insert(0, HERE)
from build_specs import turn_exists, game_turn, on_play  # noqa: E402

FIELDS = ['user_life', 'oppo_life', 'user_lands', 'user_creatures', 'user_noncreatures', 'user_hand', 'oppo_hand']


def wilson(k, n, z=1.96):
    if n == 0:
        return (float('nan'), float('nan'))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def front(n):
    if n is None:
        return ''
    i = n.find(' // ')
    if i >= 0:
        n = n[:i]
    return n.replace('’', "'").strip().lower()


def ids(g, key):
    v = g.get(key)
    if not v or not isinstance(v, str):
        return []
    return [x for x in v.split('|') if x]


def lst(s):
    return [x for x in s.split('|') if x] if s else []


def parse_out(path):
    R = collections.defaultdict(dict)
    F = collections.defaultdict(list)
    T = collections.defaultdict(list)
    X = collections.defaultdict(dict)
    Z = {}
    for line in open(path, encoding='utf-8'):
        f = line.rstrip('\n').split('\t')
        k = f[0]
        if k == 'R':
            g, t = int(f[1]), int(f[2])
            R[g][t] = dict(user_life=int(f[3]), oppo_life=int(f[4]), user_lands=lst(f[5]), user_creatures=lst(f[6]),
                           user_noncreatures=lst(f[7]), user_hand=lst(f[8]), oppo_hand=int(f[9]), over=f[10] == '1')
        elif k == 'F':
            F[int(f[1])].append((int(f[2]), f[3], f[4], f[5], f[6]))
        elif k == 'T':
            T[int(f[1])].append((int(f[2]), f[3], f[4], int(f[5])))
        elif k == 'X':
            X[int(f[1])][(int(f[2]), f[3])] = (int(f[4]), int(f[5]))
        elif k == 'Z':
            Z[int(f[1])] = (f[2], int(f[3]) if len(f) > 3 and f[3].isdigit() else 0)
    return R, F, T, X, Z


def logged_state(g, side, n, cards):
    p = f'{side}_turn_{n}_'

    def names(key):
        out = []
        for i in ids(g, p + key):
            c = cards.get(i)
            out.append(front(c['name']) if c else 'TOKEN')
        return out

    def num(key):
        try:
            return float(g.get(p + key, 0))
        except ValueError:
            return float('nan')
    return dict(user_life=num('eot_user_life'), oppo_life=num('eot_oppo_life'),
                user_lands=names('eot_user_lands_in_play'), user_creatures=names('eot_user_creatures_in_play'),
                user_noncreatures=names('eot_user_non_creatures_in_play'), user_hand=names('eot_user_cards_in_hand'),
                oppo_hand=num('eot_oppo_cards_in_hand'))


def strip_fd(l):
    """Engine names carry 'FD:' (face-down) and 'tok:' (token) prefixes; the log names both by card."""
    out = []
    for x in l:
        if x.startswith('FD:'):
            x = x[3:]
        if x.startswith('tok:'):
            x = x[4:]
        out.append(x)
    return out


def diff(field, log, eng):
    if field in ('user_life', 'oppo_life', 'oppo_hand'):
        return None if float(log) == float(eng) else f'log={log:g} engine={eng}'
    a, b = collections.Counter(log), collections.Counter(strip_fd(eng))
    if a == b:
        return None
    lo, eo = a - b, b - a
    # an unmapped log id (assumed token) may pair with any leftover engine token;
    # a logged '[face-down card]' may pair with any leftover engine face-down permanent
    for log_key, marker in (('TOKEN', 'tok:'), ('[face-down card]', 'FD:')):
        ex = collections.Counter(strip_fd([x for x in eng if marker in x]))
        spare = eo & ex
        k = min(lo.get(log_key, 0), sum(spare.values()))
        if k:
            lo[log_key] -= k
            for name in list(spare.elements())[:k]:
                eo[name] -= 1
            lo, eo = +lo, +eo
    if not lo and not eo:
        return None
    return f'log_only={sorted(lo.elements())} engine_only={sorted(eo.elements())}'


def main():
    spec_path, out_path = sys.argv[1], sys.argv[2]
    tag = sys.argv[sys.argv.index('--tag') + 1] if '--tag' in sys.argv else 'run'
    detail = int(sys.argv[sys.argv.index('--detail') + 1]) if '--detail' in sys.argv else 0
    csv_path = (sys.argv[sys.argv.index('--csv') + 1] if '--csv' in sys.argv
                else os.path.join(DATA, f'fidelity_games_{tag}.csv'))
    cards = json.load(open(os.path.join(DATA, 'DSK_top2000.cards.json'), encoding='utf-8'))
    games = [json.loads(l) for l in gzip.open(os.path.join(DATA, 'DSK_top2000.jsonl.gz'))]
    cov = {}
    cov_path = os.path.join(DATA, 'coverage_games.csv')
    if os.path.exists(cov_path):
        for r in csv.DictReader(open(cov_path, encoding='utf-8')):
            cov[int(r['game'])] = int(r['both_covered'])
    sel = [int(l.split('\t')[1]) for l in open(spec_path, encoding='utf-8') if l.startswith('G\t')]
    R, F, T, X, Z = parse_out(out_path)
    rows = []
    first_field = collections.Counter()
    fields_at_first = collections.Counter()
    fail_reasons = collections.Counter()
    fail_at_mismatch = collections.Counter()
    examples = collections.defaultdict(list)
    for gi in sel:
        if gi not in Z:
            continue
        g = games[gi]
        nt = int(g['num_turns'])
        uisa = on_play(g)
        a_side = 'user' if uisa else 'oppo'
        seq = []
        for n in range(1, nt + 1):
            for side in (a_side, 'oppo' if a_side == 'user' else 'user'):
                if turn_exists(g, side, n):
                    seq.append((game_turn(side, n, uisa), side, n))
        seq.sort()
        snaps = R.get(gi, {})
        over_at = min((t for t, s in snaps.items() if s['over']), default=None)
        first = None
        for t, side, n in seq:
            log = logged_state(g, side, n, cards)
            eng = snaps.get(t)
            if eng is None:
                why = ('engine_game_over' if over_at is not None and over_at < t
                       else 'engine_error' if Z[gi][0] != 'ok' else 'no_snapshot')
                first = (t, side, n, why, [why], {})
                break
            bad = [(f, diff(f, log[f], eng[f])) for f in FIELDS]
            bad = [(f, d) for f, d in bad if d]
            if bad:
                first = (t, side, n, bad[0][0], [f for f, _ in bad], dict(bad))
                break
        matched = nt if first is None else first[2] - 1
        first_t = first[0] if first else 10 ** 6
        # labels / ambiguity (user seat)
        tset = {(tt, name): flag for tt, seat, name, flag in T.get(gi, []) if seat == 'U'}
        amb_all = amb_m = 0
        lab = collections.Counter()
        unamb = collections.Counter()
        for t, side, n in seq:
            p = f'{side}_turn_{n}_'
            in_m = t < first_t
            if side == 'user':
                acts = ids(g, p + 'lands_played') + ids(g, p + 'creatures_cast') + ids(g, p + 'non_creatures_cast') + ids(g, p + 'user_instants_sorceries_cast')
                amb = len(set(acts)) >= 2
                amb_all += amb
                if in_m:
                    amb_m += amb
                    nl = len(ids(g, p + 'lands_played'))
                    lab['land'] += nl
                    unamb['land'] += 0 if amb else nl
                    for i in acts[nl:]:
                        lab['spell'] += 1
                        nm = cards.get(i, {}).get('name', '')
                        if not amb and not tset.get((t, nm), 0):
                            unamb['spell'] += 1
                    na = len(ids(g, p + 'creatures_attacked'))
                    lab['attack'] += na
                    unamb['attack'] += na
            else:
                if in_m:
                    for i in ids(g, p + 'user_instants_sorceries_cast'):
                        lab['spell'] += 1
                        nm = cards.get(i, {}).get('name', '')
                        if not tset.get((t, nm), 0):
                            unamb['spell'] += 1
                    nb = len(ids(g, p + 'creatures_blocking'))
                    lab['block'] += nb
                    x = X.get(gi, {}).get((t, 'U'))
                    if x and x[0] == 1:
                        unamb['block'] += nb
        tg_all = sum(1 for tt, seat, name, flag in T.get(gi, []) if seat == 'U' and flag)
        tg_m = sum(1 for tt, seat, name, flag in T.get(gi, []) if seat == 'U' and flag and tt < first_t)
        fails_before = [f for f in F.get(gi, []) if f[0] <= first_t]
        for f in F.get(gi, []):
            fail_reasons[(f[1], f[2], f[4].split('@')[0])] += 1
        if first:
            first_field[first[3]] += 1
            for f in first[4]:
                fields_at_first[f] += 1
            for f in fails_before:
                if f[0] >= first_t - 1:
                    fail_at_mismatch[(f[1], f[2], f[4].split('@')[0])] += 1
            if len(examples[first[3]]) < 6:
                examples[first[3]].append((gi, first[1], first[2], first[5].get(first[3], ''),
                                           [f'{x[0]}{x[1]}:{x[2]}:{x[3]}:{x[4]}' for x in fails_before][-4:]))
        rows.append(dict(game=gi, covered=cov.get(gi, 1), turns_logged=nt, turns_matched=matched,
                         first_mismatch_field=first[3] if first else '',
                         first_mismatch_side_turn=f'{first[1]}_{first[2]}' if first else '',
                         mismatch_fields=' '.join(first[4]) if first else '',
                         mismatch_detail=(' ; '.join(f'{k}: {v}' for k, v in first[5].items()) if first else '')[:400],
                         ambiguous_order_turns=amb_all, ambiguous_order_turns_matched=amb_m,
                         targeted_spells=tg_all, targeted_spells_matched=tg_m,
                         labels_land=lab['land'], labels_spell=lab['spell'], labels_attack=lab['attack'],
                         labels_block=lab['block'], unamb_land=unamb['land'], unamb_spell=unamb['spell'],
                         unamb_attack=unamb['attack'], unamb_block=unamb['block'],
                         forced_fails_before_mismatch=len(fails_before), engine_status=Z[gi][0][:80], ms=Z[gi][1]))
        if detail and len(rows) <= detail:
            print(f'DETAIL|game={gi}|nt={nt}|on_play={g["on_play"]}|matched={matched}|first={first[:5] if first else None}')
            if first:
                for k, v in first[5].items():
                    print(f'   {k}: {v}')
                for f in fails_before[-6:]:
                    print('   F', f)
    with open(csv_path, 'w', newline='', encoding='utf-8') as fcsv:
        w = csv.DictWriter(fcsv, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    n = len(rows)
    tm = [r['turns_matched'] for r in rows]
    ge8 = sum(1 for x in tm if x >= 8)
    lo, hi = wilson(ge8, n)
    full = sum(1 for r in rows if not r['first_mismatch_field'])
    lo2, hi2 = wilson(full, n)
    long_games = [r for r in rows if r['turns_logged'] >= 8]
    ge8l = sum(1 for r in long_games if r['turns_matched'] >= 8)
    lo3, hi3 = wilson(ge8l, len(long_games))
    status = collections.Counter(r['engine_status'].split(':')[0] for r in rows)
    print(f'FIDELITY|tag={tag}|games={n}|engine_status={dict(status)}')
    print(f'FIDELITY|median_turns_matched={statistics.median(tm):g}|mean={statistics.mean(tm):.2f}|median_turns_logged={statistics.median(r["turns_logged"] for r in rows):g}')
    print(f'FIDELITY|share_ge8={ge8}/{n}={ge8 / n:.3f} wilson95=[{lo:.3f},{hi:.3f}]')
    print(f'FIDELITY|share_ge8_among_games_ge8_turns_long={ge8l}/{len(long_games)}={ge8l / max(1, len(long_games)):.3f} wilson95=[{lo3:.3f},{hi3:.3f}]')
    print(f'FIDELITY|fully_matched={full}/{n}={full / n:.3f} wilson95=[{lo2:.3f},{hi2:.3f}]')
    print(f'FIDELITY|turns_matched_hist={sorted(collections.Counter(tm).items())}')
    print(f'FIRST_FIELD|{first_field.most_common()}')
    print(f'FIELDS_AT_FIRST|{fields_at_first.most_common()}')
    tot = collections.Counter()
    un = collections.Counter()
    for r in rows:
        for k in ('land', 'spell', 'attack', 'block'):
            tot[k] += r[f'labels_{k}']
            un[k] += r[f'unamb_{k}']
    print('YIELD|per_game ' + ' '.join(f'{k}={tot[k] / n:.2f}' for k in ('land', 'spell', 'attack', 'block'))
          + f' total={sum(tot.values()) / n:.2f}')
    print('YIELD|unambiguous_share ' + ' '.join(f'{k}={un[k] / max(1, tot[k]):.3f}' for k in ('land', 'spell', 'attack', 'block'))
          + f' all={sum(un.values()) / max(1, sum(tot.values())):.3f}')
    amb = sum(r['ambiguous_order_turns'] for r in rows)
    ut = sum(1 for gi in sel if gi in Z for n_ in range(1, int(games[gi]['num_turns']) + 1) if turn_exists(games[gi], 'user', n_))
    print(f'AMBIG|user_turns_more_than_one_order={amb}/{ut}={amb / max(1, ut):.3f}|targeted_user_spells={sum(r["targeted_spells"] for r in rows)}')
    print(f'FAILS_ALL|{fail_reasons.most_common(20)}')
    print(f'FAILS_NEAR_FIRST_MISMATCH|{fail_at_mismatch.most_common(20)}')
    for k, ex in examples.items():
        for e in ex[:3]:
            print(f'EXAMPLE|{k}|game={e[0]}|{e[1]}_{e[2]}|{e[3][:300]}|fails={e[4]}')


if __name__ == '__main__':
    main()

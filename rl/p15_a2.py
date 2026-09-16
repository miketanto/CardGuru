#!/usr/bin/env python3
"""Phase 15 A2 probe 1 / probe 3 (rl/PHASE15-ARCH.md): does the policy network keep
card identity?

Freeze the encoder; take the ENTITY TOKEN of every card in the recorded seat's hand
(zone one-hot = hand, mine = 1, face-up, card id resolved) and linear-probe the card's
mechanical facts from it: the 68 `rl/e2_features.tsv` columns, the five colour bits,
and mana value / power / toughness.

    python3 rl/p15_a2.py --ckpt BC=.../bc.pt --ckpt RAND=.../bc_random.pt \
        --out DIR --tag probe1 REC.jsonl [...]

TWO MEASUREMENTS ARE REPORTED, and the difference between them is the whole point.

(1) `pre` - the probe EXACTLY as pre-registered: fit on training GAMES, scored on
    held-out GAMES, over every informative binary column.  Kept because it is the bar
    that was written down.  It is SATURATED and cannot discriminate: a recording uses
    one deck, so the held-out games contain the SAME card identities the probe was fit
    on (BenchDimir has 38 distinct cards), and a linear map over so few identities is
    memorised exactly.  Worse, mana value, power, toughness, the type flags and the 18
    keyword bits are literally FIELDS OF THE ENTITY ROW (WIRE-V7 2d 10-17, 30-33,
    34-51) that the token is built from, and `v7_net.MLPSkip` exists precisely to keep
    every input field linearly recoverable - so a card-BLIND network scores high on
    them too.  Measured in the smoke: token 1.0000 and frozen embedding 1.0000.

(2) `card` - the informative variant, added 2026-09-16 after the smoke showed (1) is
    saturated, and reported BESIDE the bar rather than instead of it:
      * split by CARD IDENTITY, not by game - the probe is fit on one set of card ids
        and scored on ids it has never seen (plus, separately, on cards of another
        deck entirely, which share no identities at all);
      * scored only on OFF-WIRE columns - the e2 columns the entity row does NOT
        carry (ans_* / api_* / trig_* / has_* / tgt_*: 50 of 68) plus the 5 colour
        bits, which appear nowhere in WIRE-V7 2d.  What survives here can only have
        come through the card embedding, which is what A2 asks about.
    The on-wire columns and the mv / power / toughness R^2 are still printed, labelled
    on-wire, so the contrast is visible in one table.

Controls, on exactly the same entity instances and the same splits:
  EMB   the frozen card_emb_v8 row itself (128-d, pre-adapter) - the CEILING.
  RAND  a clone trained from V7Policy(random_table=True) - the card-blind FLOOR.  That
        table has 1,000 random rows and CardTable clamps ids, so every card id >= 1000
        lands on one shared zero row: the control is card-BLIND, not random-identity.
        `rand_distinct_frac` reports how many probed entities keep a distinct row.

Populations reported for every model and both measurements: all / unseen_card /
unseen_id (card_emb_v8 split.json, held out before the embedding was trained) /
off_deck (cards absent from --baseline-names).
"""
import argparse
import collections
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np                 # noqa: E402
import torch                       # noqa: E402
import v7_obs as V                 # noqa: E402
import v7_policy as P              # noqa: E402
import v7_bc as BC                 # noqa: E402

COLOURS = ["W", "U", "B", "R", "G"]
NUM = ["mv", "power", "toughness"]
# the 18 keyword bits the entity row carries (WIRE-V7 2d 34-51, e2_extract KEYWORDS order)
WIRE_KEYWORDS = ["flying", "haste", "deathtouch", "lifelink", "first_strike", "double_strike",
                 "trample", "vigilance", "flash", "menace", "reach", "defender", "ward",
                 "hexproof", "shroud", "protection", "prowess", "ninjutsu"]


def say(*a):
    print("A2|" + "|".join(str(x) for x in a), flush=True)


def norm(name):
    import unicodedata
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower().strip()


def load_consults(paths, ids, cap=0):
    """Every parseable v7 consult, LABEL-FREE.

    A2 probes the encoder's entity tokens and never uses a teacher label, but
    v7_bc.load drops any consult without `y` - which would exclude the label-free
    wire recordings (rl/artifacts/v7/wire3a/*.jsonl) that are the only source of
    mechanically DIVERSE cards.  That matters: with the probe fit on BenchDimir and
    scored on W0Base alone, only one off-wire column stays informative, because the
    minimal white decks are vanilla creatures and every ans_/api_/trig_ column is
    constant there.  Parsing is v7_obs' own, as in p14_d1.load.
    -> [(game_key, obs)], drop counter
    """
    rows, drop = [], collections.Counter()
    for p in paths:
        ep, hello = 0, None
        with open(p, "rb") as fh:
            for raw in fh:
                if not raw.strip():
                    continue
                try:
                    m = json.loads(raw)
                except ValueError:
                    drop["bad_json"] += 1
                    continue
                t = m.get("t")
                if t == "hello":
                    hello = hello or m
                elif t == "end":
                    ep += 1
                elif t == "consult" and "v7_ent" in m:
                    try:
                        obs = V.compact(V.parse_consult(m, ids, hello))
                    except ValueError:
                        drop["bad_consult"] += 1
                        continue
                    rows.append(((os.path.basename(p), ep), obs))
                    if cap and len(rows) >= cap:
                        return rows, drop
    return rows, drop


def e2_column_names():
    idx = json.load(open(os.path.join(HERE, "artifacts", "cards_v1", "index.json"), encoding="utf-8"))
    return idx["graph_features"]


def load_targets():
    e2 = {}
    with open(os.path.join(HERE, "e2_features.tsv"), encoding="utf-8") as fh:
        dim = int(fh.readline().strip())
        for line in fh:
            if "\t" not in line:
                continue
            nm, vec = line.rstrip("\n").split("\t", 1)
            v = np.fromstring(vec, sep=",", dtype=np.float32)
            if v.shape[0] == dim:
                e2[norm(nm)] = v
    import gzip
    fields = {}
    with gzip.open(os.path.join(HERE, "artifacts", "cards_v1", "fields.jsonl.gz"), "rt", encoding="utf-8") as fh:
        for line in fh:
            o = json.loads(line)
            if o.get("kind") != "card":
                continue
            k = norm(o["name"])
            if k in fields:
                continue
            col = np.array([1.0 if c in (o.get("colors") or "") else 0.0 for c in COLOURS], dtype=np.float32)

            def num(x):
                try:
                    return float(x)
                except (TypeError, ValueError):
                    return np.nan
            fields[k] = (col, np.array([num(o.get("mv")), num(o.get("power")), num(o.get("toughness"))],
                                       dtype=np.float32))
    return e2, dim, fields


def collect(net, rows, args, heldout_ids, base_names):
    e2, dim, fields = load_targets()
    dev = args.device
    X, E, YB, YN, G, CID, UN, OFF, NAMES = [], [], [], [], [], [], [], [], []
    distinct = 0
    net.eval()
    with torch.no_grad():
        for s in range(0, len(rows), args.batch):
            chunk = rows[s:s + args.batch]
            b = {k: (v.to(dev) if torch.is_tensor(v) else v)
                 for k, v in V.collate([r[1] for r in chunk]).items()}
            toks = net.build(b)
            bel = net.belief(toks)
            toks = net.belief.attach(toks, bel)
            enc = net.enc(toks, ent_raw=b["ent"])
            ent = enc["ent"].float().cpu().numpy()
            raw = b["ent"].float().cpu().numpy()
            eid = b["ent_id"].cpu().numpy()
            for i, r in enumerate(chunk):
                names = r[1].ent_name
                for j in range(min(len(names), raw.shape[1])):
                    if raw[i, j, 1] < 0.5 or raw[i, j, 7] < 0.5 or raw[i, j, 8] > 0.5:
                        continue
                    cid = int(eid[i, j])
                    k = norm(names[j])
                    if cid < 0 or k not in e2 or k not in fields:
                        continue
                    col, num = fields[k]
                    X.append(ent[i, j])
                    E.append(net.table.table[cid].float().cpu().numpy())
                    YB.append(np.concatenate([e2[k], col]))
                    YN.append(num)
                    G.append(r[0])
                    CID.append(cid)
                    UN.append(1.0 if cid in heldout_ids else 0.0)
                    OFF.append(0.0 if k in base_names else 1.0)
                    NAMES.append(k)
                    distinct += int(cid < getattr(net.table, "n", 0) and net.table.version == "random")
                    if args.max_entities and len(X) >= args.max_entities:
                        break
            if args.max_entities and len(X) >= args.max_entities:
                break
    rd = (distinct / len(X)) if X else float("nan")
    return (np.array(X, np.float64), np.array(E, np.float64), np.array(YB, np.float64),
            np.array(YN, np.float64), G, np.array(CID), np.array(UN), np.array(OFF), NAMES, dim, rd)


def ridge(Xtr, Ytr, lam=1.0):
    mu, sd = Xtr.mean(0), Xtr.std(0)
    sd = np.where(sd < 1e-8, 1.0, sd)
    Z = np.concatenate([(Xtr - mu) / sd, np.ones((len(Xtr), 1))], 1)
    W = np.linalg.solve(Z.T @ Z + lam * np.eye(Z.shape[1]), Z.T @ Ytr)
    return (mu, sd, W)


def apply_ridge(model, X):
    mu, sd, W = model
    return np.concatenate([(X - mu) / sd, np.ones((len(X), 1))], 1) @ W


def score(mb, mn, X, YB, YN, cols, num_ok):
    if len(X) < 5 or not cols:
        return {"n": int(len(X)), "macro_acc": float("nan"), "n_cols": len(cols),
                "r2": {k: float("nan") for k in NUM}}
    pb = apply_ridge(mb, X)
    acc = [float(((pb[:, c] > 0.5) == (YB[:, c] > 0.5)).mean()) for c in cols]
    pn = apply_ridge(mn, X)
    r2 = {}
    for t, name in enumerate(NUM):
        m = num_ok[:, t]
        y = YN[m, t] if m.sum() else np.zeros(0)
        r2[name] = (float(1 - ((pn[m, t] - y) ** 2).mean() / y.var())
                    if m.sum() >= 5 and y.var() > 1e-9 else float("nan"))
    return {"n": int(len(X)), "macro_acc": float(np.mean(acc)), "n_cols": len(cols), "r2": r2}


def informative(YB, tr, te, subset):
    return [c for c in subset
            if 0 < YB[tr, c].sum() < tr.sum() and 0 < YB[te, c].sum() < te.sum()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recordings", nargs="+")
    ap.add_argument("--ckpt", action="append", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--max-entities", type=int, default=60000)
    ap.add_argument("--max-consults", type=int, default=0)
    ap.add_argument("--baseline-names", default="")
    ap.add_argument("--card-holdout", type=float, default=0.25, help="fraction of CARD IDENTITIES held out")
    ap.add_argument("--card-test", choices=["random", "off_deck"], default="random",
                    help="random: a seeded 25 %% of card identities. off_deck: the test set is exactly the "
                         "cards absent from --baseline-names, so the probe is FIT on one deck's cards and "
                         "SCORED on cards it has never seen (A2 probe 3).")
    ap.add_argument("--tag", default="probe1")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    t0 = time.time()
    ids = V.CardIds()

    gf = e2_column_names()
    kw_cols = {i for i, n in enumerate(gf) if any(k in n.lower() for k in WIRE_KEYWORDS)}
    n_e2 = len(gf)
    onwire = sorted(kw_cols)                                   # e2 keyword bits = wire bits 34..51
    offwire = [c for c in range(n_e2) if c not in kw_cols] + [n_e2 + i for i in range(len(COLOURS))]
    say("columns", f"e2={n_e2}", f"on_wire_keyword_cols={len(onwire)}",
        f"off_wire_cols={len(offwire)} (e2 non-keyword + {len(COLOURS)} colour bits)")

    split = json.load(open(os.path.join(HERE, "artifacts", "card_emb_v8", "split.json")))
    heldout_ids = set(int(x) for x in split["heldout_ids"])
    base_names = set()
    if args.baseline_names:
        for line in open(args.baseline_names, encoding="utf-8"):
            if line.startswith("NAME:") or not line.strip():
                continue
            parts = line.strip().split("]", 1)
            if len(parts) == 2:
                base_names.add(norm(parts[1]))
    say("setup", f"heldout_card_ids={len(heldout_ids)}", f"baseline_names={len(base_names)}")

    rows, drop = load_consults(args.recordings, ids, args.max_consults)
    # interleave by source file: --max-entities truncates collection, and without this the
    # first recordings would fill the budget and later decks would contribute no entities
    # at all (the smoke pooled two decks and collected cards from only one).
    by_file = collections.OrderedDict()
    for r in rows:
        by_file.setdefault(r[0][0], []).append(r)
    if len(by_file) > 1:
        streams = list(by_file.values())
        rows = [x for grp in __import__("itertools").zip_longest(*streams) for x in grp if x is not None]
        say("interleaved", f"files={len(streams)}", "sizes=" + ",".join(str(len(s)) for s in streams))
    games = sorted(set(r[0] for r in rows))
    random.Random(0).shuffle(games)
    held_games = set(games[:max(1, int(round(len(games) * 0.1)))])
    say("data", f"consults={len(rows)}", f"games={len(games)}", f"held_games={len(held_games)}",
        f"load_s={time.time() - t0:.0f}")

    out = {"tag": args.tag, "recordings": [os.path.basename(p) for p in args.recordings],
           "games": len(games), "models": {}, "off_wire_cols": len(offwire)}
    shared = {}
    for spec in args.ckpt:
        name, path = spec.split("=", 1)
        if not os.path.exists(path):
            say(name, "MISSING", path)
            continue
        net = P.V7Policy.load(path, device=args.device)
        X, E, YB, YN, G, CID, UN, OFF, NAMES, dim, rd = collect(net, rows, args, heldout_ids, base_names)
        card_emb_version = net.table.version
        del net
        torch.cuda.empty_cache()
        if not len(X):
            say(name, "no entities")
            continue
        # split A: by GAME (the pre-registered one).  split B: by CARD IDENTITY.
        g_tr = np.array([g not in held_games for g in G])
        cards = sorted(set(int(c) for c in CID))
        if args.card_test == "off_deck":
            # fit on the baseline deck's cards, score on cards the probe has never seen
            test_cards = set(int(c) for c, o in zip(CID, OFF) if o > 0.5)
        else:
            shuf = list(cards)
            random.Random(0).shuffle(shuf)
            test_cards = set(shuf[:max(1, int(round(len(shuf) * args.card_holdout)))])
        c_te = np.array([int(c) in test_cards for c in CID])
        c_tr = ~c_te
        if "counts" not in shared:
            shared["counts"] = {"entities": int(len(X)), "distinct_cards": len(cards),
                                "held_game_entities": int((~g_tr).sum()),
                                "test_cards": len(test_cards), "unseen_card_entities": int(c_te.sum()),
                                "unseen_id_entities": int((UN > 0.5).sum()),
                                "off_deck_entities": int((OFF > 0.5).sum()),
                                "distinct_names": len(set(NAMES))}
            shared["pre_cols"] = informative(YB, g_tr, ~g_tr, list(range(YB.shape[1])))
            shared["card_cols"] = informative(YB, c_tr, c_te, offwire)
            shared["card_cols_onwire"] = informative(YB, c_tr, c_te, onwire)
            say("entities", json.dumps(shared["counts"]))
            say("cols_used", f"pre={len(shared['pre_cols'])}",
                f"card_offwire={len(shared['card_cols'])}", f"card_onwire={len(shared['card_cols_onwire'])}")
        num_ok = np.isfinite(YN)
        res = {"card_emb": card_emb_version, "rand_distinct_frac": rd}
        for key, F in (("TOKEN", X), ("EMB", E)):
            # (1) pre-registered: fit on training games, score on held-out games
            mb = ridge(F[g_tr], YB[g_tr])
            mn = ridge(F[g_tr], np.nan_to_num(YN[g_tr]))
            s = score(mb, mn, F[~g_tr], YB[~g_tr], YN[~g_tr], shared["pre_cols"], num_ok[~g_tr])
            res[f"{key}_pre_heldgame"] = s
            say(name, key, "pre|pop=held_game", f"n={s['n']}", f"cols={s['n_cols']}",
                f"macro_acc={s['macro_acc']:.4f}", "r2=" + ",".join(f"{k}:{v:.3f}" for k, v in s["r2"].items()))
            # (2) informative: fit on training CARDS, score on unseen cards / populations
            mb = ridge(F[c_tr], YB[c_tr])
            mn = ridge(F[c_tr], np.nan_to_num(YN[c_tr]))
            for pop, mask in (("unseen_card", c_te), ("unseen_id", c_te & (UN > 0.5)),
                              ("off_deck", c_te & (OFF > 0.5)), ("seen_card", c_tr)):
                s_off = score(mb, mn, F[mask], YB[mask], YN[mask], shared["card_cols"], num_ok[mask])
                s_on = score(mb, mn, F[mask], YB[mask], YN[mask], shared["card_cols_onwire"], num_ok[mask])
                res[f"{key}_card_{pop}"] = {"off_wire": s_off, "on_wire": s_on}
                say(name, key, f"card|pop={pop}", f"n={s_off['n']}",
                    f"offwire_acc={s_off['macro_acc']:.4f}", f"onwire_acc={s_on['macro_acc']:.4f}",
                    "r2=" + ",".join(f"{k}:{v:.3f}" for k, v in s_off["r2"].items()))
        out["models"][name] = res
    out["counts"] = shared.get("counts", {})
    out["cols_used"] = {k: len(shared.get(k, [])) for k in ("pre_cols", "card_cols", "card_cols_onwire")}
    with open(os.path.join(args.out, f"a2_{args.tag}.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    say("done", f"wall_s={time.time() - t0:.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

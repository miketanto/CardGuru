#!/usr/bin/env python3
"""Gate 5b: the faithfulness probe (rl/probes/faithfulness.py) on REAL recorded
consults (rl/record_5b.sh) after L3 (the token builders, rl/v7_net.py) and
after L4 (the state-graph encoder, rl/v7_encoder.py, woken as in
rl/v7_leak_real.py: at init the encoder is an identity, so an unwoken L4
result would just repeat the L3 result).

    python3 rl/v7_faith_real.py REC.jsonl [REC.jsonl ...] [--layers 2] [--cap 40000]
        [--out rl/artifacts/v7/5b_faith.json] [--md rl/artifacts/v7/5b_faith.md]

Pre-registered thresholds (written before the first run on real dumps):
  fields after L3: binary/cat accuracy >= 0.99, real R^2 >= 0.95 (the MLPSkip
    linear skip of 4b makes exact carry a property of the architecture);
  fields after L4: binary/cat >= 0.95, real R^2 >= 0.90 (woken blocks mix
    tokens; the residual keeps the field);
  edges (L4 only - L3 tokens do not see edges by construction, they enter the
    net at L4): balanced held-out accuracy >= 0.90 per edge type from a linear
    readout of [x_i, x_j, x_i * x_j]; positives = ordered pairs carrying the
    type, negatives = as many edge-free pairs from the same consults; the
    encoder's edge-bias rows are woken too (zero at init: an edge would
    change nothing and the probe would be vacuous);
  consult-level, after L4, from [game token | masked mean of the sequence]:
    remaining-deck count per name R^2 >= 0.90 (mean over names, rows = the
    consults of the recordings whose opponent deck holds the name),
    instant-speed threat count (distinct remaining instant-speed cards
    castable with their open mana now) R^2 >= 0.90, known-card set per name
    accuracy >= 0.95 or "not exercised".  After L3 the multiset is the token
    set itself (identity + count on the same token: the per-token fields).
A field is "not exercised" (no verdict) when fewer than 20 rows over the
whole set carry a value other than the majority (binary/cat) or the field
is constant (real).  Entity readouts are per zone (4b builds one MLPSkip per
zone, so one linear map across zones is not implied by the architecture);
the reported score is the held-out-row-weighted score over zones with
enough rows.  Identity (the card id from the card table, a cat field) is
probed on entity, opponent-hand and remaining-deck tokens.
Nothing here writes to the model.
"""
import argparse
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "probes"))
import torch                       # noqa: E402
import wire_validate as W          # noqa: E402
import v7_obs as V                 # noqa: E402
import v7_net as N                 # noqa: E402
import v7_encoder as E             # noqa: E402
import faithfulness as F           # noqa: E402

KW = ["flying", "haste", "deathtouch", "lifelink", "first_strike", "double_strike", "trample", "vigilance",
      "flash", "menace", "reach", "defender", "ward", "hexproof", "shroud", "protection", "prowess", "ninjutsu"]
ZONE = ["battlefield", "hand", "stack", "graveyard", "exile", "library_known", "command"]
STEP = ["upkeep", "draw", "main1", "decl_att", "decl_blk", "combat_dmg", "main2", "end"]
CT = ["PASS", "LAND", "SPELL", "ACTIVATE", "TARGET", "ATTACK", "BLOCK", "OTHER"]
EDGE = ["blocks", "blocked_by", "attacking_player", "targets", "controls", "attached_to", "can_block", "stack_above",
        "refers_to", "referred_by"]
OACT = ["cast", "activate", "attack", "block", "declined_block", "passed_mana_up", "other"]


def _b(names):
    return [(n, "binary") for n in names]


def _r(names):
    return [(n, "real") for n in names]


GAME_FIELDS = _r(["turn"]) + _b(["i_am_active"]) + _b(["step_" + s for s in STEP]) + _b(["priority"]) + _r(["stack_depth"]) \
    + _b(["dtype_" + c for c in CT]) + _r(["n_cand", "consults_so_far"]) + _b(["my_deck_open", "opp_deck_open"])
PLAYER_FIELDS = _r(["life", "poison", "hand", "library", "graveyard", "exile", "pool_W", "pool_U", "pool_B", "pool_R",
                    "pool_G", "pool_C", "untapped_sources", "lands", "drawn_this_turn", "permanents"])
ENT_FIELDS = _b(["zone_" + z for z in ZONE]) + _b(["mine", "face_down"]) + _r(["stack_pos"]) \
    + _r(["power", "toughness", "damage", "tough_left", "printed_power", "printed_tough", "loyalty", "mv",
          "ctr_p1p1", "ctr_m1m1", "ctr_loyalty", "ctr_other"]) \
    + _b(["tapped", "sick", "attacking", "blocking", "entered", "token"]) + _r(["turns_on_bf"]) \
    + _b(["creature", "land", "instant", "sorcery", "other_perm"]) + _b(["kw_" + k for k in KW]) \
    + _b(["castable"]) + _r(["mana_left_if_cast", "legal_targets"]) + _b(["can_attack", "can_block", "lethal_as_is"]) \
    + _r(["stack_X", "stack_modes"]) + _b(["stack_mine", "stack_is_ability"]) + [("reserved62", None), ("reserved63", None)]
# candidate afterstate slots are overloaded per type (WIRE §2f): one target column per (group, slot)
CAND_GROUPS = {
    "LSA": ([1, 2, 3], _r(["mana_left_after", "targets_legal"]) + _b(["instant_speed", "sorcery_speed", "flash"])
            + _r(["stack_above_n", "X_chosen"])),
    "TARGET": ([4], _b(["is_player", "is_me"]) + _r(["life_if_player"]) + _b(["is_creature"]) + _r(["power", "toughness"])
               + _b(["mine"])),
    "ATTACK": ([5], _r(["damage_dealt", "their_kills", "my_losses"]) + _b(["lethal"])
               + _r(["attackers_used", "opp_life_after", "bodies_retained", "power_retained", "tough_retained",
                     "crack_back", "my_life_after"])),
    "BLOCK": ([6], _r(["damage_taken", "attackers_killed", "value_killed", "blockers_lost", "value_lost"])
              + _b(["defender_dies"]) + _r(["blockers_used", "life_after"])),
}
OPP_HAND_FIELDS = _b(["origin_opening", "origin_drawn", "origin_returned", "origin_other"]) + _r(["age"]) \
    + _b(["known", "seen"]) + [("reserved7", None)]
OPP_DECK_FIELDS = _r(["count", "fraction"]) + _b(["castable_now"]) + _r(["mv"]) + _b(["instant_speed"]) + [("reserved5", None)]
OPP_ACT_FIELDS = _b(["act_" + a for a in OACT]) + _r(["consult_age"])

THR = {"L3": {"binary": 0.99, "cat": 0.99, "real": 0.95}, "L4": {"binary": 0.95, "cat": 0.95, "real": 0.90},
       "edge": 0.90, "consult": {"real": 0.90, "binary": 0.95}}


def wake(enc, gen):
    for blk in enc.blocks:
        for lin in (blk.att.out, blk.ffn[-1]):
            with torch.no_grad():
                lin.weight.copy_(torch.randn(lin.weight.shape, generator=gen) * 0.05)
        with torch.no_grad():
            blk.att.bias_rows.copy_(torch.randn(blk.att.bias_rows.shape, generator=gen) * 1.0)
    return enc


def load(paths):
    """-> hello, list of (msg, gid, file_idx); games delimited by the recording's 'end' messages."""
    hello, msgs, deck_names = None, [], defaultdict(set)
    for fi, p in enumerate(paths):
        game = 0
        for raw in open(p, "rb"):
            if not raw.strip():
                continue
            m = json.loads(raw)
            t = m.get("t")
            if t == "hello":
                hello = hello or m
            elif t == "end":
                game += 1
            elif t == "consult" and "v7_ent" in m:
                msgs.append((m, fi * 1000 + game, fi))
                deck_names[fi].update(m.get("v7_opp_deck_name", []))
    return hello, msgs, deck_names


def exercised(y, kind):
    ok = ~np.isnan(y)
    if ok.sum() == 0:
        return 0
    v = y[ok]
    if kind == "real":
        return int((np.abs(v) > 1e-9).sum()) if v.std() > 1e-9 else 0
    vals, cnt = np.unique(v, return_counts=True)
    return int(cnt.sum() - cnt.max())


def run_probe(X, Y, groups, fields, thr, min_rows=200):
    """fields: list of (name, kind|None). Returns {name: {...}}; kind None = reserved (skipped)."""
    out = {}
    idx = [(j, n, k) for j, (n, k) in enumerate(fields) if k is not None]
    if X.shape[0] < min_rows:
        for _, n, k in idx:
            out[n] = {"kind": k, "exercised": 0, "score": None, "chance": None, "pass": None, "n_test": 0, "note": "too few rows"}
        return out
    kinds = [k for _, _, k in idx]
    Ysub = np.stack([Y[:, j] for j, _, _ in idx], 1)
    ex = [exercised(Ysub[:, c], k) for c, k in enumerate(kinds)]
    # exercised on the held-out games too (the same split faithfulness.probe makes):
    # an R^2 on a held-out set with no variance is not a measurement
    _, te = F._split_by_group(np.asarray(groups))
    ex_te = [exercised(Ysub[te, c], k) for c, k in enumerate(kinds)]
    keep = [c for c, e in enumerate(ex) if e >= 20 and ex_te[c] >= 10]
    res = F.probe(X, Ysub[:, keep], groups, [kinds[c] for c in keep],
                  thresholds={i: thr[kinds[c]] for i, c in enumerate(keep)}) if keep else {}
    for c, (_, n, k) in enumerate(idx):
        if c in keep:
            r = res[keep.index(c)]
            out[n] = {"kind": k, "exercised": ex[c], "score": r["score"], "chance": r["chance"], "pass": r["pass"], "n_test": r["n_test"]}
        else:
            out[n] = {"kind": k, "exercised": ex[c], "score": None, "chance": None, "pass": None, "n_test": 0, "note": "not exercised"}
    return out


def merge_zones(per_zone):
    """Row-weighted score over zones where the field was exercised."""
    names = set()
    for r in per_zone.values():
        names.update(r)
    out = {}
    for n in names:
        rows = [(z, r[n]) for z, r in per_zone.items() if n in r and r[n]["score"] is not None]
        ex = sum(r[n]["exercised"] for r in per_zone.values() if n in r)
        kind = next(r[n]["kind"] for r in per_zone.values() if n in r)
        if not rows:
            out[n] = {"kind": kind, "exercised": ex, "score": None, "chance": None, "pass": None, "n_test": 0, "note": "not exercised"}
            continue
        w = sum(r["n_test"] for _, r in rows)
        sc = sum(r["score"] * r["n_test"] for _, r in rows) / w
        ch = sum(r["chance"] * r["n_test"] for _, r in rows) / w
        out[n] = {"kind": kind, "exercised": ex, "score": sc, "chance": ch, "pass": all(r["pass"] for _, r in rows),
                  "n_test": w, "zones": {z: round(r["score"], 4) for z, r in rows}}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recordings", nargs="+")
    ap.add_argument("--layers", type=int, default=2)
    ap.add_argument("--cap", type=int, default=40000, help="max rows per token part fed to a probe")
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--out", default=os.path.join(HERE, "artifacts", "v7", "5b_faith.json"))
    ap.add_argument("--md", default=os.path.join(HERE, "artifacts", "v7", "5b_faith.md"))
    args = ap.parse_args()

    hello, msgs, deck_names = load(args.recordings)
    if hello is None or not msgs:
        print("FAITH5B|no v7 consults")
        return 2
    n_games = len({g for _, g, _ in msgs})
    print(f"FAITH5B|consults={len(msgs)}|games={n_games}|files={len(args.recordings)}")

    torch.manual_seed(0)
    gen = torch.Generator().manual_seed(5)
    table = N.CardTable().float()
    build = N.TokenBuilders(table).float().eval()
    enc = wake(E.StateGraphEncoder(layers=args.layers).float().eval(), gen)
    ids = V.CardIds()
    rng = np.random.RandomState(0)

    # collectors: part -> stage -> list of arrays
    X = {s: defaultdict(list) for s in ("L3", "L4")}
    Yc = defaultdict(list)          # part -> targets (stage-independent)
    G = defaultdict(list)           # part -> groups
    ZN = []                         # ent zone per row
    CTY = []                        # cand type per row
    IDS = defaultdict(list)         # part -> identity per row (-1 unknown)
    EX, EY, EG = defaultdict(list), defaultdict(list), defaultdict(list)     # edge type -> pair feats / label / group
    CX3, CX4, CY, CG, CF = [], [], {}, [], []                                 # consult-level
    all_names = sorted(set().union(*deck_names.values())) if deck_names else []
    name_col = {n: i for i, n in enumerate(all_names)}
    CY["deck_count"], CY["known"], CY["threat"] = [], [], []

    for s in range(0, len(msgs), args.batch):
        chunk = msgs[s:s + args.batch]
        obs = [V.parse_consult(m, ids, hello) for m, _, _ in chunk]
        b = V.collate(obs)
        with torch.no_grad():
            toks = build(b)
            out = enc(toks, ent_raw=b["ent"])
            seq3, mask, edges_full, layout = E.StateGraphEncoder.assemble(toks)
            seq4 = out["seq"]
        for i, (m, gid, fi) in enumerate(chunk):
            o = obs[i]
            n, k = o.ent.shape[0], o.cand.shape[0]
            h, d, a = o.opp_hand.shape[0], o.opp_deck.shape[0], o.opp_act.shape[0]
            parts = {"game": (slice(0, 1), o.game.unsqueeze(0)), "players": (slice(0, 2), o.players),
                     "ent": (slice(0, n), o.ent), "cand": (slice(0, k), o.cand),
                     "opp_hand": (slice(0, h), o.opp_hand), "opp_deck": (slice(0, d), o.opp_deck),
                     "opp_act": (slice(0, a), o.opp_act)}
            for name, (sl, y) in parts.items():
                if y.shape[0] == 0:
                    continue
                X["L3"][name].append(toks[name][i, sl].numpy())
                X["L4"][name].append(out[name][i, sl].numpy())
                Yc[name].append(y.numpy())
                G[name].extend([gid] * y.shape[0])
            ZN.extend(o.ent[:, :7].argmax(-1).tolist())
            CTY.extend(o.cand_type.tolist())
            IDS["ent"].extend(o.ent_id.tolist()); IDS["opp_hand"].extend(o.opp_hand_id.tolist()); IDS["opp_deck"].extend(o.opp_deck_id.tolist())
            # edges: full assembled matrix (wire types + refers) on the L4 sequence
            T = int(mask[i].sum())
            ef = edges_full[i, :T, :T].numpy()
            x4 = seq4[i, :T].numpy()
            valid = mask[i, :T].numpy()
            for t in range(1, E.N_EDGE):
                pi, pj = np.nonzero(ef == t)
                if len(pi) == 0:
                    continue
                if len(pi) > 50:
                    sel = rng.choice(len(pi), 50, replace=False); pi, pj = pi[sel], pj[sel]
                zi, zj = np.nonzero((ef == 0) & valid[:, None] & valid[None, :] & ~np.eye(T, dtype=bool))
                if len(zi) == 0:
                    continue
                sel = rng.choice(len(zi), min(len(pi), len(zi)), replace=False); zi, zj = zi[sel], zj[sel]
                for (ii, jj, lab) in [(pi, pj, 1.0), (zi, zj, 0.0)]:
                    EX[t].append(np.concatenate([x4[ii], x4[jj], x4[ii] * x4[jj]], 1))
                    EY[t].extend([lab] * len(ii)); EG[t].extend([gid] * len(ii))
            # consult-level
            mm = mask[i].numpy()
            CX3.append(np.concatenate([seq3[i, 0].numpy(), seq3[i][mm].numpy().mean(0)]))
            CX4.append(np.concatenate([seq4[i, 0].numpy(), seq4[i][mm].numpy().mean(0)]))
            CG.append(gid); CF.append(fi)
            lib = m["v7_players"][1][3] * 60.0
            row = np.full(len(all_names), np.nan)
            for nm in deck_names[fi]:
                row[name_col[nm]] = 0.0
            for j, nm in enumerate(m.get("v7_opp_deck_name", [])):
                r = m["v7_opp_deck"][j]
                row[name_col[nm]] = round(r[1] * lib) if lib > 0 else min(round(r[0] * 4), 4)
            CY["deck_count"].append(row)
            kn = np.full(len(all_names), np.nan)
            for nm in deck_names[fi]:
                kn[name_col[nm]] = 0.0
            for nm in m.get("v7_opp_hand_name", []) or []:
                if nm and nm in name_col:
                    kn[name_col[nm]] = 1.0
            CY["known"].append(kn)
            CY["threat"].append([sum(1.0 for r in m.get("v7_opp_deck", []) if r[2] > 0.5 and r[4] > 0.5)])

    report = {"consults": len(msgs), "games": n_games, "files": args.recordings, "layers": args.layers, "thresholds": THR,
              "stages": {}}
    part_fields = {"game": GAME_FIELDS, "players": PLAYER_FIELDS, "ent": ENT_FIELDS,
                   "opp_hand": OPP_HAND_FIELDS, "opp_deck": OPP_DECK_FIELDS, "opp_act": OPP_ACT_FIELDS}
    ZN, CTY = np.array(ZN), np.array(CTY)
    for stage in ("L3", "L4"):
        thr = THR[stage]
        st = {}
        for part, fields in part_fields.items():
            if not Yc[part]:
                continue
            Xp, Yp, Gp = np.concatenate(X[stage][part]), np.concatenate(Yc[part]), np.array(G[part])
            keep = np.arange(Xp.shape[0])
            if Xp.shape[0] > args.cap:
                keep = np.sort(rng.choice(Xp.shape[0], args.cap, replace=False))
            if part == "ent":
                per_zone = {}
                for z, zn in enumerate(ZONE):
                    rows = keep[ZN[keep] == z]
                    if len(rows) < 200:
                        continue
                    per_zone[zn] = run_probe(Xp[rows], Yp[rows], Gp[rows], fields, thr)
                    idv = np.array(IDS["ent"])[rows].astype(float); idv[idv < 0] = np.nan
                    per_zone[zn].update(run_probe(Xp[rows], idv[:, None], Gp[rows], [("identity", "cat")], thr))
                st[part] = merge_zones(per_zone)
                st[part + "_zone_rows"] = {zn: int((ZN[keep] == z).sum()) for z, zn in enumerate(ZONE)}
            else:
                st[part] = run_probe(Xp[keep], Yp[keep], Gp[keep], fields, thr)
                if part in ("opp_hand", "opp_deck"):
                    idv = np.array(IDS[part])[keep].astype(float); idv[idv < 0] = np.nan
                    st[part].update(run_probe(Xp[keep], idv[:, None], Gp[keep], [("identity", "cat")], thr))
        # candidates: the type one-hot on all rows, then the overloaded slots per group
        Xp, Yp, Gp = np.concatenate(X[stage]["cand"]), np.concatenate(Yc["cand"]), np.array(G["cand"])
        keep = np.arange(Xp.shape[0])
        if Xp.shape[0] > args.cap:
            keep = np.sort(rng.choice(Xp.shape[0], args.cap, replace=False))
        cand = run_probe(Xp[keep], Yp[keep], Gp[keep], _b(["type_" + c for c in CT]), thr)
        for gname, (types, fields) in CAND_GROUPS.items():
            rows = keep[np.isin(CTY[keep], types)]
            pf = [(f"{gname}.{n}", kd) for n, kd in fields]
            if len(rows) < 200:
                for n, _ in pf:
                    cand[n] = {"kind": "-", "exercised": 0, "score": None, "chance": None, "pass": None, "n_test": 0,
                               "note": f"too few rows ({len(rows)})"}
                continue
            cand.update(run_probe(Xp[rows], Yp[rows][:, 8:8 + len(fields)], Gp[rows], pf, thr))
        st["cand"] = cand
        st["cand_type_rows"] = {c: int((CTY == t).sum()) for t, c in enumerate(CT)}
        report["stages"][stage] = st

    # edges (L4)
    ed = {}
    for t in range(1, E.N_EDGE):
        name = EDGE[t - 1]
        if not EX[t]:
            ed[name] = {"exercised": 0, "score": None, "pass": None, "note": "not exercised"}
            continue
        Xe, Ye, Ge = np.concatenate(EX[t]), np.array(EY[t]), np.array(EG[t])
        if Xe.shape[0] > args.cap:
            sel = np.sort(rng.choice(Xe.shape[0], args.cap, replace=False)); Xe, Ye, Ge = Xe[sel], Ye[sel], Ge[sel]
        r = run_probe(Xe, Ye[:, None], Ge, [(name, "binary")], {"binary": THR["edge"]}, min_rows=40)[name]
        r["positives"] = int(Ye.sum())
        ed[name] = r
    report["edges_L4"] = ed

    # consult level
    cons = {}
    CG = np.array(CG)
    for stage, CX in (("L3", np.array(CX3)), ("L4", np.array(CX4))):
        dc = np.array(CY["deck_count"])
        r_names = run_probe(CX, dc, CG, [(n, "real") for n in all_names], THR["consult"], min_rows=40)
        scored = [r["score"] for r in r_names.values() if r["score"] is not None]
        kn = np.array(CY["known"])
        r_known = run_probe(CX, kn, CG, [(n, "binary") for n in all_names], THR["consult"], min_rows=40)
        kn_scored = [r["score"] for r in r_known.values() if r["score"] is not None]
        r_thr = run_probe(CX, np.array(CY["threat"]), CG, [("threat_count", "real")], THR["consult"], min_rows=40)
        cons[stage] = {
            "deck_count": {"names": len(all_names), "names_scored": len(scored),
                           "mean_r2": float(np.mean(scored)) if scored else None, "min_r2": float(np.min(scored)) if scored else None,
                           "pass": bool(scored and np.mean(scored) >= THR["consult"]["real"]),
                           "worst": sorted(((r["score"], n) for n, r in r_names.items() if r["score"] is not None))[:5]},
            "known_set": {"names_exercised": len(kn_scored), "mean_acc": float(np.mean(kn_scored)) if kn_scored else None,
                          "pass": bool(kn_scored and np.min(kn_scored) >= THR["consult"]["binary"]) if kn_scored else None,
                          "note": "not exercised" if not kn_scored else ""},
            "threat_count": r_thr["threat_count"],
        }
    report["consult"] = cons

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(report, open(args.out, "w"), indent=1, default=float)
    write_md(report, args.md)
    # summary line per stage
    ok = True
    for stage in ("L3", "L4"):
        st = report["stages"][stage]
        p = f_ = ne = 0
        fails = []
        for part, res in st.items():
            if not isinstance(res, dict) or part.endswith("_rows"):
                continue
            for n, r in res.items():
                if not isinstance(r, dict) or "pass" not in r:
                    continue
                if r["pass"] is None:
                    ne += 1
                elif r["pass"]:
                    p += 1
                else:
                    f_ += 1; fails.append(f"{part}.{n}={r['score']:.3f}")
        ok &= f_ == 0
        print(f"FAITH5B|{stage}|pass={p}|fail={f_}|not_exercised={ne}|" + (" ".join(fails[:12]) if fails else "-"))
    ef = [f"{n}={r['score']:.3f}" for n, r in ed.items() if r["pass"] is False]
    ok &= not ef
    print(f"FAITH5B|edges_L4|pass={sum(1 for r in ed.values() if r['pass'])}|fail={len(ef)}|not_exercised={sum(1 for r in ed.values() if r['pass'] is None)}|" + (" ".join(ef) or "-"))
    c4 = cons["L4"]
    print(f"FAITH5B|consult_L4|deck_count_mean_r2={c4['deck_count']['mean_r2']}|threat_r2={c4['threat_count']['score']}|known={c4['known_set']['note'] or c4['known_set']['mean_acc']}")
    print(f"FAITH5B|written|{args.out}|{args.md}")
    return 0 if ok else 1


def write_md(report, path):
    L = [f"# 5b faithfulness on real dumps — {report['consults']} consults, {report['games']} games, {len(report['files'])} recordings",
         "", f"Thresholds: `{json.dumps(report['thresholds'])}`", ""]
    for stage in ("L3", "L4"):
        st = report["stages"][stage]
        L += [f"## after {stage}", "", "| part | field | kind | exercised | held-out | chance | n | result |", "|---|---|---|---|---|---|---|---|"]
        for part, res in st.items():
            if part.endswith("_rows"):
                continue
            for n, r in res.items():
                if r.get("score") is None:
                    L.append(f"| {part} | {n} | {r.get('kind','')} | {r.get('exercised',0)} | — | — | {r.get('n_test',0)} | {r.get('note','')} |")
                else:
                    L.append(f"| {part} | {n} | {r['kind']} | {r['exercised']} | {r['score']:.3f} | {r['chance']:.3f} | {r['n_test']} | {'pass' if r['pass'] else '**FAIL**'} |")
        L.append("")
        L.append(f"entity rows by zone: `{st['ent_zone_rows']}`; candidate rows by type: `{st['cand_type_rows']}`")
        L.append("")
    L += ["## edges after L4 (balanced pairs)", "", "| edge | positives | held-out | chance | result |", "|---|---|---|---|---|"]
    for n, r in report["edges_L4"].items():
        if r.get("score") is None:
            L.append(f"| {n} | {r.get('positives', 0)} | — | — | {r.get('note','')} |")
        else:
            L.append(f"| {n} | {r['positives']} | {r['score']:.3f} | {r['chance']:.3f} | {'pass' if r['pass'] else '**FAIL**'} |")
    L += ["", "## consult-level", ""]
    for stage, c in report["consult"].items():
        L.append(f"- after {stage}: remaining-deck count per name mean R² = {c['deck_count']['mean_r2']} (min {c['deck_count']['min_r2']}, "
                 f"{c['deck_count']['names_scored']}/{c['deck_count']['names']} names exercised; worst {c['deck_count']['worst']}); "
                 f"instant-speed threat count R² = {c['threat_count']['score']} (exercised {c['threat_count']['exercised']}); "
                 f"known-card set: {c['known_set']['note'] or c['known_set']['mean_acc']}")
    open(path, "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    sys.exit(main())

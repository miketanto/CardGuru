#!/usr/bin/env python3
"""Gate 5c (belief): rl/v7_belief.py's 4f gates on REAL recorded consults from
the oracle JVM (-Drl.encoderV=7 -Drl.oracle=true); labels from `v7_oe_hand`.

    python3 rl/v7_belief_real.py REC.jsonl ... [--steps 1500] [--device cuda]

Pre-registered before the first run (thresholds fixed here, committed first):
  B1  leak with belief ON: policy logits bit-identical (tol 1e-6, as
      rl/probes/leak.py level 2) under a swap of `oe` / `v7_oe_hand`, with the
      belief features attached, on a woken encoder, >= 200 real consults drawn
      from every recording given.
  B2  stop-gradient on real inputs: after belief.loss(...).backward() on a
      real minibatch every TokenBuilders parameter has grad None / 0 and some
      belief parameter has a non-zero grad.
  B3  held-out slot log-likelihood of the TRUE hand (the pointer over the
      remaining-deck tokens), game-grouped 20 % hold-out, trained on the other
      games: beats uniform-over-remaining by >= 0.3 nats (the 4f margin).
  B4  known slots (identity is on the token): held-out mean pointer mass on the
      true token >= 0.95 (only recordings with returned-to-hand slots carry any;
      "not exercised" below 20 held-out known slots).
  Reported, not gated: the multiset prior log-lik (count_j / sum_k count_k over
  the remaining tokens) - a belief that only learns the counts ties it; beating
  it is Phase 6's question (self-play labels, trained builders, the real card
  table), not 5c's.  P(in hand) BCE vs the base-rate BCE and a rank AUC, likewise.

Labels.  slot_target[h] = the remaining-deck token of the true card in slot h:
a known slot points at its own token; the unknown slots take the true names
not covered by known slots, assigned in deck-token order (the slots are
unordered, so this is one of the equivalent permutations - the pointer loss
is over the per-slot marginal, which the permutation leaves unchanged when
the unknown slots are indistinguishable, as they are up to origin and age).
hand_target[d] = 1 if the token's name is in the true hand.  draw_target = -1
everywhere: the next draw is not on the wire (WIRE §4 carries the hand only),
so l_draw is identically 0 here.  A true name absent from the remaining tokens
is counted and its slot is -1 (excluded).

Card table: random (as rl/v7_leak_real.py); builders untrained; the belief
module sees the builders' tokens through .detach() as in training.  What this
cannot show: that real hidden hands are predictable beyond the multiset prior.
"""
import argparse
import json
import os
import random
import sys
import time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "probes"))
import torch                       # noqa: E402
import v7_obs as V                 # noqa: E402
import v7_net as N                 # noqa: E402
import v7_encoder as E             # noqa: E402
import v7_heads as H               # noqa: E402
import v7_belief as BL             # noqa: E402

THR = {"B1_tol": 1e-6, "B3_margin": 0.3, "B4_mass": 0.95, "B4_min_rows": 20, "B1_min_consults": 200}


def load(paths):
    """-> hello, list of (msg, gid); games delimited by the recording's 'end' messages."""
    hello, msgs = None, []
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
            elif t == "consult" and "v7_oe_hand" in m and "v7_ent" in m:
                msgs.append((m, fi * 1000 + game, fi))
    return hello, msgs


def labels(m, o):
    """-> slot_t [H] long, hand_t [D] float, n_true, n_unmatched."""
    dn = m.get("v7_opp_deck_name", [])
    hn = m.get("v7_opp_hand_name", [])
    true = list(m.get("v7_oe_hand", []))
    idx = {}
    for j, n in enumerate(dn):
        idx.setdefault(n, j)
    H, D = len(hn), len(dn)
    slot_t = torch.full((H,), -1, dtype=torch.long)
    hand_t = torch.zeros(D)
    for n in true:
        if n in idx:
            hand_t[idx[n]] = 1.0
    rem = Counter(true)
    for h, n in enumerate(hn):                                      # known slots first
        if n and n in idx and rem[n] > 0:
            slot_t[h] = idx[n]
            rem[n] -= 1
    left = sorted([n for n, c in rem.items() for _ in range(c) if n in idx], key=lambda n: idx[n])
    unmatched = [n for n, c in rem.items() for _ in range(c) if n not in idx]
    k = 0
    for h, n in enumerate(hn):
        if slot_t[h] < 0 and k < len(left):
            slot_t[h] = idx[left[k]]
            k += 1
    return slot_t, hand_t, len(true), unmatched, [n for n in hn if n]


def collate_labels(items, Hmax, Dmax):
    B = len(items)
    st = torch.full((B, Hmax), -1, dtype=torch.long)
    ht = torch.zeros(B, Dmax)
    for b, (s, h) in enumerate(items):
        st[b, :s.shape[0]] = s
        ht[b, :h.shape[0]] = h
    return st, ht


def to_dev(b, dev):
    return {k: (v.to(dev) if torch.is_tensor(v) else v) for k, v in b.items()}


def batch_of(obs, labs, dev):
    b = V.collate([o for o in obs])
    st, ht = collate_labels(labs, b["opp_hand_mask"].shape[1], b["opp_deck_mask"].shape[1])
    return to_dev(b, dev), st.to(dev), ht.to(dev)


def wake(enc, gen):
    for blk in enc.blocks:
        for lin in (blk.att.out, blk.ffn[-1]):
            with torch.no_grad():
                lin.weight.copy_(torch.randn(lin.weight.shape, generator=gen, dtype=lin.weight.dtype) * 0.05)
    return enc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recordings", nargs="+")
    ap.add_argument("--steps", type=int, default=1500)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--leak-per-file", type=int, default=40)
    ap.add_argument("--out", default=os.path.join(HERE, "artifacts", "v7", "5c_belief.json"))
    args = ap.parse_args()
    t0 = time.time()
    torch.manual_seed(args.seed)
    random.seed(args.seed)

    hello, msgs = load(args.recordings)
    if hello is None or not msgs:
        print("BELIEF5C|no oracle-labelled consults")
        return 2
    ids = V.CardIds()
    obs, labs, meta = [], [], []
    n_true = n_unm = n_known = n_unm_known = 0
    unm_names = Counter()
    for m, gid, fi in msgs:
        o = V.parse_consult(m, ids, hello)
        s, h, nt, nu, kn = labels(m, o)
        obs.append(o); labs.append((s, h)); meta.append((gid, fi))
        n_true += nt; n_unm += len(nu); n_known += int((o.opp_hand_id >= 0).sum())
        unm_names.update(nu); n_unm_known += sum(1 for n in nu if n in kn)
    games = sorted({g for g, _ in meta})
    rng = random.Random(args.seed)
    held = set(rng.sample(games, max(1, int(round(0.2 * len(games))))))
    tr = [i for i, (g, _) in enumerate(meta) if g not in held]
    te = [i for i, (g, _) in enumerate(meta) if g in held]
    print(f"BELIEF5C|consults={len(obs)}|games={len(games)}|files={len(args.recordings)}|train={len(tr)}|test={len(te)}"
          f"|true_cards={n_true}|unmatched={n_unm}|unmatched_that_are_known_slot_names={n_unm_known}|known_slots={n_known}|device={args.device}")
    print("BELIEF5C|unmatched_names|" + "|".join(f"{n}={c}" for n, c in unm_names.most_common(12)))

    dev = torch.device(args.device)
    table = N.CardTable(random=True)
    build = N.TokenBuilders(table).to(dev).eval()
    belief = BL.BeliefModule(d=256, layers=2).to(dev)
    opt = torch.optim.Adam(belief.parameters(), lr=args.lr)
    report = {"consults": len(obs), "games": len(games), "files": args.recordings, "train": len(tr), "test": len(te),
              "true_cards": n_true, "unmatched": n_unm, "unmatched_known": n_unm_known, "unmatched_names": dict(unm_names.most_common(30)),
              "known_slots": n_known, "thresholds": THR, "steps": args.steps}

    # ---- B2: stop-gradient on a real minibatch (builders in train mode, grads cleared) ----
    build.train(); belief.train()
    for p in build.parameters():
        p.grad = None
    bi = tr[:args.batch]
    b, st, ht = batch_of([obs[i] for i in bi], [labs[i] for i in bi], dev)
    toks = build(b)
    out = belief(toks)
    dt = torch.full((len(bi),), -1, dtype=torch.long, device=dev)
    loss = belief.loss(out, st, ht, dt, b["opp_hand_mask"], b["opp_deck_mask"])
    loss.backward()
    b2_build = all(p.grad is None or p.grad.abs().sum().item() == 0 for p in build.parameters())
    b2_belief = any(p.grad is not None and p.grad.abs().sum().item() > 0 for p in belief.parameters())
    report["B2"] = {"builder_grads_zero": b2_build, "belief_grads_nonzero": b2_belief, "pass": b2_build and b2_belief}
    print(f"BELIEF5C|B2|builder_grads_zero={b2_build}|belief_grads_nonzero={b2_belief}|pass={report['B2']['pass']}")
    opt.zero_grad(); build.eval()
    for p in build.parameters():
        p.requires_grad_(False)

    # ---- B3/B4: train on the train games, evaluate on the held-out games ----
    belief.train()
    for step in range(args.steps):
        bi = rng.sample(tr, min(args.batch, len(tr)))
        b, st, ht = batch_of([obs[i] for i in bi], [labs[i] for i in bi], dev)
        with torch.no_grad():
            toks = build(b)
        out = belief(toks)
        dt = torch.full((len(bi),), -1, dtype=torch.long, device=dev)
        loss = belief.loss(out, st, ht, dt, b["opp_hand_mask"], b["opp_deck_mask"])
        opt.zero_grad(); loss.backward(); opt.step()
        if step % 250 == 0 or step == args.steps - 1:
            print(f"BELIEF5C|train|step={step}|loss={loss.item():.4f}|t={time.time() - t0:.0f}s")
    belief.eval()

    def evaluate(idx_list):
        ll_sum = base_sum = ms_sum = 0.0; n_ok = 0
        du_sum = du_sq = dm_sum = dm_sq = 0.0                          # paired per-slot margins -> SE
        known_mass = 0.0; n_known_eval = 0
        bce_sum = 0.0; n_deck = 0; pos = []; neg = []
        for s in range(0, len(idx_list), 128):
            bi = idx_list[s:s + 128]
            b, st, ht = batch_of([obs[i] for i in bi], [labs[i] for i in bi], dev)
            with torch.no_grad():
                out = belief(build(b))
            hm, dm = b["opp_hand_mask"], b["opp_deck_mask"]
            ok = (st >= 0) & hm
            lp = (out["pointer"] + 1e-9).log()
            g = lp.gather(2, st.clamp(min=0).unsqueeze(-1)).squeeze(-1)
            ll_sum += g[ok].sum().item(); n_ok += int(ok.sum())
            n = dm.sum(1).float().clamp(min=1)
            base_sum += (-(n.log().unsqueeze(1).expand_as(g)))[ok].sum().item()
            cnt = b["opp_deck"][..., 0] * dm.float()                        # count remaining (÷4, saturating)
            ms = (cnt / cnt.sum(1, keepdim=True).clamp(min=1e-9) + 1e-9).log()   # [B, D]
            msg_ = ms.gather(1, st.clamp(min=0))
            ms_sum += msg_.masked_fill(~ok, 0).sum().item()
            du = (g + n.log().unsqueeze(1).expand_as(g))[ok]; dmm = (g - msg_)[ok]
            du_sum += du.sum().item(); du_sq += (du ** 2).sum().item(); dm_sum += dmm.sum().item(); dm_sq += (dmm ** 2).sum().item()
            kn = ok & (b["opp_hand_id"] >= 0)
            if kn.any():
                known_mass += out["pointer"].gather(2, st.clamp(min=0).unsqueeze(-1)).squeeze(-1)[kn].sum().item()
                n_known_eval += int(kn.sum())
            ph = out["p_hand"].clamp(1e-6, 1 - 1e-6)
            bce = -(ht * ph.log() + (1 - ht) * (1 - ph).log())
            bce_sum += bce[dm].sum().item(); n_deck += int(dm.sum())
            pos += ph[dm & (ht > 0.5)].tolist(); neg += ph[dm & (ht < 0.5)].tolist()
        # base-rate BCE and a rank AUC on a subsample
        p_base = len(pos) / max(1, len(pos) + len(neg))
        bce_base = -(p_base * torch.log(torch.tensor(p_base)) + (1 - p_base) * torch.log(torch.tensor(1 - p_base))).item() if 0 < p_base < 1 else 0.0
        rs = random.Random(1)
        ps = rs.sample(pos, min(2000, len(pos))); ns = rs.sample(neg, min(2000, len(neg)))
        auc = sum((1.0 if a > c else 0.5 if a == c else 0.0) for a in ps for c in ns) / max(1, len(ps) * len(ns))
        def se(sm, sq):
            n = max(1, n_ok); mu = sm / n
            return ((max(0.0, sq / n - mu * mu)) / n) ** 0.5
        return {"slots": n_ok, "loglik": ll_sum / max(1, n_ok), "uniform": base_sum / max(1, n_ok),
                "se_vs_uniform": se(du_sum, du_sq), "se_vs_multiset": se(dm_sum, dm_sq),
                "multiset": ms_sum / max(1, n_ok), "known_slots": n_known_eval,
                "known_mass": (known_mass / n_known_eval) if n_known_eval else None,
                "p_hand_bce": bce_sum / max(1, n_deck), "base_rate": p_base, "base_bce": bce_base, "auc": auc}

    ev_tr = evaluate(tr); ev_te = evaluate(te)
    report["B3"] = {"train": ev_tr, "test": ev_te,
                    "pass": ev_te["loglik"] > ev_te["uniform"] + THR["B3_margin"]}
    print(f"BELIEF5C|B3|test_loglik={ev_te['loglik']:.3f}|uniform={ev_te['uniform']:.3f}|multiset={ev_te['multiset']:.3f}"
          f"|slots={ev_te['slots']}|se_vs_uniform={ev_te['se_vs_uniform']:.4f}|se_vs_multiset={ev_te['se_vs_multiset']:.4f}"
          f"|train_loglik={ev_tr['loglik']:.3f}|pass={report['B3']['pass']}")
    print(f"BELIEF5C|p_hand|test_bce={ev_te['p_hand_bce']:.3f}|base_bce={ev_te['base_bce']:.3f}|base_rate={ev_te['base_rate']:.3f}|auc={ev_te['auc']:.3f}")
    if ev_te["known_slots"] >= THR["B4_min_rows"]:
        b4 = {"known_slots": ev_te["known_slots"], "mass": ev_te["known_mass"], "pass": ev_te["known_mass"] >= THR["B4_mass"]}
    else:
        b4 = {"known_slots": ev_te["known_slots"], "mass": ev_te["known_mass"], "pass": None, "note": "not exercised"}
    report["B4"] = b4
    print(f"BELIEF5C|B4|known_slots={b4['known_slots']}|mass={b4['mass']}|pass={b4['pass']}")

    # ---- B1: leak gate with belief ON (double precision, woken encoder, features woken as in 4f) ----
    gen = torch.Generator().manual_seed(6)
    build_d = N.TokenBuilders(N.CardTable(random=True)).double().eval()
    enc_d = wake(E.StateGraphEncoder(layers=2).double().eval(), gen)
    heads_d = H.V7Heads().double().eval()
    bl_d = BL.BeliefModule().double().eval()
    with torch.no_grad():
        bl_d.hand_feat.weight.copy_(torch.randn(bl_d.hand_feat.weight.shape, generator=gen, dtype=torch.float64) * 0.05)
        bl_d.deck_feat.weight.copy_(torch.randn(bl_d.deck_feat.weight.shape, generator=gen, dtype=torch.float64) * 0.5)
    names = sorted({n for m, _, _ in msgs for n in m.get("v7_ent_name", []) + m.get("v7_oe_hand", []) if n})

    def logits(m):
        o = V.parse_consult(m, ids, hello)
        b = V.collate([o]); b = {k: (v.double() if v.dtype == torch.float32 else v) for k, v in b.items()}
        with torch.no_grad():
            toks = build_d(b)
            lg, _, _ = heads_d(enc_d(bl_d.attach(toks, bl_d(toks))))
        return lg[0][torch.isfinite(lg[0])]

    per_file = {}
    for i, (m, _, fi) in enumerate(msgs):
        per_file.setdefault(fi, []).append(i)
    pick = [i for fi in sorted(per_file) for i in rng.sample(per_file[fi], min(args.leak_per_file, len(per_file[fi])))]
    max_d = 0.0; n_moved = 0
    for i in pick:
        m = dict(msgs[i][0])
        a = logits(m)
        g = random.Random(i)
        m["oe"] = [[g.random() for _ in range(48)] for _ in range(len(m.get("oe") or []) + 1)]
        m["v7_oe_hand"] = [g.choice(names) for _ in range(len(m["v7_oe_hand"]) + 1)]
        c = logits(m)
        d = (a - c).abs().max().item() if a.shape == c.shape else float("inf")
        max_d = max(max_d, d)
        if a.numel() > 1 and a.std().item() > 0:
            n_moved += 1
    b1 = {"consults": len(pick), "max_abs_dlogit": max_d, "logit_rows_nondegenerate": n_moved,
          "pass": max_d <= THR["B1_tol"] and len(pick) >= THR["B1_min_consults"]}
    report["B1"] = b1
    print(f"BELIEF5C|B1|consults={len(pick)}|max_abs_dlogit={max_d}|nondegenerate={n_moved}|pass={b1['pass']}")

    gates = [report[k]["pass"] for k in ("B1", "B2", "B3")] + ([report["B4"]["pass"]] if report["B4"]["pass"] is not None else [])
    report["pass"] = all(gates)
    report["seconds"] = round(time.time() - t0)
    json.dump(report, open(args.out, "w"), indent=1)
    print(f"BELIEF5C|pass={report['pass']}|B4={report['B4']['pass']}|seconds={report['seconds']}|out={args.out}")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())

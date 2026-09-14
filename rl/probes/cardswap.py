#!/usr/bin/env python3
"""Phase 9 / P1 - card-swap counterfactual (rl/PHASE9-PROBES.md).

Does a v7 checkpoint's candidate scorer read a card's rules text, or only its
type, cost and power/toughness?  For every recorded consult that offers a
SPELL candidate whose card is the SOURCE of a pair, the referred entity's
identity is swapped to the PARTNER card (embedding row via ent_id plus the
identity fields of the entity row that the partner would carry), everything
else fixed, and the candidate's probability is rescored with the same
memoryless path as rl/v7_init_logits.py (fresh LSTM state, no deck context).

Pair classes (built from the cards_v1 corpus; written to pairs_<class>.txt):
  text  same mana cost / types / supertypes / P/T, both texts are ONLY
        keywords, keyword sets differ (vanilla vs one keyword, or two
        different keywords).  Swapped: ent_id (embedding row) + the 18
        keyword bits (ent row 34..51).  Sub-variants reported: text_emb
        (embedding row only) and text_kw (keyword bits only).
  pt    same cost / types / supertypes / keyword set, |dP|+|dT| == 1.
        Swapped: ent_id + P/T fields (ent row 10, 11, 13, 14, 15).
  cost  same types / supertypes / P/T / keyword set / colours, mana value
        differs by 1.  Swapped: ent_id + mana value (ent row 17).  NOT
        swapped: the candidate afterstate (mana left after, castable now).
  type  same mana cost, partner is a non-creature non-land (instant /
        sorcery / enchantment / artifact).  Swapped: ent_id + is-creature
        (29) + type flags (30..33) + P/T fields zeroed + keyword bits.

Usage (WSL):
  python3 rl/probes/cardswap.py --ckpt init=rl/artifacts/v7/9/init.pt \
      --ckpt C1s0=rl/artifacts/v7/7c1/s0/ck_2048.pt ... --out rl/artifacts/v7/9 \
      rl/artifacts/v7/wire3a/7c_W0Base_{p1,p99,sf}.jsonl rl/artifacts/v7/wire3a/7c_BenchDimir_{p1,p99,sf}.jsonl
"""
import argparse
import collections
import dataclasses
import glob
import gzip
import json
import os
import random
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RL = os.path.dirname(HERE)
sys.path.insert(0, RL)
import torch                      # noqa: E402
import v7_obs as V                # noqa: E402
import v7_policy as P             # noqa: E402

TYPES = ["PASS", "LAND", "SPELL", "ACTIVATE", "TARGET", "ATTACK", "BLOCK", "OTHER"]
# WIRE-V7 §2d bits 34..51, rl/e2_extract.py KEYWORDS order
KEYWORDS = ["Flying", "Haste", "Deathtouch", "Lifelink", "First Strike",
            "Double Strike", "Trample", "Vigilance", "Flash", "Menace",
            "Reach", "Defender", "Ward", "Hexproof", "Shroud",
            "Protection", "Prowess", "Ninjutsu"]
KW_LOWER = [k.lower() for k in KEYWORDS]
KW_IDX = {k: i for i, k in enumerate(KW_LOWER)}
CARDS = os.path.join(RL, "artifacts", "cards_v1")
ENT_KW0, ENT_KW1 = 34, 52
MAX_PARTNERS = 8


# ----------------------------------------------------------------------------- corpus
def load_corpus():
    F, O = {}, {}
    with gzip.open(os.path.join(CARDS, "fields.jsonl.gz"), "rt", encoding="utf-8") as fh:
        for line in fh:
            o = json.loads(line)
            if o.get("kind") == "card":
                F[o["name"]] = o
    with gzip.open(os.path.join(CARDS, "oracle.jsonl.gz"), "rt", encoding="utf-8") as fh:
        for line in fh:
            o = json.loads(line)
            O[o["name"]] = o.get("oracle") or ""
    return F, O


def kw_only(text):
    """The keyword set if the rules text is nothing but keywords from KEYWORDS
    (reminder text stripped); None otherwise.  '' -> frozenset() (vanilla)."""
    t = (text or "").replace("\\n", "\n")
    t = re.sub(r"\([^)]*\)", "", t)
    parts = [p.strip().lower() for p in re.split(r"[\n,;]+", t)]
    out = set()
    for p in parts:
        if not p:
            continue
        if p not in KW_IDX or p in ("ward", "protection"):   # 'ward {2}' / 'protection from x' carry a parameter
            return None
        out.add(p)
    return frozenset(out)


def kw_bits(kws):
    v = [0.0] * len(KEYWORDS)
    for k in kws:
        if k in KW_IDX:
            v[KW_IDX[k]] = 1.0
    return v


def _int(x):
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def key_ptc(f):
    return (f["mana_cost"], tuple(f["types"]), tuple(f.get("supertypes") or []), f["power"], f["toughness"])


def build_pairs(sources, F, O, ids, cap=MAX_PARTNERS, seed=9):
    """sources: list of card names (creatures that appear as SPELL candidates).
    Returns {cls: [(src, partner, note)]}."""
    rng = random.Random(seed)
    usable = {n: f for n, f in F.items() if f.get("n_faces", 1) == 1 and ids.resolve(n) >= 0
              and f.get("mana_cost") not in (None, "no cost")}
    by_ptc = collections.defaultdict(list)
    for n, f in usable.items():
        by_ptc[key_ptc(f)].append(n)
    pairs = {"text": [], "pt": [], "cost": [], "type": []}
    why = {}
    for s in sources:
        f = F.get(s)
        if f is None or ids.resolve(s) < 0:
            why[s] = "not in corpus/embedding"; continue
        if "Creature" not in f["types"]:
            why[s] = "not a creature"; continue
        A = kw_only(O.get(s, ""))
        kp = key_ptc(f)
        # text: same everything, keyword-only texts, sets differ by 1 or 2 keywords
        if A is None:
            why[s] = "source text is not keyword-only (no text/pt/cost pairs); type pairs only"
        else:
            cand = []
            for n in by_ptc[kp]:
                if n == s:
                    continue
                B = kw_only(O.get(n, ""))
                if B is None or B == A or not (1 <= len(A ^ B) <= 2):
                    continue
                cand.append((n, "kw:%s->%s" % ("+".join(sorted(A)) or "vanilla", "+".join(sorted(B)) or "vanilla")))
            for n, note in rng.sample(sorted(cand), min(cap, len(cand))):
                pairs["text"].append((s, n, note))
            # pt: same cost/types/supertypes/keywords, |dP|+|dT| == 1
            cand = []
            for n, g in usable.items():
                if n == s or g["mana_cost"] != f["mana_cost"] or tuple(g["types"]) != tuple(f["types"]) \
                        or tuple(g.get("supertypes") or []) != tuple(f.get("supertypes") or []):
                    continue
                gp, gt, fp, ft = _int(g["power"]), _int(g["toughness"]), _int(f["power"]), _int(f["toughness"])
                if None in (gp, gt, fp, ft) or abs(gp - fp) + abs(gt - ft) != 1:
                    continue
                if kw_only(O.get(n, "")) != A:
                    continue
                cand.append((n, "pt:%s/%s->%s/%s" % (f["power"], f["toughness"], g["power"], g["toughness"])))
            for n, note in rng.sample(sorted(cand), min(cap, len(cand))):
                pairs["pt"].append((s, n, note))
            # cost: same types/supertypes/PT/keywords/colours, mv differs by 1
            cand = []
            for n, g in usable.items():
                if n == s or tuple(g["types"]) != tuple(f["types"]) or g["power"] != f["power"] \
                        or g["toughness"] != f["toughness"] or g.get("colors") != f.get("colors") \
                        or tuple(g.get("supertypes") or []) != tuple(f.get("supertypes") or []):
                    continue
                if g["mv"] is None or f["mv"] is None or abs(int(g["mv"]) - int(f["mv"])) != 1:
                    continue
                if kw_only(O.get(n, "")) != A:
                    continue
                cand.append((n, "mv:%s->%s" % (f["mana_cost"], g["mana_cost"])))
            for n, note in rng.sample(sorted(cand), min(cap, len(cand))):
                pairs["cost"].append((s, n, note))
        # type: same mana cost, non-creature non-land spell
        cand = []
        for n, g in usable.items():
            if n == s or g["mana_cost"] != f["mana_cost"]:
                continue
            ts = set(g["types"])
            if "Creature" in ts or "Land" in ts or not ts <= {"Instant", "Sorcery", "Enchantment", "Artifact"}:
                continue
            if g.get("subtypes"):                      # keep it plain: no Auras / Equipment / Sagas
                continue
            cand.append((n, "type:Creature->%s" % "/".join(g["types"])))
        for n, note in rng.sample(sorted(cand), min(cap, len(cand))):
            pairs["type"].append((s, n, note))
    return pairs, why


# ----------------------------------------------------------------------------- swaps
def apply_swap(obs, i, cls, partner, F, O, ids):
    """Return a copy of obs with entity i's identity swapped to partner per class."""
    g = F.get(partner, {})
    ent = obs.ent.clone()
    ent_id = obs.ent_id.clone()
    pid = ids.resolve(partner)
    row = ent[i]
    swap_id = cls not in ("text_kw",)
    if swap_id:
        ent_id[i] = pid
    if cls in ("text", "text_kw"):
        row[ENT_KW0:ENT_KW1] = torch.tensor(kw_bits(kw_only(O.get(partner, "")) or frozenset()))
    elif cls == "text_emb":
        pass
    elif cls == "pt":
        pw, tg = _int(g["power"]) / 6.0, _int(g["toughness"]) / 6.0
        dmg = float(row[12])
        row[10], row[11], row[14], row[15] = pw, tg, pw, tg
        row[13] = tg - dmg
    elif cls == "cost":
        row[17] = float(g["mv"]) / 6.0
    elif cls == "type":
        row[10:16] = 0.0
        row[29] = 0.0
        ts = set(g["types"])
        row[30] = 0.0
        row[31] = 1.0 if "Instant" in ts else 0.0
        row[32] = 1.0 if "Sorcery" in ts else 0.0
        row[33] = 1.0 if ts & {"Artifact", "Enchantment"} else 0.0
        gf = g.get("graph") or []
        row[ENT_KW0:ENT_KW1] = torch.tensor(kw_bits({k for k in KW_LOWER if _graph_kw(gf, k)}))
    elif cls == "self_mana":                          # control: the candidate's OWN afterstate row (partner = k)
        cand = obs.cand.clone()
        k = int(partner)
        cand[k, 8] = cand[k, 8] - 1.0 / 6.0 if cand[k, 8] >= 1.0 / 6.0 else cand[k, 8] + 1.0 / 6.0
        return dataclasses.replace(obs, cand=cand)
    else:
        raise ValueError(cls)
    return dataclasses.replace(obs, ent=ent, ent_id=ent_id)


_GRAPH_FEATURES = None


def _graph_kw(gf, kw):
    global _GRAPH_FEATURES
    if _GRAPH_FEATURES is None:
        _GRAPH_FEATURES = json.load(open(os.path.join(CARDS, "index.json")))["graph_features"]
    name = "kw_" + kw.replace(" ", "_")
    if name in _GRAPH_FEATURES and len(gf) == len(_GRAPH_FEATURES):
        return gf[_GRAPH_FEATURES.index(name)] > 0.5
    return False


def load_consults(paths):
    hello, msgs = None, []
    for p in paths:
        for raw in open(p, "rb"):
            if not raw.strip():
                continue
            m = json.loads(raw)
            if m.get("t") == "hello":
                hello = hello or m
            elif m.get("t") == "consult" and "v7_ent" in m:
                m["_file"] = os.path.basename(p)
                msgs.append(m)
    return hello, msgs


def score(net, obs_list, device, batch=64, bound=5.0):
    """-> list of (probs over valid candidates, argmax index, bounded logits, raw logits).
    The net is run UNBOUNDED; the bound (B * tanh(x / B), the lane's 5) is applied here."""
    out = []
    net.heads.logit_bound = 0.0
    for s in range(0, len(obs_list), batch):
        b = V.collate(obs_list[s:s + batch])
        b = {k: (v.to(device) if torch.is_tensor(v) else v) for k, v in b.items()}
        with torch.no_grad():
            lg, _, _, _ = net(b, with_value=False)
        lg = lg.float().cpu()
        for i, o in enumerate(obs_list[s:s + batch]):
            raw = lg[i][:o.cand.shape[0]]
            row = bound * torch.tanh(raw / bound) if bound else raw
            out.append((torch.softmax(row, 0), int(row.argmax()), row, raw))
    return out


def mechanism(net, obs, device, n=256):
    """How far the encoder is from the identity on the builder tokens, and the
    magnitude of the zero-initialised output projections vs the qkv weights."""
    rel_c, rel_g = [], []
    for s in range(0, min(n, len(obs)), 32):
        b = V.collate(obs[s:s + 32])
        b = {k: (v.to(device) if torch.is_tensor(v) else v) for k, v in b.items()}
        with torch.no_grad():
            toks = net.build(b)
            toks = net.belief.attach(toks, net.belief(toks))
            enc = net.enc(toks, ent_raw=b["ent"])
        cm = toks["cand_mask"]
        dc = (enc["cand"] - toks["cand"]).norm(dim=-1)[cm] / toks["cand"].norm(dim=-1)[cm].clamp(min=1e-6)
        dg = (enc["game"][:, 0] - toks["game"][:, 0]).norm(dim=-1) / toks["game"][:, 0].norm(dim=-1).clamp(min=1e-6)
        rel_c += dc.cpu().tolist(); rel_g += dg.cpu().tolist()
    sd = net.enc.state_dict()
    mag = lambda pat: float(np.mean([sd[k].abs().mean().item() for k in sd if pat in k and sd[k].dim() == 2]))   # noqa: E731
    # the per-edge attention bias rows: refers_to (candidate -> its referent) is table row 9 = bias_rows[8]
    rows = torch.stack([blk.att.bias_rows.detach().cpu() for blk in net.enc.blocks])      # [layers, n_edge-1, heads]
    return ("rel|enc(cand)-build(cand)|=%.5f|rel|enc(game)-build(game)|=%.5f|mean|W| att.qkv=%.4f att.out=%.5f ffn.in=%.4f ffn.out=%.5f"
            "|edge_bias refers_to max=%.5f mean=%.5f|all edges max=%.5f"
            % (float(np.mean(rel_c)), float(np.mean(rel_g)), mag("att.qkv.weight"), mag("att.out.weight"), mag("ffn.0.weight"), mag("ffn.2.weight"),
               float(rows[:, 8].abs().max()), float(rows[:, 8].abs().mean()), float(rows.abs().max())))


def cand_key(o, k):
    """(type, referent name) - identical copies share a key."""
    toks = torch.nonzero(o.refers[k]).flatten().tolist()
    return (int(o.cand_type[k]), o.ent_name[toks[0] - 3] if toks else "")


def boot_ci(groups, vals, reps=2000, seed=0):
    """Mean of vals with a bootstrap CI resampling GROUPS (consults)."""
    vals = np.asarray(vals, dtype=float)
    groups = np.asarray(groups)
    if len(vals) == 0:
        return float("nan"), float("nan"), float("nan")
    uniq = np.unique(groups)
    idx_by = {g: np.nonzero(groups == g)[0] for g in uniq}
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(reps):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        sel = np.concatenate([idx_by[g] for g in pick])
        means.append(vals[sel].mean())
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(vals.mean()), float(lo), float(hi)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recordings", nargs="+")
    ap.add_argument("--ckpt", action="append", required=True, help="name=path")
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--logit-bound", type=float, default=5.0)
    ap.add_argument("--cap", type=int, default=MAX_PARTNERS)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    paths = [q for p in args.recordings for q in sorted(glob.glob(p))] or args.recordings
    F, O = load_corpus()
    ids = V.CardIds()
    hello, msgs = load_consults(paths)
    obs = [V.parse_consult(m, ids, hello) for m in msgs]
    # sources: creature cards referred by SPELL candidates
    src_count = collections.Counter()
    for o in obs:
        for k in range(o.cand.shape[0]):
            if int(o.cand_type[k]) != 2:
                continue
            toks = torch.nonzero(o.refers[k]).flatten().tolist()
            if not toks:
                continue
            nm = o.ent_name[toks[0] - 3]
            src_count[nm] += 1
    sources = sorted(src_count)
    pairs, why = build_pairs(sources, F, O, ids, cap=args.cap)
    with open(os.path.join(args.out, "pairs_sources.txt"), "w") as fh:
        for s in sources:
            f = F.get(s, {})
            fh.write("%s\t%d\t%s\t%s\t%s/%s\t%s\t%s\n" % (s, src_count[s], f.get("mana_cost"), "/".join(f.get("types", [])),
                                                       f.get("power"), f.get("toughness"),
                                                       (O.get(s, "") or "").replace("\\n", " | ")[:90], why.get(s, "")))
    for cls, lst in pairs.items():
        with open(os.path.join(args.out, "pairs_%s.txt" % cls), "w") as fh:
            for s, n, note in lst:
                fh.write("%s\t%s\t%s\n" % (s, n, note))
    print("CARDSWAP|consults=%d|files=%d|sources=%d|pairs=%s" % (
        len(obs), len(paths), len(sources), ",".join("%s:%d" % (c, len(l)) for c, l in pairs.items())))
    print("CARDSWAP|sources_without_pairs|" + "; ".join("%s: %s" % (s, w) for s, w in why.items()))
    # the swap jobs: (consult idx, k, ent i, cls, src, partner)
    by_src = collections.defaultdict(lambda: collections.defaultdict(list))
    for cls, lst in pairs.items():
        for s, n, note in lst:
            by_src[s][cls].append(n)
    jobs = []
    for ci, o in enumerate(obs):
        for k in range(o.cand.shape[0]):
            if int(o.cand_type[k]) != 2:
                continue
            toks = torch.nonzero(o.refers[k]).flatten().tolist()
            if not toks:
                continue
            i = toks[0] - 3
            nm = o.ent_name[i]
            for cls, partners in by_src[nm].items():
                for n in partners:
                    jobs.append((ci, k, i, cls, nm, n))
                    if cls == "text":
                        jobs.append((ci, k, i, "text_emb", nm, n))
                        jobs.append((ci, k, i, "text_kw", nm, n))
            if by_src[nm]:
                jobs.append((ci, k, i, "self_mana", nm, str(k)))
    print("CARDSWAP|swap_jobs=%d|device=%s" % (len(jobs), args.device))
    classes = ["text", "text_emb", "text_kw", "pt", "cost", "type", "self_mana"]
    summary_lines = []
    per_subject = {}
    for spec in args.ckpt:
        name, path = spec.split("=", 1)
        net = P.V7Policy.load(path, device=args.device).eval()
        net.heads.logit_bound = args.logit_bound
        base = score(net, obs, args.device, bound=args.logit_bound)
        swapped = [apply_swap(obs[ci], i, cls, n, F, O, ids) for (ci, k, i, cls, s, n) in jobs]
        after = score(net, swapped, args.device, bound=args.logit_bound)
        rows = []
        with open(os.path.join(args.out, "cardswap_%s.tsv" % name), "w") as fh:
            fh.write("\t".join(["consult", "file", "k", "class", "src", "partner", "p_before", "p_after", "dp", "dlogit", "dlogit_raw",
                                "flip", "argmax_before", "argmax_after"]) + "\n")
            for (ci, k, i, cls, s, n), (pa, aa, la, ra) in zip(jobs, after):
                pb, ab, lb, rb = base[ci]
                dp = abs(float(pa[k]) - float(pb[k]))
                dl = abs(float(la[k]) - float(lb[k]))
                dr = abs(float(ra[k]) - float(rb[k]))
                o = obs[ci]
                flip = int(cand_key(o, aa) != cand_key(o, ab))     # identical copies tie exactly: a flip is a CLASS change
                strict = int(flip and abs(float(lb[aa]) - float(lb[ab])) > 1e-3)   # ... and the two were not tied before
                rows.append((ci, k, cls, s, n, float(pb[k]), float(pa[k]), dp, flip, dl, dr, strict))
                fh.write("\t".join(["%d", "%s", "%d", "%s", "%s", "%s", "%.6f", "%.6f", "%.6f", "%.6f", "%.6f", "%d", "%s", "%s\n"]) % (
                    ci, msgs[ci]["_file"], k, cls, s, n, float(pb[k]), float(pa[k]), dp, dl, dr, flip,
                    TYPES[int(o.cand_type[ab])], TYPES[int(o.cand_type[aa])]))
        # aggregate: per (consult, k) mean over partners, bootstrap over consults
        res = {}
        for cls in classes:
            per_ck = collections.defaultdict(list); per_dl = collections.defaultdict(list)
            flips = []; fgroups = []; dls = []
            per_dr = collections.defaultdict(list)
            stricts = []
            for (ci, k, c, s, n, pb, pa, dp, fl, dl, dr, st) in rows:
                if c != cls:
                    continue
                per_ck[(ci, k)].append(dp); per_dl[(ci, k)].append(dl); per_dr[(ci, k)].append(dr)
                flips.append(fl); fgroups.append(ci); dls.append(dl); stricts.append(st)
            groups = [ci for (ci, k) in per_ck]
            vals = [float(np.mean(v)) for v in per_ck.values()]
            m, lo, hi = boot_ci(groups, vals)
            fm, flo, fhi = boot_ci(fgroups, flips)
            sm, slo, shi = boot_ci(fgroups, stricts)
            dlm = float(np.mean([np.mean(v) for v in per_dl.values()])) if per_dl else float("nan")
            dlmax = max(dls) if dls else float("nan")
            drm = float(np.mean([np.mean(v) for v in per_dr.values()])) if per_dr else float("nan")
            res[cls] = dict(mean=m, lo=lo, hi=hi, flip=fm, flo=flo, fhi=fhi, n_ck=len(vals),
                            n_consults=len(set(groups)), n_swaps=len(flips), dlogit=dlm, dlogit_max=dlmax)
            summary_lines.append("P1|%s|%s|mean_dp=%.5f [%.5f,%.5f]|mean_dlogit=%.5f|mean_dlogit_raw=%.5f|max_dlogit=%.4f|flip=%.3f [%.3f,%.3f]|flip_strict=%.3f [%.3f,%.3f]|cand=%d|consults=%d|swaps=%d" % (
                name, cls, m, lo, hi, dlm, drm, dlmax, fm, flo, fhi, sm, slo, shi, len(vals), len(set(groups)), len(flips)))
            print(summary_lines[-1])
        # per keyword for the text class
        per_kw = collections.defaultdict(list)
        for (ci, k, c, s, n, pb, pa, dp, fl, dl, dr, st) in rows:
            if c == "text":
                B = kw_only(O.get(n, "")) or frozenset()
                A = kw_only(O.get(s, "")) or frozenset()
                per_kw["+".join(sorted(A ^ B))].append(dp)
        summary_lines.append("P1|%s|text_by_keyword|" % name + "|".join(
            "%s=%.5f(n=%d)" % (kw, float(np.mean(v)), len(v)) for kw, v in sorted(per_kw.items())))
        print(summary_lines[-1])
        # mean p_before of the swapped candidates (context)
        pbs = [pb for (ci, k, c, s, n, pb, pa, dp, fl, dl, dr, st) in rows if c == "text"]
        summary_lines.append("P1|%s|context|mean_p_before(text cands)=%.3f" % (name, float(np.mean(pbs)) if pbs else float("nan")))
        # tie census: pairs of SPELL candidates naming DIFFERENT cards, same vs different afterstate row
        same_row, diff_row = [], []
        for ci, o in enumerate(obs):
            lb = base[ci][2]
            ks = [k for k in range(o.cand.shape[0]) if int(o.cand_type[k]) == 2]
            for x in range(len(ks)):
                for y in range(x + 1, len(ks)):
                    a, b2 = ks[x], ks[y]
                    if cand_key(o, a)[1] == cand_key(o, b2)[1]:
                        continue
                    d = abs(float(lb[a]) - float(lb[b2]))
                    (same_row if torch.equal(o.cand[a], o.cand[b2]) else diff_row).append(d)
        summary_lines.append("P1|%s|tie_census|diff-name SPELL pairs, same afterstate row: n=%d mean|dlogit|=%.5f tied(<1e-4)=%.3f | different row: n=%d mean|dlogit|=%.3f" % (
            name, len(same_row), float(np.mean(same_row)) if same_row else float("nan"),
            float(np.mean([d < 1e-4 for d in same_row])) if same_row else float("nan"),
            len(diff_row), float(np.mean(diff_row)) if diff_row else float("nan")))
        print(summary_lines[-1])
        # yardstick: the scorer's working range on the same consults (bounded logits)
        gaps, stds, raws = [], [], []
        for (pb, ab, lb, rb) in base:
            if lb.numel() > 1:
                srt = lb.sort(descending=True).values
                gaps.append(float(srt[0] - srt[1])); stds.append(float(lb.std()))
            raws.append(float(rb.abs().mean()))
        summary_lines.append("P1|%s|yardstick|mean_top_gap=%.3f|mean_within_consult_logit_std=%.3f|mean_abs_raw_logit=%.2f" % (
            name, float(np.mean(gaps)), float(np.mean(stds)), float(np.mean(raws))))
        print(summary_lines[-1])
        summary_lines.append("P1|%s|mechanism|%s" % (name, mechanism(net, obs, args.device)))
        print(summary_lines[-1])
        per_subject[name] = res
        # reading
        t, p = res["text"], res["pt"]
        if t["mean"] < 0.10 * p["mean"] and t["hi"] < p["lo"]:
            reading = "text-blind"
        elif t["mean"] >= 0.5 * p["mean"]:
            reading = "text-sensitive"
        else:
            reading = "weakly text-sensitive"
        ratio = t["mean"] / p["mean"] if p["mean"] > 0 else float("nan")
        summary_lines.append("P1|%s|reading=%s|ratio_text_over_pt=%.3f" % (name, reading, ratio))
        print(summary_lines[-1])
        del net
    if "init" in per_subject:
        i0 = per_subject["init"]["text"]
        for name, res in per_subject.items():
            if name == "init":
                continue
            t = res["text"]
            eff = "sharpened" if t["lo"] > i0["hi"] else ("erased" if t["hi"] < i0["lo"] else "preserved")
            summary_lines.append("P1|%s|training_effect_vs_init(text)=%s|trained=%.4f [%.4f,%.4f]|init=%.4f [%.4f,%.4f]" % (
                name, eff, t["mean"], t["lo"], t["hi"], i0["mean"], i0["lo"], i0["hi"]))
            print(summary_lines[-1])
    with open(os.path.join(args.out, "cardswap_summary.txt"), "w") as fh:
        fh.write("\n".join(summary_lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

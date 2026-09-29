"""Profile clusters, run the plan's validation checks, surface sparse edges.

Reads fra_signals.json, fra_edges.json, fra_graph.json. Writes
GRAPH-REPORT.md (generated; do not edit) and eval.json. This is the only
module that reads the held-out DeckHas/DeckHints labels.
"""
import json, math, random, collections, re, sys

SCHEMES = ("uniform", "tight", "rarity", "full", "full_knn")
cards = {c["name"]: c for c in json.load(open("fra_signals.json", encoding="utf-8"))}
edges = json.load(open("fra_edges.json", encoding="utf-8"))
graph = json.load(open("fra_graph.json", encoding="utf-8"))
names = list(cards)
OUT = []
EV = {}


def P(s=""):
    OUT.append(s)


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, c - h), min(1.0, c + h))


def weights(s):
    w = collections.defaultdict(dict)
    for k, v in graph["schemes"][s]["weights"].items():
        a, b = k.split("|||")
        w[a][b] = v; w[b][a] = v
    return w


W = {s: weights(s) for s in SCHEMES}
LAB = {s: graph["schemes"][s]["communities"] for s in SCHEMES}

# per ordered pair, the reasons (best match per primitive)
REASON = collections.defaultdict(dict)
for x in edges:
    k = (x["a"], x["b"])
    cur = REASON[k].get(x["prim"] + "/" + x["type"])
    if cur is None or x["w"]["full"] > cur["w"]["full"]:
        REASON[k][x["prim"] + "/" + x["type"]] = x


def why(a, b, n=3):
    rs = list(REASON.get((a, b), {}).values()) + list(REASON.get((b, a), {}).values())
    rs.sort(key=lambda x: -x["w"]["full"])
    return "; ".join(f"{x['a']} [{x['emit']}] → {x['b']} [{x['listen']}] ({x['prim']}, {x['type']})" for x in rs[:n])


def neighbours(card, s="full", k=10):
    return sorted(W[s][card].items(), key=lambda kv: -kv[1])[:k]


# ---------------- cluster profiles ----------------
def profile(s):
    lab = LAB[s]
    comm = collections.defaultdict(list)
    for n, c in lab.items():
        comm[c].append(n)
    prim_in = collections.defaultdict(collections.Counter)
    for x in edges:
        if lab[x["a"]] == lab[x["b"]] and x["b"] in W[s][x["a"]]:
            prim_in[lab[x["a"]]][x["prim"] + ("" if x["type"] == "state" else f" ({x['type']})")] += \
                x["w"]["full" if s == "full_knn" else s]
    rows = []
    for c, members in sorted(comm.items(), key=lambda kv: -len(kv[1])):
        strength = {m: sum(W[s][m].get(o, 0) for o in members if o != m) for m in members}
        core = sorted(members, key=lambda m: -strength[m])[:8]
        tot = sum(prim_in[c].values()) or 1
        top = [(p, v / tot) for p, v in prim_in[c].most_common(5)]
        colors = collections.Counter(col for m in members for col in cards[m]["colors"])
        rows.append({"id": c, "size": len(members), "core": core, "top_prims": top,
                     "colors": "".join(k for k, _ in colors.most_common(3)), "members": sorted(members)})
    return rows


P("# FRA synergy graph — generated report (`evaluate.py`, do not edit)")
P()
P(f"Cards: {len(names)}. Directed matches: {len(edges)} "
  f"({dict(collections.Counter(x['type'] for x in edges))}).")
P()
P("## 1. Schemes")
P()
P("| scheme | undirected edges | Louvain modularity | seed stability (NMI, 20 seeds) | communities |")
P("|---|---|---|---|---|")
for s in SCHEMES:
    g = graph["schemes"][s]
    sizes = sorted(collections.Counter(g["communities"].values()).values(), reverse=True)
    P(f"| {s} | {g['n_edges']} | {g['modularity']:.3f} | {g['seed_stability_nmi']:.3f} | {sizes} |")
P()
P("Cross-scheme agreement (NMI): " + ", ".join(f"{k} {v}" for k, v in graph["cross_scheme_nmi"].items()))
P()
EV["profiles"] = {}
for s, tag in (("full_knn", "a"), ("full", "b"), ("rarity", "c")):
    rows = profile(s)
    EV["profiles"][s] = rows
    P(f"## 2{tag}. Communities under `{s}`")
    P()
    for r in rows:
        tp = ", ".join(f"{p} {v:.0%}" for p, v in r["top_prims"])
        P(f"**C{r['id']}** ({r['size']} cards, colours {r['colors']}) — primitives: {tp}")
        P(f"  core: {', '.join(r['core'])}")
        P()

# ---------------- colour coherence (post-hoc) ----------------
def nmi(p, q):
    keys = list(p); n = len(keys)
    cp = collections.Counter(p[k] for k in keys); cq = collections.Counter(q[k] for k in keys)
    j = collections.Counter((p[k], q[k]) for k in keys)
    mi = sum(v / n * math.log((v / n) / ((cp[a] / n) * (cq[b] / n))) for (a, b), v in j.items())
    h = lambda c: -sum(v / n * math.log(v / n) for v in c.values())
    return 2 * mi / (h(cp) + h(cq)) if h(cp) + h(cq) else 1.0


COL = {n: "".join(c["colors"]) or "C" for n, c in cards.items()}
P("## 2x. Colour coherence (post-hoc; colour is not a state-edge input)")
P()
P("Colour enters the graph only through the resource-flow colour factor. In a draft set archetypes are "
  "colour pairs, so communities that align with colour identity are recovering real structure. "
  "**Added after the first results, not pre-registered.** NMI(community, colour identity) vs 200 label shuffles.")
P()
P("| scheme | NMI with colour | shuffled mean | max shuffled |")
P("|---|---|---|---|")
EV["colour_nmi"] = {}
rng = random.Random(1)
for s in SCHEMES:
    obs = nmi(LAB[s], COL)
    vals = list(LAB[s].values()); sh = []
    for _ in range(200):
        rng.shuffle(vals); sh.append(nmi(dict(zip(LAB[s].keys(), vals)), COL))
    EV["colour_nmi"][s] = {"obs": obs, "shuffled_mean": sum(sh) / len(sh), "shuffled_max": max(sh)}
    P(f"| {s} | {obs:.3f} | {sum(sh)/len(sh):.3f} | {max(sh):.3f} |")
P()

# ---------------- validation ----------------
def emitters(pred):
    return sorted({c["name"] for c in cards.values() for e in c["emits"] if pred(e)})


def listeners(pred):
    return sorted({c["name"] for c in cards.values() for l in c["listens"] if pred(l)})


def cocluster(S, T, s, trials=2000, seed=0):
    lab = LAB[s]
    pairs = [(a, b) for a in S for b in T if a != b]
    obs = sum(lab[a] == lab[b] for a, b in pairs) / len(pairs)
    rng = random.Random(seed)
    vals = list(lab.values())
    ge = 0; tot = 0.0
    for _ in range(trials):
        rng.shuffle(vals)
        perm = dict(zip(lab.keys(), vals))
        r = sum(perm[a] == perm[b] for a, b in pairs) / len(pairs)
        tot += r; ge += r >= obs
    return obs, tot / trials, (ge + 1) / (trials + 1)


P("## 3. Validation (plan's three known-good checks)")
P()
surv = emitters(lambda e: e["event"] == "surveil")
gy_pay = listeners(lambda l: l["event"] == "tograve" and l["mech"] in ("condition", "trigger", "cost_mod"))
P(f"### V1 surveil enablers ↔ graveyard-count payoffs")
P()
P(f"{len(surv)} surveil emitters; {len(gy_pay)} graveyard-size payoffs (Count$ValidGraveyard, Threshold, graveyard triggers).")
P()
P("| scheme | same-community rate | shuffled-label baseline | p (one-sided, 2000 perms) | direct edges S→P / pairs |")
P("|---|---|---|---|---|")
EV["V1"] = {}
direct = sum(1 for a in surv for b in gy_pay if (a, b) in REASON and any(k.startswith("tograve") for k in REASON[(a, b)]))
npairs = sum(1 for a in surv for b in gy_pay if a != b)
for s in SCHEMES:
    obs, base, p = cocluster(surv, gy_pay, s)
    EV["V1"][s] = {"obs": obs, "base": base, "p": p}
    P(f"| {s} | {obs:.3f} | {base:.3f} | {p:.4f} | {direct}/{npairs} |")
P()
P("Payoffs: " + ", ".join(gy_pay))
P()

P("### V2 loyalty adders → 'whenever you put loyalty counters on a planeswalker'")
P()
loy_l = listeners(lambda l: l["event"] == "counter+" and l["sub"] == "LOYALTY" and l["mech"] == "trigger")
loy_e = emitters(lambda e: e["event"] == "counter+" and e["sub"] == "LOYALTY")
EV["V2"] = {}
for L in loy_l:
    got = [a for a in loy_e if (a, L) in REASON and any(k.startswith("counter+:LOYALTY") for k in REASON[(a, L)])]
    nb = [n for n, _ in neighbours(L, "full", 280)]
    ranks = sorted(nb.index(a) + 1 for a in got if a in nb)
    EV["V2"][L] = {"loyalty_emitters": len(loy_e), "linked": len(got), "median_rank_full": ranks[len(ranks) // 2] if ranks else None}
    P(f"`{L}`: {len(got)}/{len(loy_e)} loyalty emitters link to it by `counter+:LOYALTY`. "
      f"Their rank among its {len(nb)} neighbours under `full`: median {ranks[len(ranks)//2] if ranks else '—'}, "
      f"best {ranks[0] if ranks else '—'}. Same community under full: "
      f"{sum(LAB['full'][a] == LAB['full'][L] for a in got)}/{len(got)}.")
    P()
    P("Top-10 neighbours (full): " + "; ".join(f"{n} {v:.3f}" for n, v in neighbours(L, "full", 10)))
    P()
# pre-registration item 4: Empower must not feed a PW card's SubCounter fuel
bad = [x for x in edges if x["prim"] == "counter+:LOYALTY" and "Empower" in x["emit"] and "Cost$ -LOYALTY" in x["listen"]]
EV["prereg4_violations"] = len(bad)
P(f"Pre-registration check 4 (Empower → PW card SubCounter fuel edges): **{len(bad)}** (must be 0).")
P()

P("### V3 Chandra, Torch of Defiance → top end / X spells (resource flow)")
P()
ch = "Chandra, Torch of Defiance"
res = [x for x in edges if x["a"] == ch and x["type"] == "resource"]
cons = sorted({x["b"] for x in res})
kw_ch = set(cards[ch]["keywords"])
shared_kw = [b for b in cons if kw_ch & set(cards[b]["keywords"])]
kw_in_reason = [x for x in res if re.search(r"\bK:", x["listen"] + x["emit"])]
EV["V3"] = {"consumers": len(cons), "shared_keyword": len(shared_kw), "keyword_in_reason": len(kw_in_reason)}
P(f"{len(cons)} resource-flow consumers. Chandra's keywords: {sorted(kw_ch) or 'none'}. "
  f"Consumers sharing a keyword: {len(shared_kw)}. Resource edges whose reason cites a keyword: {len(kw_in_reason)} (pre-reg 2: must be 0).")
P()
top = sorted(res, key=lambda x: -x["w"]["full"])[:12]
P("| consumer | MV / cost | reason | w(full) |")
P("|---|---|---|---|")
for x in top:
    P(f"| {x['b']} | {cards[x['b']]['mana_cost']} | {x['listen']} | {x['w']['full']:.3f} |")
P()
nb_all = [n for n, _ in neighbours(ch, "full", 280)]
def strongest(a, b):
    rs = list(REASON.get((a, b), {}).values()) + list(REASON.get((b, a), {}).values())
    return max(rs, key=lambda x: x["w"]["full"]) if rs else None
pure = [b for b in cons if strongest(ch, b)["type"] == "resource"]
first_res = min((nb_all.index(b) + 1 for b in cons if b in nb_all), default=None)
first_pure = min((nb_all.index(b) + 1 for b in pure if b in nb_all), default=None)
EV["V3"].update({"best_any_consumer_rank_full": first_res, "pure_resource_consumers": len(pure),
                 "best_pure_resource_rank_full": first_pure})
P(f"Among Chandra's {len(nb_all)} neighbours under `full`: best consumer of any kind ranks {first_res} "
  f"(that one is linked by other edges too); {len(pure)} consumers have resource flow as their *strongest* link, the best of "
  f"which ranks {first_pure}. "
  "Mana is a common primitive (25 emitters, 84 listeners), so rarity weighting ranks these edges low; "
  "they are present but not what the combined weight surfaces first.")
P()
P("Chandra top-10 neighbours overall (full): " + "; ".join(f"{n} {v:.3f}" for n, v in neighbours(ch, "full", 10)))
P()

# ---------------- held-out labels ----------------
P("## 4. Held-out check: Forge's hand-authored DeckHas / DeckHints")
P()
P("Forge authors tag some cards `DeckHints:Ability$Graveyard` (\"this card wants graveyard enablers\") and others "
  "`DeckHas:Ability$Graveyard`. Neither is an input. For each hinted card, take its top-10 neighbours and ask what "
  "fraction carry the matching `DeckHas` (for `Type$X` hints: have type X). Baseline = the label's rate over all "
  "other cards. Wilson 95% intervals. Small n — these are sanity rows, not results.")
P()


def labels(raw_list):
    out = set()
    for raw in raw_list:
        for part in re.split(r"\s*&\s*|\s*\|\s*", raw):
            kind, _, vals = part.partition("$")
            for v in vals.split(","):
                v = v.strip().lower().replace("lifegain", "lifegain").replace("tokens", "token")
                if v:
                    out.add(f"{kind.strip()}${v}")
    return out


HAS = {n: labels(c["deck_has"]) for n, c in cards.items()}
HINT = {n: labels(c["deck_hints"]) for n, c in cards.items()}


def has_label(n, lab):
    kind, v = lab.split("$")
    if kind == "Type":
        return v in {t.lower() for t in cards[n]["types"]} or lab in HAS[n]
    return lab in HAS[n] or (v == "lifegain" and "Ability$lifegain" in HAS[n])


EV["heldout"] = {}
P("| scheme | hinted (card,label) pairs | hits in top-10 | rate [95% CI] | baseline rate | lift |")
P("|---|---|---|---|---|---|")
for s in SCHEMES:
    hits = n = 0; base_k = base_n = 0
    for c, hs in HINT.items():
        for lab in hs:
            nb = [m for m, _ in neighbours(c, s, 10)]
            hits += sum(has_label(m, lab) for m in nb); n += len(nb)
            others = [m for m in names if m != c]
            base_k += sum(has_label(m, lab) for m in others); base_n += len(others)
    p, lo, hi = wilson(hits, n)
    b = base_k / base_n if base_n else 0
    EV["heldout"][s] = {"hits": hits, "n": n, "rate": p, "lo": lo, "hi": hi, "base": b}
    P(f"| {s} | {n // 10} | {hits}/{n} | {p:.3f} [{lo:.3f}, {hi:.3f}] | {b:.3f} | {p / b if b else 0:.2f}× |")
P()

# ---------------- sparse / lonely edges ----------------
P("## 5. Sparse edges — scarce enablers and lonely emissions")
P()
P("Intrinsic emissions (being a creature, being cast) and resource edges are excluded here.")
P()
EFF = collections.defaultdict(set)   # (listener card, listener src) -> real emitters
for x in edges:
    if x["emit_mech"] != "intrinsic" and x["type"] != "resource":
        EFF[(x["b"], x["listen"])].add(x["a"])
P("### 5a. Scarce enablers — listeners that ≤ 3 cards in the set can satisfy")
P()
P("Grouped by (primitive, the set of cards that can satisfy it). These are the cards a whole group of "
  "listeners depends on.")
P()
grp = collections.defaultdict(set)
for x in edges:
    if x["emit_mech"] == "intrinsic" or x["type"] == "resource":
        continue
    em = EFF[(x["b"], x["listen"])]
    if len(em) <= 3:
        grp[(x["prim"], tuple(sorted(em)))].add(x["b"])
rows = sorted(grp.items(), key=lambda kv: (len(kv[0][1]), -len(kv[1])))
EV["scarce"] = [{"prim": p, "enablers": list(e), "listeners": sorted(l)} for (p, e), l in rows]
P("| primitive | the only enablers | # listener cards | listeners (first 6) |")
P("|---|---|---|---|")
for (p, e), l in rows[:30]:
    P(f"| {p} | {', '.join(e)} | {len(l)} | {', '.join(sorted(l)[:6])} |")
P()
P("### 5b. Lonely emissions — a card emitting something ≤ 3 other cards listen for")
P()
lon = collections.defaultdict(set)
for x in edges:
    if x["emit_mech"] == "intrinsic" or x["type"] == "resource" or x["m_emit"] > 3:
        continue
    lon[(x["a"], x["prim"], x["emit"])].add(x["b"])
byl = collections.defaultdict(set)   # (primitive, listener set) -> emitters
for (a, p, e), l in lon.items():
    byl[(p, tuple(sorted(l)))].add(a)
rows = sorted(byl.items(), key=lambda kv: (len(kv[0][1]), -len(kv[1])))
EV["lonely"] = [{"prim": p, "listeners": list(l), "emitters": sorted(a)} for (p, l), a in rows]
P("Grouped by (primitive, the listener set).")
P()
P("| primitive | listened for only by | # emitters | emitters (first 8) |")
P("|---|---|---|---|")
for (p, l), a in rows[:30]:
    P(f"| {p} | {', '.join(l)} | {len(a)} | {', '.join(sorted(a)[:8])} |")
P()
P(f"({len(lon)} lonely emissions in {len(rows)} groups.)")
P()

P("## 6. Top pairs overall under `full` with no shared keyword (each card at most twice)")
P()
P("Hub-capped: Tam, the Possibility pairs with every planeswalker (cost reduction + proliferate) and would "
  "otherwise fill the list.")
P()
pairs = sorted(((v, k) for k, v in graph["schemes"]["full"]["weights"].items()), reverse=True)
P("| pair | w(full) | why (top reasons) |")
P("|---|---|---|")
cnt = 0
USED = collections.Counter()
for v, k in pairs:
    a, b = k.split("|||")
    if set(cards[a]["keywords"]) & set(cards[b]["keywords"]):
        continue
    if USED[a] >= 2 or USED[b] >= 2:
        continue
    USED[a] += 1; USED[b] += 1
    P(f"| {a} ⟷ {b} | {v:.3f} | {why(a, b, 2)} |")
    cnt += 1
    if cnt >= 25:
        break
P()

open("GRAPH-REPORT.md", "w", encoding="utf-8").write("\n".join(OUT) + "\n")
json.dump(EV, open("eval.json", "w"), indent=1, ensure_ascii=False, default=str)
print(json.dumps({k: EV[k] for k in ("V1", "V2", "V3", "prereg4_violations", "heldout", "colour_nmi")}, default=str)[:3000])

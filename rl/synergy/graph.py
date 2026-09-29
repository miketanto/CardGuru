"""Build the emit->listen card graph, weight it four ways, cluster it.

Input:  fra_signals.json (signals.py)
Output: fra_edges.json   every directed match with its reason
        fra_graph.json   per-scheme undirected weights + communities
Nothing here reads deck_has / deck_hints; evaluate.py does.

Weighting schemes (the A/B the plan asks for):
  uniform  every matched (emitter-signal, listener-signal) group = 1
  tight    EMIT_T[mech] * LISTEN_T[mech] * pattern quality q
  rarity   pairing rarity: log(N/m_l) * log(N/m_e) / log(N)^2, where m_l is
           how many cards satisfy this listener and m_e how many cards this
           emission satisfies. 1.0 = the only emitter for the only listener.
  full     tight * rarity
Within an ordered pair (A->B) matches are grouped by primitive (event:sub);
each group contributes its max, groups add. Undirected w = w(A->B)+w(B->A).
"""
import json, math, sys, collections, random
import networkx as nx
from signals import EMIT_T, LISTEN_T

SCHEMES = ("uniform", "tight", "rarity", "full", "full_knn", "mutual_knn", "norm_knn")
KNN = 10  # full_knn: keep an edge only if it is in either endpoint's top-KNN under full


def match(e, l, owner_types):
    """Pattern quality in (0,1] if emission e satisfies listener l, else 0.
    owner_types: the listener card's own types (for self listeners)."""
    if e["event"] != l["event"]:
        return 0.0
    if e["event"] == "counter+":
        if not (e["sub"] == l["sub"] or "*" in (e["sub"], l["sub"])):
            return 0.0
    ep, lp = e["pat"], l["pat"]
    if e["event"] == "tograve" and e["mech"] == "intrinsic" and not (lp["types"] or lp.get("also")):
        return 0.0  # a spell resolving is not an enabler for "cards in graveyard" (§13)
    if lp["side"] == "you" and ep["side"] == "opp":
        return 0.0
    if lp.get("side") == "you" and ep.get("side") == "any" and e["mech"] == "random" and e["event"] == "die":
        return 0.0  # removal aimed at 'any creature' is not your own death trigger
    if lp["self"]:
        # something must be able to do this to *this* card: a pattern, not a
        # concrete other object, and never a token-only effect.
        if ep.get("concrete") or ep.get("self") or ep.get("token") is True:
            return 0.0
        et = ep["types"]
        if et and not set(et) <= set(owner_types):
            return 0.0
        if set(ep.get("neg") or []) & set(owner_types):
            return 0.0
        return 1.0 if et else 0.5
    lt = (lp["types"] or []) + (lp.get("also") or [])
    if lp.get("token") is not None and ep.get("token") is not None and lp["token"] != ep["token"]:
        return 0.0
    if lp.get("prepared") and not ep.get("prepared"):
        return 0.0
    if ep.get("concrete"):
        et = set(ep["types"])
        if lt and not set(lt) <= et:
            return 0.0
        if set(lp.get("neg") or []) & et:
            return 0.0
        if lp.get("token") is True and not ep.get("token"):
            return 0.0
        return 1.0
    et = ep["types"] or []
    if set(lp.get("neg") or []) & set(et):
        return 0.0
    if not lt and not lp.get("neg"):
        return 1.0  # listener accepts any object: a generic emission is an exact fit
    if lt and et:
        if set(lt) <= set(et) or set(et) <= set(lt):
            return 1.0 if set(lt) == set(et) else 0.75
        return 0.0
    return 0.5  # emission generic, listener specific (mill 'a card' vs 'instants in graveyard')


def cost_shape(cost):
    """'3 R R' -> (3, [{'R'}, {'R'}]). A pip is the set of colours that pay it,
    or 'any' (2/W, Phyrexian: payable with generic mana or life)."""
    gen, pips = 0, []
    for t in (cost or "").split():
        if t.isdigit():
            gen += int(t)
        elif t in ("X", "Y", "Z", "S"):
            continue
        elif "/" in t:
            parts = t.split("/")
            pips.append("any" if any(x.isdigit() or x == "P" for x in parts) else set(parts))
        else:
            pips.append({t})
    return gen, pips


def resource_q(e, l, consumer):
    """Curve-aware resource weight (SYNERGY-GRAPH.md §11.1)."""
    gen, pips = cost_shape(l.get("cost", ""))
    have = set(e.get("colors") or [])
    payable = sum(1 for p in pips if p == "any" or (p & have))
    eff = min(e.get("amount", 1), gen + payable)
    if eff <= 0:
        return 0.0
    kind = l.get("kind", "cast")
    if kind == "x":
        return min(1.0, eff / 2)
    if kind == "sink":
        return min(1.0, eff / max(1, gen + len(pips)))
    mv = l.get("mv", consumer["cmc"])
    saved = mv - max(e.get("ready", 1), mv - eff)
    return min(1.0, saved / 2) if saved >= 1 else 0.0


def cost_mod_q(e, target):
    """cost_mod emission is a pattern over the cards whose cost it changes."""
    if "Land" in target["front_types"]:
        return 0.0
    fake = {"event": "x", "sub": "", "mech": "intrinsic",
            "pat": {"types": target["front_types"], "neg": [], "token": False, "side": "you",
                    "self": False, "concrete": True}}
    lst = {"event": "x", "sub": "", "mech": "trigger", "pat": e["pat"]}
    return match(fake, lst, target["types"])


def build(cards):
    N = len(cards)
    raw = []  # (a, b, ei, li, q, etype)
    for bi, B in enumerate(cards):
        for li, l in enumerate(B["listens"]):
            for ai, A in enumerate(cards):
                if ai == bi:
                    continue
                for ei, e in enumerate(A["emits"]):
                    if e["event"] != l["event"]:
                        continue
                    if l["event"] == "mana" and l["mech"] == "resource":
                        q = resource_q(e, l, B); et = "resource"
                    else:
                        q = match(e, l, B["types"]); et = "cost" if l["mech"] == "cost_mod" else "state"
                    if q > 0:
                        raw.append((ai, bi, ei, li, q, et))
    for ai, A in enumerate(cards):
        for ei, e in enumerate(A["emits"]):
            if e["event"] != "cost_mod" or e.get("sign", -1) > 0:
                continue  # RaiseCost is a tax on the matching cards: anti-synergy, not an edge
            for bi, B in enumerate(cards):
                if bi != ai:
                    q = cost_mod_q(e, B)
                    if q > 0:
                        raw.append((ai, bi, ei, -1, q, "cost"))
    # rarity counts: how many distinct cards each listener / emission pairs with
    m_l = collections.defaultdict(set); m_e = collections.defaultdict(set)
    for ai, bi, ei, li, q, et in raw:
        m_l[(bi, li)].add(ai); m_e[(ai, ei)].add(bi)
    logN2 = math.log(N) ** 2
    edges = []
    for ai, bi, ei, li, q, et in raw:
        e = cards[ai]["emits"][ei]
        l = cards[bi]["listens"][li] if li >= 0 else {"mech": "cost_mod", "src": "matches ValidCard$", "event": "cost_mod", "sub": ""}
        rar = math.log(N / len(m_l[(bi, li)])) * math.log(N / len(m_e[(ai, ei)])) / logN2
        tight = EMIT_T[e["mech"]] * LISTEN_T[l["mech"]] * q
        edges.append({"a": cards[ai]["name"], "b": cards[bi]["name"], "type": et,
                      "prim": e["event"] + (":" + e["sub"] if e["sub"] else ""),
                      "emit": e["src"], "emit_mech": e["mech"], "listen": l["src"], "listen_mech": l["mech"],
                      "q": round(q, 3), "m_listen": len(m_l[(bi, li)]), "m_emit": len(m_e[(ai, ei)]),
                      "w": {"uniform": 1.0, "tight": round(tight, 4), "rarity": round(rar, 4),
                            "full": round(tight * rar, 4)}})
    return edges


def knn_keep(w, mutual=False):
    """Edges in the top-KNN of either endpoint (or of both, if mutual)."""
    nb = collections.defaultdict(list)
    for (a, b), v in w.items():
        nb[a].append((v, b)); nb[b].append((v, a))
    votes = collections.Counter()
    for a, lst in nb.items():
        for v, b in sorted(lst, reverse=True)[:KNN]:
            votes[tuple(sorted((a, b)))] += 1
    need = 2 if mutual else 1
    return {k: v for k, v in w.items() if votes[k] >= need}


def pair_weights(edges, scheme):
    # hub damping (SYNERGY-GRAPH.md §12): mutual_knn drops edges a hub cannot
    # reciprocate; norm_knn divides by sqrt(strength_a * strength_b) first.
    if scheme == "full_knn":
        return knn_keep(pair_weights(edges, "full"))
    if scheme == "mutual_knn":
        return knn_keep(pair_weights(edges, "full"), mutual=True)
    if scheme == "norm_knn":
        w = pair_weights(edges, "full")
        s = collections.defaultdict(float)
        for (a, b), v in w.items():
            s[a] += v; s[b] += v
        return knn_keep({k: v / math.sqrt(s[k[0]] * s[k[1]]) for k, v in w.items()})
    best = collections.defaultdict(float)
    for x in edges:
        k = (x["a"], x["b"], x["prim"], x["type"])
        best[k] = max(best[k], x["w"][scheme])
    w = collections.defaultdict(float)
    for (a, b, _, _), v in best.items():
        w[tuple(sorted((a, b)))] += v
    return w


def nmi(p, q):
    keys = list(p)
    n = len(keys)
    cp = collections.Counter(p[k] for k in keys); cq = collections.Counter(q[k] for k in keys)
    j = collections.Counter((p[k], q[k]) for k in keys)
    mi = sum(v / n * math.log((v / n) / ((cp[a] / n) * (cq[b] / n))) for (a, b), v in j.items())
    h = lambda c: -sum(v / n * math.log(v / n) for v in c.values())
    hp, hq = h(cp), h(cq)
    return 1.0 if hp == hq == 0 else 2 * mi / (hp + hq)


def cluster(names, w, seeds=20):
    G = nx.Graph()
    G.add_nodes_from(names)
    for (a, b), v in w.items():
        if v > 0:
            G.add_edge(a, b, weight=v)
    runs = []
    for s in range(seeds):
        comms = nx.community.louvain_communities(G, weight="weight", seed=s, resolution=1.0)
        mod = nx.community.modularity(G, comms, weight="weight")
        lab = {n: i for i, c in enumerate(sorted(comms, key=len, reverse=True)) for n in c}
        runs.append((mod, lab))
    runs.sort(key=lambda r: -r[0])
    best_mod, best = runs[0]
    stab = [nmi(best, r[1]) for r in runs[1:]]
    return G, best, best_mod, sum(stab) / len(stab)


def main():
    cards = json.load(open(sys.argv[1], encoding="utf-8"))
    edges = build(cards)
    json.dump(edges, open("fra_edges.json", "w"), indent=0, ensure_ascii=False)
    names = [c["name"] for c in cards]
    out = {"schemes": {}}
    for s in SCHEMES:
        w = pair_weights(edges, s)
        G, lab, mod, stab = cluster(names, w)
        out["schemes"][s] = {"modularity": round(mod, 4), "seed_stability_nmi": round(stab, 4),
                             "n_edges": G.number_of_edges(),
                             "isolated": sorted(n for n in names if G.degree(n) == 0),
                             "communities": lab,
                             "weights": {f"{a}|||{b}": round(v, 4) for (a, b), v in w.items()}}
        sizes = collections.Counter(lab.values())
        print(f"{s:8s} edges={G.number_of_edges()} mod={mod:.3f} stab={stab:.3f} "
              f"isolated={len(out['schemes'][s]['isolated'])} sizes={sorted(sizes.values(), reverse=True)[:12]}")
    labs = {s: out["schemes"][s]["communities"] for s in SCHEMES}
    out["cross_scheme_nmi"] = {f"{a}~{b}": round(nmi(labs[a], labs[b]), 3)
                               for i, a in enumerate(SCHEMES) for b in SCHEMES[i + 1:]}
    print("cross-scheme NMI", out["cross_scheme_nmi"])
    print("directed matches", len(edges), collections.Counter(x["type"] for x in edges))
    json.dump(out, open("fra_graph.json", "w"), ensure_ascii=False)


if __name__ == "__main__":
    main()

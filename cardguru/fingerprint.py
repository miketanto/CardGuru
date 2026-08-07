"""Per-deck fingerprint graph: what makes THIS deck run, and where to cut it.

Projects the global knowledge graph onto one decklist and keeps only
intra-deck structure: nodes are the deck's functional cards (weighted by
copies), edges are enabler->payoff relations mined from the synergy hooks.
Analysis is then graph-theoretic - centrality finds linchpins, sole-provider
detection finds non-redundant dependencies - and each linchpin gets its
exposure windows (hand/stack/battlefield/graveyard) with a preferred
interdiction, so the output answers "WHICH card needs killing, and HOW"
rather than "what kills card X".

Design notes: research/answer-frames-and-deck-fingerprints.md
"""
from __future__ import annotations

from .answers import threat_profile
from .deck import _matches, detect_roles
from .recommend import HOOKS, detect_hooks

# ------------------------------------------------------------ node typing


def _is_wincon(rec: dict) -> bool:
    """Can this card, by itself, move the opponent toward zero?"""
    types = rec.get("types") or ""
    pt = rec.get("pt") or ""
    if "Creature" in types and pt:
        try:
            if int(pt.split("/")[0]) >= 1:
                return True
        except ValueError:
            return True                     # */* attackers count
    if "Planeswalker" in types:
        return True
    for n in rec.get("nodes") or []:
        p = n.get("params") or {}
        if n.get("api") == "DealDamage" and "Player" in str(p.get("ValidTgts", "")):
            return True
        if n.get("api") == "LoseLife" and "Player" in \
                str(p.get("Defined", "")) + str(p.get("ValidTgts", "")):
            return True
    if "Land" in types and any(n.get("api") == "Animate"
                               for n in rec.get("nodes") or []):
        return True                         # creature-land clocks
    return False


def _interaction_classes(rec: dict) -> list[str]:
    """What the deck defends/disrupts with (not part of its own engine)."""
    out = []
    for n in rec.get("nodes") or []:
        p = n.get("params") or {}
        api = n.get("api")
        if api == "Counter" and n.get("apiKind") == "SP":
            out.append("counterspell")
        elif api == "Destroy" and "ValidTgts" in p:
            out.append("removal")
        elif api == "ChangeZone" and p.get("Destination") == "Exile" \
                and p.get("Origin") in ("Battlefield", None) and "ValidTgts" in p:
            out.append("removal")
        elif api == "Discard" and "Opp" in str(p.get("Defined", "")) \
                + str(p.get("ValidTgts", "")):
            out.append("hand_attack")
        elif api == "Tap" and "ValidTgts" in p:
            out.append("tempo")
    seen, uniq = set(), []
    for c in out:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    return uniq


# ------------------------------------------------------------ graph build


def build_fingerprint(by_name: dict, decklist: list[tuple[str, int]]) -> dict:
    cards = []
    for name, count in decklist:
        rec = by_name.get(name)
        if rec is None:
            continue
        types = rec.get("types") or ""
        if "Basic" in types:
            continue                        # mana substrate, not structure
        cards.append((name, count, rec))

    nodes = {}
    for name, count, rec in cards:
        nodes[name] = {
            "copies": count,
            "roles": detect_roles(rec),
            "wincon": _is_wincon(rec),
            "interaction": _interaction_classes(rec),
            "mv": threat_profile(rec)["mv"],
        }

    # enabler -> payoff edges: payoff's hook complement matched by enabler
    edges = []
    for pname, _pc, prec in cards:
        for hook in detect_hooks(prec):
            for cname, query in HOOKS[hook]["complements"].items():
                for ename, ecount, erec in cards:
                    if ename == pname:
                        continue
                    if _matches(erec, query):
                        edges.append({
                            "enabler": ename, "payoff": pname,
                            "via": f"{hook}/{cname}",
                            "weight": min(ecount, 4)})

    # weighted degree
    degree = {n: 0 for n in nodes}
    for e in edges:
        w = e["weight"]
        degree[e["enabler"]] += w
        degree[e["payoff"]] += w

    # betweenness (Brandes, unweighted, undirected) on the simple graph
    adj = {n: set() for n in nodes}
    for e in edges:
        adj[e["enabler"]].add(e["payoff"])
        adj[e["payoff"]].add(e["enabler"])
    betweenness = {n: 0.0 for n in nodes}
    for s in nodes:
        stack, preds = [], {n: [] for n in nodes}
        sigma = {n: 0 for n in nodes}
        sigma[s] = 1
        dist = {n: -1 for n in nodes}
        dist[s] = 0
        queue = [s]
        while queue:
            v = queue.pop(0)
            stack.append(v)
            for w in adj[v]:
                if dist[w] < 0:
                    dist[w] = dist[v] + 1
                    queue.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    preds[w].append(v)
        delta = {n: 0.0 for n in nodes}
        while stack:
            w = stack.pop()
            for v in preds[w]:
                delta[v] += sigma[v] / sigma[w] * (1 + delta[w])
            if w != s:
                betweenness[w] += delta[w]

    # sole/thin providers: for each (payoff, hook-family) need, who supplies it?
    needs: dict[tuple, set] = {}
    for e in edges:
        fam = e["via"].split("/")[0]
        needs.setdefault((e["payoff"], fam), set()).add(e["enabler"])
    sole_provider: dict[str, list] = {}
    for (payoff, fam), providers in needs.items():
        if len(providers) == 1:
            p = next(iter(providers))
            sole_provider.setdefault(p, []).append(f"{payoff} needs {fam}")

    # linchpin score: centrality x availability, with a bonus for being the
    # only card supplying some dependency (no parallel path = min-cut member)
    max_b = max(betweenness.values()) or 1.0
    scores = {}
    for n, meta in nodes.items():
        avail = min(meta["copies"], 4) / 4.0
        s = (degree[n] + 6.0 * betweenness[n] / max_b
             + 5.0 * len(sole_provider.get(n, []))) * (0.5 + 0.5 * avail)
        if meta["wincon"]:
            s += 1.0
        scores[n] = round(s, 2)
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])

    # engine spine: the dominant edge families, human-readable
    fam_weight: dict[str, int] = {}
    fam_pairs: dict[str, set] = {}
    for e in edges:
        fam = e["via"].split("/")[0]
        fam_weight[fam] = fam_weight.get(fam, 0) + e["weight"]
        fam_pairs.setdefault(fam, set()).add((e["enabler"], e["payoff"]))
    spine = [{"family": f, "weight": w,
              "enablers": sorted({a for a, _b in fam_pairs[f]}),
              "payoffs": sorted({b for _a, b in fam_pairs[f]})}
             for f, w in sorted(fam_weight.items(), key=lambda kv: -kv[1])]

    return {"nodes": nodes, "edges": edges, "degree": degree,
            "betweenness": {k: round(v, 1) for k, v in betweenness.items()},
            "sole_provider": sole_provider, "linchpins": ranked,
            "spine": spine}


# ------------------------------------------------------------ break plan


def _interdiction(rec: dict, meta: dict) -> dict:
    """Exposure windows for one linchpin, with the preferred permanent cut."""
    prof = threat_profile(rec)
    windows, avoid = [], []
    mv = meta.get("mv")
    windows.append({"window": "hand",
                    "note": f"hand attack works until ~turn {mv or '?'}"
                            " (proactive, full information, decays to topdecks)"})
    if prof["uncounterable"]:
        avoid.append({"window": "stack", "note": "can't be countered"})
    else:
        windows.append({"window": "stack",
                        "note": "counter is history-clean: on-cast/death "
                                "triggers never exist"})
    if prof["hexproof"] or prof["shroud"]:
        avoid.append({"window": "battlefield-targeted",
                      "note": "hexproof/shroud: use edicts or sweepers"})
    if prof["recursive"]:
        avoid.append({"window": "battlefield-destroy",
                      "note": "returns when it dies: destroy is rental - "
                              "use EXILE, an exile-rider, or counter it"})
        preferred = "stack (counter)" if not prof["uncounterable"] \
            else "battlefield (exile only)"
    elif prof["hexproof"] or prof["shroud"]:
        preferred = "stack (counter)" if not prof["uncounterable"] \
            else "battlefield (non-targeted: edict/sweeper)"
    elif prof["indestructible"]:
        preferred = "battlefield (exile / -X-X), or stack"
        avoid.append({"window": "battlefield-destroy",
                      "note": "indestructible"})
    else:
        windows.append({"window": "battlefield",
                        "note": "ordinary removal window"})
        preferred = "cheapest available (no protections detected)"
    return {"card": rec.get("name"), "windows": windows, "avoid": avoid,
            "preferred": preferred, "ward": prof["ward"]}


def break_plan(by_name: dict, fp: dict, top: int = 3) -> list[dict]:
    plans = []
    for name, score in fp["linchpins"][:top]:
        rec = by_name.get(name)
        if rec is None:
            continue
        plan = _interdiction(rec, fp["nodes"][name])
        plan["score"] = score
        plan["why_linchpin"] = fp["sole_provider"].get(name, [])
        plans.append(plan)
    return plans

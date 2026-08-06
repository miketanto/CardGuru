"""Decklist parsing + Commander deck analysis.

`parse_decklist` accepts the common text formats:
    1 Sol Ring          |  1x Sol Ring       |  Sol Ring
    (MTGO/Arena-style "1 Sol Ring (C21) 263" set/number suffixes are dropped)
Blank lines and lines starting with // or # are ignored; a "Sideboard" header
ends mainboard parsing.

`analyze_deck` produces the hook coverage matrix: which of the commander's
synergy hooks each deck card feeds (via the hook's complement queries), where
the deck is thin, and which cards connect to nothing (candidate cuts).
"""
from __future__ import annotations

import re

from .querydsl import CardGraph, evaluate
from .recommend import HOOKS, detect_hooks

_LINE = re.compile(r"^\s*(?:(\d+)\s*x?\s+)?(.+?)\s*(?:\((\w+)\)\s*[\w-]*)?\s*$")


def parse_decklist(text: str) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("//", "#")):
            continue
        if line.lower().rstrip(":") in ("sideboard", "maybeboard", "commander"):
            break
        m = _LINE.match(line)
        if not m:
            continue
        count = int(m.group(1) or 1)
        name = m.group(2).strip()
        if name:
            out.append((name, count))
    return out


def _matches(rec: dict, query: dict) -> bool:
    ok, _evidence = evaluate(query, CardGraph(rec))
    return ok


def cross_synergy(by_name: dict, commander_rec: dict,
                  decklist: list[tuple[str, int]], max_edges: int = 400) -> dict:
    """Deck-internal synergy graph: EVERY deck card (commander included) gets
    hook detection, and each hooked card's complement queries are tested
    against the other deck cards. An edge (src)-[hook/class]->(dst) means
    dst's structure feeds src's hook — with the machine-readable WHY."""
    cards = [(commander_rec["name"], commander_rec)]
    for name, _count in decklist:
        rec = by_name.get(name)
        if rec is not None and name != commander_rec["name"]:
            cards.append((name, rec))

    edges = []
    for src_name, src_rec in cards:
        for hook in detect_hooks(src_rec):
            cfg = HOOKS[hook]
            for cname, query in cfg["complements"].items():
                for dst_name, dst_rec in cards:
                    if dst_name == src_name:
                        continue
                    if _matches(dst_rec, query):
                        edges.append({
                            "src": src_name, "hook": hook, "class": cname,
                            "dst": dst_name,
                            "why": f"{src_name} {cfg['describe']}; "
                                   f"{dst_name} matches its '{cname}' complement"})
                        if len(edges) >= max_edges:
                            break

    degree: dict[str, int] = {}
    for e in edges:
        degree[e["src"]] = degree.get(e["src"], 0) + 1
        degree[e["dst"]] = degree.get(e["dst"], 0) + 1
    core = sorted(degree.items(), key=lambda kv: -kv[1])
    isolated = [n for n, _r in cards if n not in degree]
    return {"edges": edges, "engine_core": core[:10], "isolated": isolated,
            "n_cards": len(cards), "n_edges": len(edges)}


COLOR_LETTERS = set("WUBRG")

# Role EFFECT queries: what the card does. Repeatability (one-shot spell vs
# permanent engine) is determined separately by the card's node kinds.
_ROLE_QUERIES = {
    "ramp": {"any": [
        {"node": {"kind": "A", "apiKind": "AB", "api": {"any": ["Mana", "ManaReflected"]},
                  "params": {"Cost": {"contains": "T"}}}},
        {"node": {"api": "ChangeZone",
                  "params": {"Origin": "Library", "Destination": "Battlefield",
                             "ChangeType": {"regex": "Land|Plains|Island|Swamp|Mountain|Forest"}}}}]},
    # one-shot draw needs 2+ cards to count; ENGINE draw counts at any size
    # (Midnight Reaper's draw-1-per-death is a draw engine, not a cantrip)
    "card_draw": {"node": {"api": "Draw",
                           "params": {"NumCards": {"regex": "^[2-9X]"}}}},
    "card_draw_engine": {"node": {"api": "Draw"}},
    "targeted_removal": {"any": [
        {"node": {"api": "Destroy", "params": {"ValidTgts": {"regex": "Creature|Permanent"}}}},
        {"node": {"api": "ChangeZone",
                  "params": {"Origin": "Battlefield", "Destination": "Exile",
                             "ValidTgts": {"regex": "Creature|Permanent"}}}}]},
    "sweepers": {"node": {"api": {"any": ["DestroyAll", "DamageAll"]},
                          "params": {"ValidCards": {"contains": "Creature"}}}},
}

ROLES = ("ramp", "card_draw", "targeted_removal", "sweepers")


def _is_engine(rec: dict) -> bool:
    """A repeatable source: the effect lives on a permanent's trigger or
    activated ability rather than a one-shot spell."""
    types = rec.get("types") or ""
    if not any(t in types for t in ("Creature", "Artifact", "Enchantment",
                                    "Planeswalker", "Land", "Battle")):
        return False
    return any(n.get("kind") in ("T", "S")
               or (n.get("kind") == "A" and n.get("apiKind") == "AB")
               for n in rec.get("nodes") or [])


def detect_roles(rec: dict) -> dict[str, str]:
    """role -> 'engine' | 'one_shot' for each role this card serves."""
    out = {}
    engine = _is_engine(rec)
    for role in ROLES:
        if role == "card_draw":
            if engine and _matches(rec, _ROLE_QUERIES["card_draw_engine"]):
                out[role] = "engine"
            elif _matches(rec, _ROLE_QUERIES["card_draw"]):
                out[role] = "engine" if engine else "one_shot"
            continue
        if _matches(rec, _ROLE_QUERIES[role]):
            out[role] = "engine" if engine else "one_shot"
    return out


# Gameplan-conditioned interaction/draw quotas. The gameplan is detected from
# the deck's own hook distribution - quotas bend to what the deck is trying to
# do instead of one template for everyone. Mana/ramp needs are NOT quota-based
# at all: the goldfish simulation measures them (see cardguru.goldfish).
GAMEPLAN_QUOTAS = {
    "aggro":        {"card_draw": 6,  "targeted_removal": 5, "sweepers": 0},
    "spellslinger": {"card_draw": 12, "targeted_removal": 6, "sweepers": 2},
    "engine":       {"card_draw": 8,  "targeted_removal": 7, "sweepers": 2},
    "graveyard":    {"card_draw": 7,  "targeted_removal": 6, "sweepers": 3},
    "generic":      {"card_draw": 9,  "targeted_removal": 7, "sweepers": 2},
}

_GAMEPLAN_HOOKS = {
    "aggro": {"attacks_matter", "combat_damage_matters", "amplifies_attack_triggers",
              "tribal_lord", "equipment_matters"},
    "spellslinger": {"spellslinger", "copies_things"},
    "graveyard": {"reanimator", "self_mill", "plays_from_graveyard",
                  "cares_about_death", "amplifies_death_triggers", "sac_outlet"},
    "engine": {"makes_tokens", "puts_counters", "gains_life", "lifedrain",
               "landfall", "blink", "amplifies_etb_triggers",
               "creatures_entering_matter", "draw_matters", "discard_matters"},
}


def detect_gameplan(hook_counts: dict[str, int]) -> str:
    scores = {}
    for plan, hookset in _GAMEPLAN_HOOKS.items():
        scores[plan] = sum(c for h, c in hook_counts.items() if h in hookset)
    best = max(scores, key=lambda p: scores[p]) if scores else "generic"
    return best if scores.get(best, 0) >= 3 else "generic"


def mana_value(mana_cost: str | None) -> int | None:
    if not mana_cost or mana_cost == "no cost":
        return None
    mv = 0
    for tok in mana_cost.split():
        if tok.isdigit():
            mv += int(tok)
        elif tok == "X":
            continue
        else:
            mv += 1          # colored or hybrid symbol
    return mv


def deck_shape(by_name: dict, commander_rec: dict,
               decklist: list[tuple[str, int]]) -> dict:
    """Mana curve, color-pip demand vs mana sources, gameplan detection, and
    gameplan-conditioned role quotas. Repeatable engines are counted separately
    from one-shot spells (an engine is worth roughly two one-shots — a draw
    engine keeps drawing). Mana/ramp sufficiency is deliberately NOT judged
    here: the goldfish simulation measures it."""
    curve: dict[int, int] = {}
    pips: dict[str, int] = {c: 0 for c in COLOR_LETTERS}
    sources: dict[str, int] = {c: 0 for c in COLOR_LETTERS}
    roles: dict[str, dict[str, list[str]]] = {
        r: {"one_shot": [], "engines": []} for r in ROLES}
    hook_counts: dict[str, int] = {}
    n_lands = 0

    for h in detect_hooks(commander_rec):
        hook_counts[h] = hook_counts.get(h, 0) + 2      # commander weighs double

    for name, count in decklist:
        rec = by_name.get(name)
        if rec is None:
            continue
        types = rec.get("types") or ""
        if "Land" in types:
            n_lands += count
            oracle = (rec.get("oracle") or "")
            for c, word in (("W", "{W}"), ("U", "{U}"), ("B", "{B}"),
                            ("R", "{R}"), ("G", "{G}")):
                if word in oracle or "any color" in oracle:
                    sources[c] += count
            continue
        mv = mana_value(rec.get("manaCost"))
        if mv is not None:
            bucket = min(mv, 7)
            curve[bucket] = curve.get(bucket, 0) + count
        for sym in (rec.get("manaCost") or "").split():
            if sym in COLOR_LETTERS:
                pips[sym] += count
        for role, kind in detect_roles(rec).items():
            roles[role]["engines" if kind == "engine" else "one_shot"].append(name)
        for h in detect_hooks(rec):
            hook_counts[h] = hook_counts.get(h, 0) + 1

    gameplan = detect_gameplan(hook_counts)
    quotas = GAMEPLAN_QUOTAS[gameplan]

    def effective(role):
        r = roles[role]
        return len(r["one_shot"]) + 2 * len(r["engines"])

    flags = []
    nonland = sum(curve.values())
    heavy = sum(v for k, v in curve.items() if k >= 5)
    if nonland and heavy / nonland > 0.30:
        flags.append(f"top-heavy curve: {heavy}/{nonland} nonland spells at MV 5+")
    for c in COLOR_LETTERS:
        if pips[c] >= 8 and sources[c] < pips[c]:
            flags.append(f"{c}: {pips[c]} pips but only {sources[c]} producing lands")
    for role, quota in quotas.items():
        if effective(role) < quota:
            flags.append(
                f"{role}: effective {effective(role)} vs ~{quota} for a "
                f"{gameplan} gameplan (engines count double)")

    return {"curve": dict(sorted(curve.items())), "lands": n_lands,
            "pips": {c: v for c, v in pips.items() if v},
            "sources": {c: v for c, v in sources.items() if v},
            "roles": {r: {k: sorted(v) for k, v in d.items()}
                      for r, d in roles.items()},
            "effective_roles": {r: effective(r) for r in ROLES},
            "gameplan": gameplan,
            "hook_counts": dict(sorted(hook_counts.items(),
                                       key=lambda kv: -kv[1])),
            "quotas": quotas,
            "flags": flags}


def suggest(idx, by_name: dict, commander_rec: dict,
            decklist: list[tuple[str, int]], ci_by_name: dict,
            printings_by_name: dict | None = None, top_n: int = 15,
            shape: dict | None = None) -> dict:
    """Ranked recommendations: candidates come from the complement queries of
    every hook present in the deck (commander included); each candidate is
    scored by how many synergy edges it would add to THIS deck (provider side:
    deck hooks it feeds; consumer side: deck cards feeding its own hooks).
    With `shape` (from deck_shape), the score is adjusted for deck needs:
    +25% per deficient role the candidate fills, -25% when the candidate sits
    in an already-fat part of the curve. Ties break on reprint count (staple
    proxy) then lower mana value."""
    from .recommend import color_identity_ok

    printings_by_name = printings_by_name or {}
    commander_ci = set(ci_by_name.get(commander_rec["name"]) or "")
    deck_names = {commander_rec["name"]} | {n for n, _c in decklist}
    deck_recs = [(n, by_name[n]) for n in deck_names if n in by_name]

    # hook sources in the deck: (card, hook) pairs
    deck_hooks = [(name, h) for name, rec in deck_recs for h in detect_hooks(rec)]

    # deck-internal coverage per hook: how many deck cards already feed it
    # (thin hooks get priority in diversified selection)
    hook_coverage: dict[str, int] = {}
    for src_name, hook in deck_hooks:
        feeders = set()
        for cname, query in HOOKS[hook]["complements"].items():
            for dn, drec in deck_recs:
                if dn != src_name and _matches(drec, query):
                    feeders.add(dn)
        hook_coverage[hook] = max(hook_coverage.get(hook, 0), len(feeders))

    # provider side: candidates matching any deck hook's complement queries
    provider_edges: dict[str, list[tuple[str, str, str]]] = {}
    for src_name, hook in deck_hooks:
        for cname, query in HOOKS[hook]["complements"].items():
            for hit in idx.search(query):
                rec = hit["record"]
                cand = rec["name"]
                if cand in deck_names:
                    continue
                if not color_identity_ok(ci_by_name.get(cand), commander_ci):
                    continue
                provider_edges.setdefault(cand, []).append((src_name, hook, cname))

    # consumer side: does the deck feed the candidate's own hooks?
    scores = []
    for cand, plinks in provider_edges.items():
        rec = by_name.get(cand)
        if rec is None:
            continue
        why = [f"feeds {s}'s {h} ({c})" for s, h, c in plinks]
        consumer = 0
        for hook in detect_hooks(rec):
            for cname, query in HOOKS[hook]["complements"].items():
                consumer += sum(1 for _dn, drec in deck_recs if _matches(drec, query))
        edges = len(why) + consumer
        score = float(edges)
        adjustments = []
        if shape:
            deficient = {r for r, quota in shape.get("quotas", {}).items()
                         if shape.get("effective_roles", {}).get(r, 0) < quota}
            cand_roles = detect_roles(rec)
            for r in deficient & set(cand_roles):
                score *= 1.35 if cand_roles[r] == "engine" else 1.25
                adjustments.append(
                    f"+{35 if cand_roles[r] == 'engine' else 25}% fills {r}"
                    + (" (engine)" if cand_roles[r] == "engine" else ""))
            mv = mana_value(rec.get("manaCost"))
            curve = shape.get("curve", {})
            nonland = sum(curve.values()) or 1
            if mv is not None and curve.get(min(mv, 7), 0) / nonland > 0.25:
                score *= 0.75
                adjustments.append(f"-25% curve already fat at MV {min(mv, 7)}")
        scores.append({
            "card": cand, "edges": edges, "score": round(score, 1),
            "provider_edges": len(why), "consumer_edges": consumer,
            "adjustments": adjustments,
            "feeds_hooks": sorted({h for _s, h, _c in plinks}),
            "fills_roles": [a.split("fills ")[1].split(" (")[0]
                            for a in adjustments if "fills" in a],
            "printings": len(printings_by_name.get(cand) or []),
            "mv": rec.get("manaCost"),
            "why": why[:4]})
    scores.sort(key=lambda s: (-s["score"], -s["printings"], str(s["mv"] or "z")))

    # ---- diversified selection: round-robin over the deck's NEEDS ----
    # buckets: deficient roles first, then hooks by ascending deck coverage
    buckets: list[tuple[str, str]] = []
    if shape:
        for r, quota in shape.get("quotas", {}).items():
            if shape.get("effective_roles", {}).get(r, 0) < quota:
                buckets.append(("role", r))
    for hook in sorted(hook_coverage, key=lambda h: hook_coverage[h]):
        buckets.append(("hook", hook))

    picked, picked_names = [], set()
    while len(picked) < top_n and buckets:
        progressed = False
        for kind, key in buckets:
            if len(picked) >= top_n:
                break
            for s in scores:
                if s["card"] in picked_names:
                    continue
                ok = (key in s["fills_roles"]) if kind == "role" \
                    else (key in s["feeds_hooks"])
                if ok:
                    label = f"thin hook: {key} (deck coverage {hook_coverage.get(key, 0)})" \
                        if kind == "hook" else f"deficient role: {key}"
                    picked.append({**s, "picked_for": label})
                    picked_names.add(s["card"])
                    progressed = True
                    break
        if not progressed:
            break
    for s in scores:                      # fill remainder by raw score
        if len(picked) >= top_n:
            break
        if s["card"] not in picked_names:
            picked.append({**s, "picked_for": "overall score"})
            picked_names.add(s["card"])

    return {"commander": commander_rec["name"],
            "deck_hooks": sorted({h for _n, h in deck_hooks}),
            "hook_coverage": hook_coverage,
            "suggestions": picked,
            "by_score": scores[:top_n],
            "candidates_considered": len(scores)}


def ablation_importance(idx, by_name: dict, commander_rec: dict,
                        decklist: list[tuple[str, int]],
                        iterations: int = 1200, top_n: int = 10) -> list[dict]:
    """Concept-free importance: remove each nonland card entirely, re-measure
    the deck (synergy edges + simulated commander-on-curve), importance =
    degradation. Finds load-bearing cards WITHOUT needing a concept that
    explains them - the generalized version of 'the deck is a lot weaker
    without this card'. Caveat: only measures what the models model (the
    goldfish sim doesn't yet simulate mana multipliers or spell ramp)."""
    from .goldfish import simulate

    base_cs = cross_synergy(by_name, commander_rec, decklist)
    base_gf = simulate(by_name, commander_rec, decklist, iterations=iterations)
    key_t = max(base_gf["commander_mv"], 1)
    base_curve = base_gf["commander_by_turn_pct"].get(key_t, 0.0)

    rows = []
    for name, count in decklist:
        rec = by_name.get(name)
        if rec is None or "Land" in (rec.get("types") or ""):
            continue
        # replace the cut with a vanilla bystander so deck size, land count,
        # and curve mass stay comparable (a land filler would flatter every
        # removal by improving the mana)
        without = [(n, c) for n, c in decklist if n != name]
        filler = ("Grizzly Bears", count)
        cs = cross_synergy(by_name, commander_rec, without)
        gf = simulate(by_name, commander_rec, without + [filler],
                      iterations=iterations)
        on_curve_delta = round(
            gf["commander_by_turn_pct"].get(key_t, 0.0) - base_curve, 1)
        mana_t5_delta = round(gf["avg_mana_by_turn"].get(5, 0.0)
                              - base_gf["avg_mana_by_turn"].get(5, 0.0), 2)
        rows.append({
            "card": name,
            "edges_lost": base_cs["n_edges"] - cs["n_edges"],
            "on_curve_delta": on_curve_delta,
            "mana_t5_delta": mana_t5_delta,
            "importance": (base_cs["n_edges"] - cs["n_edges"])
            - 2 * on_curve_delta - 10 * mana_t5_delta,
        })
    rows.sort(key=lambda r: -r["importance"])
    return rows[:top_n]


def find_loops(edges: list[dict], max_len: int = 3, limit: int = 25) -> list[dict]:
    """Directed cycles (length 2-3) in the cross-synergy graph: card sets whose
    hooks feed each other. These are SYNERGY loops (the aristocrats engine,
    recursion engines), not proven infinite combos - resource accounting is the
    engine's job, so loops are candidates for engine verification, ranked by
    how many distinct hook-edges participate."""
    adj: dict[str, set[str]] = {}
    edge_info: dict[tuple[str, str], list[str]] = {}
    for e in edges:
        adj.setdefault(e["src"], set()).add(e["dst"])
        edge_info.setdefault((e["src"], e["dst"]), []).append(
            f"{e['hook']}/{e['class']}")

    loops, seen = [], set()
    nodes = sorted(adj)
    for a in nodes:
        # 2-cycles: a -> b -> a
        for b in adj.get(a, ()):
            if a < b and a in adj.get(b, set()):
                key = frozenset((a, b))
                if key not in seen:
                    seen.add(key)
                    loops.append({"cards": [a, b], "len": 2,
                                  "edges": edge_info[(a, b)] + edge_info[(b, a)]})
        if max_len >= 3:
            for b in adj.get(a, ()):
                for c in adj.get(b, ()):
                    if c != a and a in adj.get(c, set()) and a < b and a < c:
                        key = frozenset((a, b, c))
                        if key not in seen and len(key) == 3:
                            seen.add(key)
                            loops.append({"cards": [a, b, c], "len": 3,
                                          "edges": (edge_info[(a, b)]
                                                    + edge_info[(b, c)]
                                                    + edge_info[(c, a)])})
    loops.sort(key=lambda l: (-len(l["edges"]), l["len"]))
    return loops[:limit]


def cuts(by_name: dict, commander_rec: dict, decklist: list[tuple[str, int]],
         cross_edges: list[dict], shape: dict, top_n: int = 10) -> list[dict]:
    """The antithesis of suggest(): rank deck cards by cuttability.
    A card is cuttable when it has few synergy edges, serves no deficient
    role, and sits high on the curve. Cards filling a deficient role or
    anchoring the synergy graph are protected."""
    degree: dict[str, int] = {}
    for e in cross_edges:
        degree[e["src"]] = degree.get(e["src"], 0) + 1
        degree[e["dst"]] = degree.get(e["dst"], 0) + 1

    deficient = {r for r, quota in shape.get("quotas", {}).items()
                 if shape.get("effective_roles", {}).get(r, 0) < quota}
    rows = []
    for name, _count in decklist:
        rec = by_name.get(name)
        if rec is None or "Land" in (rec.get("types") or ""):
            continue
        if name == commander_rec["name"]:
            continue
        deg = degree.get(name, 0)
        roles = detect_roles(rec)
        fills_deficient = sorted(deficient & set(roles))
        mv = mana_value(rec.get("manaCost")) or 0
        # cut score: high = cut first
        score = -deg + max(0, mv - 3) * 1.5
        reasons = [f"{deg} synergy edges"]
        if mv >= 5:
            reasons.append(f"MV {mv}")
        if fills_deficient:
            score -= 10
            reasons.append(f"PROTECTED: fills deficient {'/'.join(fills_deficient)}")
        elif roles.get("ramp") == "engine" and mv <= 3:
            # cheap mana rocks/dorks serve the mana system: their worth is
            # measured by the goldfish sim, not by synergy edges - and
            # cutting mana to add mana is circular
            score -= 10
            reasons.append("PROTECTED: cheap mana engine (judged by simulation)")
        elif roles:
            reasons.append(f"role: {'/'.join(sorted(roles))} (already met)")
        rows.append({"card": name, "cut_score": round(score, 1), "edges": deg,
                     "mv": mv, "reasons": reasons})
    rows.sort(key=lambda r: -r["cut_score"])
    return rows[:top_n]


_BASIC_FOR = {"W": "Plains", "U": "Island", "B": "Swamp",
              "R": "Mountain", "G": "Forest"}


def prescribe(by_name: dict, commander_rec: dict,
              decklist: list[tuple[str, int]], shape: dict,
              cut_rows: list[dict], iterations: int = 3000) -> dict:
    """Close the loop: for each measured mana deficit, build swap variants
    (cut the most cuttable cards, add the fix), RE-SIMULATE each variant,
    and report the measured deltas. The prescription is only issued if the
    simulation actually improves."""
    from .goldfish import simulate

    baseline = simulate(by_name, commander_rec, decklist,
                        iterations=iterations)
    if not any("DEFICIT" in v for v in baseline["verdicts"]):
        return {"baseline": baseline, "variants": [],
                "note": "no measured deficits - nothing to prescribe"}

    # the basic land that fixes the most-underserved color
    pips, sources = shape.get("pips", {}), shape.get("sources", {})
    worst = max(pips, key=lambda c: pips.get(c, 0) - sources.get(c, 0),
                default="G")
    basic = _BASIC_FOR[worst]

    def swap(n_cuts: int, add_name: str) -> list[tuple[str, int]]:
        cut_names = {r["card"] for r in cut_rows[:n_cuts]
                     if not any("PROTECTED" in x for x in r["reasons"])}
        new = [(n, c) for n, c in decklist if n not in cut_names]
        return new + [(add_name, len(cut_names))]

    variants = []
    for n, label in ((2, f"cut 2 worst, add 2 {basic}"),
                     (4, f"cut 4 worst, add 4 {basic}")):
        mod = swap(n, basic)
        gf = simulate(by_name, commander_rec, mod, iterations=iterations)
        key_t = max(baseline["commander_mv"], 1)
        variants.append({
            "label": label,
            "cut": sorted({r["card"] for r in cut_rows[:n]
                           if not any("PROTECTED" in x for x in r["reasons"])}),
            "delta": {
                "commander_on_curve": (
                    gf["commander_by_turn_pct"].get(key_t, 0)
                    - baseline["commander_by_turn_pct"].get(key_t, 0)),
                "t3_land_drop": (gf["land_drop_pct"][3]
                                 - baseline["land_drop_pct"][3]),
                "screw_rate": (gf["screw_rate_pct"]
                               - baseline["screw_rate_pct"]),
            },
            "after": {"commander_on_curve": gf["commander_by_turn_pct"].get(key_t, 0),
                      "t3_land_drop": gf["land_drop_pct"][3],
                      "screw_rate": gf["screw_rate_pct"],
                      "verdicts": gf["verdicts"]},
        })
    variants.sort(key=lambda v: -(v["delta"]["commander_on_curve"]
                                  + v["delta"]["t3_land_drop"]
                                  - v["delta"]["screw_rate"]))
    return {"baseline": baseline, "basic": basic, "variants": variants}


def analyze_deck(idx, commander_rec: dict, decklist: list[tuple[str, int]]) -> dict:
    by_name = {}
    for r in idx.records:
        by_name.setdefault(r.get("name"), r)

    hooks = detect_hooks(commander_rec)
    matrix: dict[str, dict] = {
        h: {"why": f"{commander_rec['name']} {HOOKS[h]['describe']}",
            "classes": {c: [] for c in HOOKS[h]["complements"]}}
        for h in hooks}
    unknown, unconnected = [], []

    for name, _count in decklist:
        rec = by_name.get(name)
        if rec is None:
            unknown.append(name)
            continue
        connected = False
        for h in hooks:
            for cname, query in HOOKS[h]["complements"].items():
                if _matches(rec, query):
                    matrix[h]["classes"][cname].append(name)
                    connected = True
        if not connected:
            unconnected.append(name)

    coverage = {}
    for h in hooks:
        classes = matrix[h]["classes"]
        n = len({card for cards in classes.values() for card in cards})
        coverage[h] = {"cards_feeding_hook": n,
                       "thin": n < 5,
                       "classes": {c: sorted(set(v)) for c, v in classes.items()}}
    return {
        "commander": commander_rec["name"],
        "hooks": hooks,
        "matrix": {h: {"why": matrix[h]["why"], **coverage[h]} for h in hooks},
        "unconnected": unconnected,
        "unknown_cards": unknown,
        "deck_size": sum(c for _n, c in decklist),
    }

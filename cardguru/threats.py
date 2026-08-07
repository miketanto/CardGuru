"""Meta Lab v2: answer the DECK, not the card.

Given an opposing decklist, this module reads its gameplan mechanically
(hook distribution), finds its load-bearing cards (cross-synergy centrality:
the cards the most edges run through), detects its loops, and produces an
answer plan in two layers:

1. surgical: per key threat, which cards in your colors actually work
   (find_answers verdicts), prioritized by the threat's centrality - killing
   a 25-edge hub beats killing a 2-edge bystander;
2. systemic: gameplan-level disruption classes (a graveyard deck fears
   graveyard exile more than any single removal spell), each class a
   structural query over your colors.
"""
from __future__ import annotations

from .deck import cross_synergy, deck_shape, find_loops
from .recommend import color_identity_ok

# gameplan -> systemic disruption classes (structural queries)
DISRUPTION = {
    "graveyard": {
        "graveyard_exile": {"node": {"api": "ChangeZoneAll",
                                     "params": {"Origin": "Graveyard",
                                                "Destination": "Exile"}}},
        "anti_recursion_statics": {"node": {"kind": "R",
                                            "params": {"Event": "Moved",
                                                       "Destination": "Exile"}}},
    },
    "aggro": {
        "sweepers": {"node": {"api": {"any": ["DestroyAll", "DamageAll"]},
                              "params": {"ValidCards": {"contains": "Creature"}}}},
        "fogs": {"node": {"api": "Fog"}},
    },
    "spellslinger": {
        "counterspells": {"node": {"apiKind": "SP", "api": "Counter",
                                   "params": {"TargetType": "Spell"}}},
    },
    "engine": {
        "sweepers": {"node": {"api": {"any": ["DestroyAll", "DamageAll"]},
                              "params": {"ValidCards": {"contains": "Creature"}}}},
        "enchantment_artifact_removal": {"node": {
            "api": "Destroy",
            "params": {"ValidTgts": {"regex": "Artifact|Enchantment|Permanent"}}}},
    },
    "control": {
        # against a pile of answers: attack the hand before they untap, and
        # play threats the stack window can't touch
        "hand_attack": {"node": {"api": "Discard",
                                 "params": {"ValidTgts": {"contains": "Player"}}}},
        "uncounterable_threats": {"node": {"kind": "R",
                                           "params": {"Event": "Counter",
                                                      "Layer": "CantHappen",
                                                      "ValidCard": {"contains": "Self"}}}},
    },
    "ramp_aggro": {
        "sweepers": {"node": {"api": {"any": ["DestroyAll", "DamageAll"]},
                              "params": {"ValidCards": {"contains": "Creature"}}}},
        "edicts": {"node": {"api": "Sacrifice",
                            "params": {"ValidTgts": {"contains": "Player"}}}},
    },
    "generic": {
        "sweepers": {"node": {"api": {"any": ["DestroyAll", "DamageAll"]},
                              "params": {"ValidCards": {"contains": "Creature"}}}},
    },
}


def analyze_opponent(idx, by_name: dict, commander_rec: dict,
                     decklist: list[tuple[str, int]],
                     my_colors: set[str] | None,
                     ci_by_name: dict | None = None,
                     token_scripts: dict | None = None,
                     top_threats: int = 5) -> dict:
    from .answers import find_answers

    shape = deck_shape(by_name, commander_rec, decklist)
    cs = cross_synergy(by_name, commander_rec, decklist)
    loops = find_loops(cs["edges"])

    degree: dict[str, int] = {}
    for e in cs["edges"]:
        degree[e["src"]] = degree.get(e["src"], 0) + 1
        degree[e["dst"]] = degree.get(e["dst"], 0) + 1

    # ENABLER weighting: centrality measures payoff wiring, but a card that
    # accelerates the deck's mana is upstream of everything above it on the
    # curve - killing it collapses the curve. Mana AMPLIFIERS (multiplicative)
    # count every later drop; plain ramp engines (additive dorks/rocks) count
    # half.
    from .deck import detect_roles, mana_value
    from .recommend import HOOKS
    amp_detect = HOOKS["amplifies_mana"]["detect"]
    key_scores: dict[str, dict] = {}
    for name, _count in decklist:
        rec = by_name.get(name)
        if rec is None or "Land" in (rec.get("types") or ""):
            continue
        mv = mana_value(rec.get("manaCost")) or 0
        unlocked = sum(c for n2, c in decklist
                       if (r2 := by_name.get(n2)) is not None
                       and "Land" not in (r2.get("types") or "")
                       and (mana_value(r2.get("manaCost")) or 0) > mv)
        enabler = 0
        why = None
        reducer_detect = HOOKS.get("cost_reducer", {}).get("detect", lambda r: False)
        if amp_detect(rec):
            enabler = unlocked
            why = f"mana multiplier accelerating {unlocked} later drops"
        elif detect_roles(rec).get("ramp") == "engine":
            enabler = unlocked // 2
            why = f"ramp engine accelerating {unlocked} later drops"
        elif reducer_detect(rec):
            enabler = unlocked // 2
            why = f"cost reducer discounting {unlocked} later drops"
        score = degree.get(name, 0) + enabler
        key_scores[name] = {"score": score, "centrality": degree.get(name, 0),
                            "enabler": enabler, "enabler_why": why}
    key_threats = [(n, d["score"]) for n, d in
                   sorted(key_scores.items(), key=lambda kv: -kv[1]["score"])
                   ][:top_threats]
    key_detail = {n: key_scores[n] for n, _s in key_threats}

    def _playable_key(name):
        rec = by_name.get(name) or {}
        types = rec.get("types") or ""
        is_spell = "Instant" in types or "Sorcery" in types
        from .deck import mana_value
        return (0 if is_spell else 1, mana_value(rec.get("manaCost")) or 9)

    surgical = []
    working_sets: list[set[str]] = []
    for name, centrality in key_threats:
        rec = by_name.get(name)
        if rec is None:
            continue
        res = find_answers(idx, rec, colors=my_colors,
                           token_scripts=token_scripts, limit_per_class=1000)
        works = {}
        for klass, data in res["classes"].items():
            for r in data["top"]:
                if r["works"] is True and r["card"] not in works:
                    works[r["card"]] = {"class": klass,
                                        "reason": (r["reasons"] or [""])[0]}
        working_sets.append(set(works))
        best = sorted(works, key=_playable_key)[:5]
        surgical.append({"threat": name, "centrality": centrality,
                         "profile_flags": [k for k in ("hexproof", "shroud",
                                                       "indestructible")
                                           if res["threat"].get(k)],
                         "answers": [{"card": c, **works[c]} for c in best]})

    # the sideboard slots that matter: answers working vs EVERY key threat
    coverage = set.intersection(*working_sets) if working_sets else set()
    best_coverage = sorted(coverage, key=_playable_key)[:10]

    # sweeper sizing: the toughness curve of their creature base decides the
    # minimal mass-damage tier (the "Pyroclasm, not Wrath" derivation)
    tough_rows = []
    for name, count in decklist:
        rec = by_name.get(name)
        if rec is None or "Creature" not in (rec.get("types") or ""):
            continue
        pt = rec.get("pt") or ""
        try:
            t = int(pt.split("/")[1])
        except (ValueError, IndexError):
            continue
        tough_rows.append((t, count, name))
    total_bodies = sum(c for _t, c, _n in tough_rows)
    sweeper = None
    if total_bodies:
        tiers = {}
        for dmg in range(1, 6):
            killed = sum(c for t, c, _n in tough_rows if t <= dmg)
            tiers[dmg] = killed
        # minimal tier clearing >=70% of their bodies
        pick = next((d for d in range(1, 6)
                     if tiers[d] / total_bodies >= 0.7), 5)
        survivors = sorted({n for t, c, n in tough_rows if t > pick})
        examples = []
        q = {"node": {"api": "DamageAll",
                      "params": {"ValidCards": {"contains": "Creature"},
                                 "NumDmg": {"regex": "^[%d-9]$" % pick}}}}
        from .deck import mana_value
        for hit in idx.search(q):
            rec = hit["record"]
            if my_colors is not None:
                cc = {c for c in (rec.get("manaCost") or "") if c in "WUBRG"}
                if not cc <= my_colors:
                    continue
            examples.append((mana_value(rec.get("manaCost")) or 9, rec["name"]))
        examples = [n for _mv, n in sorted(set(examples))[:8]]
        sweeper = {"tier": pick,
                   "kills": tiers[pick], "bodies": total_bodies,
                   "kill_pct": round(100 * tiers[pick] / total_bodies, 1),
                   "survivors": survivors,
                   "examples": examples}

    # mana-value sweep: the second sizing axis. Damage tiers read the
    # toughness curve; destroy-by-MV reads the cost curve. A deck of
    # big-but-cheap bodies (fat toughness, compressed MV) dies whole to an
    # X the damage tiers never reach - Day of Black Sun X=4 wipes a board
    # that laughs at 3 damage.
    mv_sweep = None
    mv_rows = []
    for name, count in decklist:
        rec = by_name.get(name)
        if rec is None or "Creature" not in (rec.get("types") or ""):
            continue
        mv_rows.append((mana_value(rec.get("manaCost")) or 0, count, name))
    if mv_rows:
        mv_total = sum(c for _m, c, _n in mv_rows)
        clear_x = max(m for m, _c, _n in mv_rows)
        mv_pick = next((x for x in range(1, clear_x + 1)
                        if sum(c for m, c, _n in mv_rows if m <= x)
                        / mv_total >= 0.7), clear_x)
        # pool: cards with an MV-<= gate feeding a DestroyAll anywhere in the
        # graph (the gate is often on an upstream node chained by Remember,
        # so this is a card-level conjunction, not a single-node query)
        import re
        mv_examples = []
        for rec2 in idx.records:
            nodes = rec2.get("nodes") or []
            has_destroy = any(nd.get("api") == "DestroyAll" for nd in nodes)
            if not has_destroy:
                continue
            gates = [str((nd.get("params") or {}).get("ValidCards", ""))
                     for nd in nodes]
            gate = next((g for g in gates if "cmcLE" in g and "Creature" in g),
                        None)
            if gate is None:
                continue
            m = re.search(r"Creature\.cmcLE(\w+)", gate)
            if m is None:
                continue
            bound = m.group(1)
            if bound.isdigit():
                if int(bound) < mv_pick:
                    continue
                cost_note = f"fixed <= {bound}"
            else:
                cost_note = f"X-scaling (pay X={clear_x} for full clear)"
            if my_colors is not None:
                cc = {c for c in (rec2.get("manaCost") or "") if c in "WUBRG"}
                if not cc <= my_colors:
                    continue
            mv_examples.append((mana_value(rec2.get("manaCost")) or 9,
                                rec2["name"], cost_note))
        mv_examples = sorted(set(mv_examples))[:8]
        mv_sweep = {"tier": mv_pick,
                    "kills": sum(c for m, c, _n in mv_rows if m <= mv_pick),
                    "bodies": mv_total,
                    "kill_pct": round(100 * sum(c for m, c, _n in mv_rows
                                                if m <= mv_pick) / mv_total, 1),
                    "full_clear_x": clear_x,
                    "survivors": sorted({n for m, c, n in mv_rows
                                         if m > mv_pick}),
                    "examples": [{"card": n, "note": note}
                                 for _mv, n, note in mv_examples]}

    systemic = {}
    for cname, query in DISRUPTION.get(shape["gameplan"], DISRUPTION["generic"]).items():
        rows = []
        for hit in idx.search(query):
            rec = hit["record"]
            if my_colors is not None:
                card_colors = {c for c in (rec.get("manaCost") or "")
                               if c in "WUBRG"}
                if not card_colors <= my_colors:
                    continue
            rows.append(rec["name"])
        systemic[cname] = {"total": len(set(rows)), "top": sorted(set(rows))[:8]}

    from .intuition import stack_window_contests
    stack_window = stack_window_contests(by_name, decklist)

    return {"gameplan": shape["gameplan"],
            "stack_window": stack_window,
            "hook_counts": shape["hook_counts"],
            "key_threats": key_threats,
            "key_detail": key_detail,
            "loops": loops[:5],
            "surgical": surgical,
            "coverage_answers": best_coverage,
            "coverage_pool": len(coverage),
            "sweeper_sizing": sweeper,
            "mv_sweep": mv_sweep,
            "systemic": systemic}

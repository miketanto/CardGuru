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
    key_threats = sorted(degree.items(), key=lambda kv: -kv[1])[:top_threats]

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

    return {"gameplan": shape["gameplan"],
            "hook_counts": shape["hook_counts"],
            "key_threats": key_threats,
            "loops": loops[:5],
            "surgical": surgical,
            "coverage_answers": best_coverage,
            "coverage_pool": len(coverage),
            "systemic": systemic}

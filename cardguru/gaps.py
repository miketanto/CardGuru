"""Concept-gap mining: make the system find its own blind spots.

Every hand-built improvement this project has made followed one template:
a structural signature existed in the card data (TapsForMana->Mana,
SearchedLibrary triggers, Earthbend, ChangeZoneAll graveyard returns...)
but no concept in the libraries (hooks, roles, axes) covered it, so a card
was mis-ranked until a human noticed.

The ontology is CLOSED, so that residual is computable: signature every
card's structures, mark which signatures the concept libraries explain,
and rank the unexplained clusters by frequency. Each top cluster is a
candidate concept, reported with example cards - the raw material for a
new hook/axis/role, found by the system instead of by anecdote.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from .querydsl import CardGraph


def _params(n):
    return n.get("params") or {}


def signatures(rec: dict) -> set[str]:
    """Structural signatures of one card: trigger-mode -> reached-api chains,
    activated-cost archetypes, static modes, replacement events."""
    sigs = set()
    try:
        graph = CardGraph(rec)
    except Exception:
        return sigs
    by_id = {n["id"]: n for n in rec.get("nodes") or []}
    for n in rec.get("nodes") or []:
        kind = n.get("kind")
        p = _params(n)
        if kind == "T":
            mode = p.get("Mode")
            reached = {by_id[d].get("api") for d, _ in
                       graph.reachable(n["id"], None) if by_id[d].get("api")}
            if reached:
                for api in sorted(reached)[:3]:
                    sigs.add(f"T:{mode}->{api}")
            else:
                sigs.add(f"T:{mode}")
        elif kind == "S":
            mode = p.get("Mode") or n.get("mode")
            if mode == "Continuous":
                # sub-signature the catch-all by effect-param family so its
                # clusters are mineable (was one 1,864-card blob)
                fams = [k for k in ("AddPower", "AddToughness", "AddKeyword",
                                    "AddAbility", "SetPower", "SetToughness",
                                    "MayPlay", "GainControl", "AddType",
                                    "RemoveKeyword", "RemoveAllAbilities",
                                    "AddHiddenKeyword", "AdjustLandPlays",
                                    "SetMaxHandSize", "AddColor", "Protection")
                        if k in p]
                aff = str(p.get("Affected", ""))
                scope = ("Self" if "Card.Self" in aff else
                         "YouCtrl" if "YouCtrl" in aff else
                         "Opp" if "Opp" in aff else
                         "All" if aff else "None")
                if fams:
                    sigs.add(f"S:Continuous[{'+'.join(fams[:2])}@{scope}]")
                else:
                    other = sorted(set(p) - {"Mode", "Affected", "Description",
                                             "EffectZone", "AffectedZone",
                                             "Condition", "CheckSVar",
                                             "SVarCompare"})
                    sigs.add(f"S:Continuous[{other[0] if other else 'bare'}@{scope}]")
            else:
                sigs.add(f"S:{mode}")
        elif kind == "R":
            sigs.add(f"R:{p.get('Event')}->{p.get('ReplaceWith') and 'replace' or 'other'}")
        elif kind == "A" and n.get("apiKind") == "AB":
            cost = str(p.get("Cost", ""))
            arche = []
            if "Sac<" in cost:
                arche.append("SacCost")
            if "Discard<" in cost:
                arche.append("DiscardCost")
            if "T" in cost.split():
                arche.append("TapCost")
            sigs.add(f"AB:{'+'.join(arche) or 'ManaCost'}->{n.get('api')}")
    return sigs


def concept_coverage(rec: dict) -> bool:
    """Is this card explained by ANY concept library?"""
    from .deck import detect_roles
    from .intuition import AXES
    from .recommend import detect_hooks
    if detect_hooks(rec) or detect_roles(rec):
        return True
    return any(cfg["signal"](rec) for cfg in AXES.values())


def mine_gaps(records: list[dict], top_n: int = 40) -> list[dict]:
    """The residual report: signatures carried by concept-UNCOVERED cards,
    ranked by how many uncovered cards share them. High-frequency clusters
    are missing concepts; their example cards are the design brief."""
    sig_count: Counter = Counter()
    sig_examples: dict[str, list[str]] = defaultdict(list)
    covered_sigs: Counter = Counter()
    seen = set()
    n_uncovered = 0
    for rec in records:
        name = rec.get("name")
        if not name or name in seen:
            continue
        seen.add(name)
        sigs = signatures(rec)
        if not sigs:
            continue
        if concept_coverage(rec):
            for s in sigs:
                covered_sigs[s] += 1
            continue
        n_uncovered += 1
        for s in sigs:
            sig_count[s] += 1
            if len(sig_examples[s]) < 6:
                sig_examples[s].append(name)

    out = []
    for sig, count in sig_count.most_common(top_n):
        out.append({"signature": sig, "uncovered_cards": count,
                    "also_on_covered_cards": covered_sigs.get(sig, 0),
                    "examples": sig_examples[sig]})
    return {"total_cards": len(seen), "uncovered_cards": n_uncovered,
            "clusters": out}

"""Concept induction: turn mined-cluster drafts into validated hooks.

The pipeline stage between the gap miner and the concept libraries:
an agent (or human) drafts a concept as declarative JSON; this module
compiles the declarative detector into a callable, validates it against
the cluster's example cards and counterexamples, measures its selectivity
over the whole pool, and registers it into HOOKS at runtime. Nothing
enters the libraries without passing the gate.
"""
from __future__ import annotations

from .querydsl import CardGraph


def _nodes(rec):
    return rec.get("nodes") or []


def _params(n):
    return n.get("params") or {}


def _match_pattern(rec: dict, pat: dict) -> bool:
    if "trigger_mode" in pat:
        api = pat.get("chains_to_api")
        try:
            graph = CardGraph(rec)
        except Exception:
            return False
        by_id = {n["id"]: n for n in _nodes(rec)}
        for n in _nodes(rec):
            if n.get("kind") != "T" or _params(n).get("Mode") != pat["trigger_mode"]:
                continue
            if api is None:
                return True
            reached = {by_id[d].get("api")
                       for d, _ in graph.reachable(n["id"], None)}
            if api in reached:
                return True
        return False
    if "ab_cost_contains" in pat:
        return any(n.get("kind") == "A" and n.get("apiKind") == "AB"
                   and pat["ab_cost_contains"] in str(_params(n).get("Cost", ""))
                   and (pat.get("api") is None or n.get("api") == pat.get("api"))
                   for n in _nodes(rec))
    if "static_mode" in pat:
        return any(n.get("kind") == "S"
                   and (_params(n).get("Mode") == pat["static_mode"]
                        or n.get("mode") == pat["static_mode"])
                   for n in _nodes(rec))
    if "has_api" in pat:
        return any(n.get("api") == pat["has_api"] for n in _nodes(rec))
    if "card_type_contains" in pat:
        return pat["card_type_contains"] in (rec.get("types") or "")
    raise ValueError(f"unknown pattern: {pat}")


def compile_detector(spec: dict):
    if "all_of" in spec:
        pats = spec["all_of"]
        return lambda rec: all(_match_pattern(rec, p) for p in pats)
    if "any_of" in spec:
        pats = spec["any_of"]
        return lambda rec: any(_match_pattern(rec, p) for p in pats)
    raise ValueError("detect spec needs all_of or any_of")


def validate_concept(defn: dict, by_name: dict,
                     max_pool_fraction: float = 0.10) -> dict:
    """The gate: detector must match its verified examples, must reject its
    counterexample, and must be selective (not match a large fraction of the
    whole pool)."""
    detect = compile_detector(defn["detect"])
    report = {"name": defn["name"], "errors": [], "warnings": []}

    for ex in defn.get("example_cards_verified", []):
        rec = by_name.get(ex)
        if rec is None:
            report["warnings"].append(f"example not in dataset: {ex}")
        elif not detect(rec):
            report["errors"].append(f"detector rejects claimed example: {ex}")

    counter = defn.get("counterexample", "")
    counter_name = counter.split(" - ")[0].split(":")[0].strip()
    if counter_name and counter_name in by_name:
        if detect(by_name[counter_name]):
            report["errors"].append(
                f"detector matches its own counterexample: {counter_name}")

    n = matched = 0
    for name, rec in by_name.items():
        n += 1
        if detect(rec):
            matched += 1
    report["pool_matches"] = matched
    report["pool_fraction"] = round(matched / max(n, 1), 4)
    if matched == 0:
        report["errors"].append("detector matches nothing in the pool")
    elif report["pool_fraction"] > max_pool_fraction:
        report["errors"].append(
            f"detector not selective: matches {report['pool_fraction']:.0%} of pool")
    report["ok"] = not report["errors"]
    return report


def register_hook(defn: dict) -> None:
    """Runtime registration into the HOOKS library (post-validation)."""
    from .recommend import HOOKS
    HOOKS[defn["name"]] = {
        "describe": defn["describe"],
        "detect": compile_detector(defn["detect"]),
        "complements": defn.get("complements", {}),
    }

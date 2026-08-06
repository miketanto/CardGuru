"""Attach Comprehensive Rules citations to adjudication results.

Given the cards in a scenario, walk their ability graphs and translate every
mapped ontology token (keyword, effect API, trigger mode, replacement event)
into its CR rule via research/data/cr_mapping.json. This is what lets a
simulated answer say *which rules governed it* — automatically, from data.
"""
from __future__ import annotations

import json


# card-layout rules (verified against parsed CR section titles)
ALT_MODE_RULES = {
    "Adventure": ("715", "Adventurer Cards"),
    "Split": ("709", "Split Cards"),
    "Flip": ("710", "Flip Cards"),
    "DoubleFaced": ("712", "Double-Faced Cards"),
    "Modal": ("712", "Double-Faced Cards"),
    "Meld": ("701", "Keyword Actions"),   # meld action; melded pairs also 712-adjacent
    "Prototype": ("718", "Prototype Cards"),
    "Omen": ("722", "Omen Cards"),
}


class Citer:
    def __init__(self, mapping_path: str, cr_path: str | None = None):
        with open(mapping_path, encoding="utf-8") as f:
            data = json.load(f)
        self.mapping = data["mapping"]
        self.cr_effective = data.get("cr_effective")
        self.rule_texts = {}
        if cr_path:
            with open(cr_path, encoding="utf-8") as f:
                self.rule_texts = json.load(f)["rules"]

    def _lookup(self, table: str, token: str):
        entry = self.mapping.get(table, {}).get(token)
        if entry and entry.get("rule"):
            return entry
        return None

    def citations_for_record(self, rec: dict) -> list[dict]:
        """Citations for one card's graph record (dataset row)."""
        out = {}
        alt = rec.get("alternateMode")
        if alt in ALT_MODE_RULES:
            rule, title = ALT_MODE_RULES[alt]
            if rule in self.rule_texts:
                title = self.rule_texts[rule].get("title") or title
            out[(rule, alt)] = {"rule": rule, "title": title,
                                "token": f"layout:{alt}", "card": rec.get("name")}
        for node in rec.get("nodes", []):
            kind = node.get("kind")
            hits = []
            if kind == "K" and node.get("keyword"):
                hits.append(("keywords", node["keyword"]))
            if node.get("api"):
                hits.append(("apis", node["api"]))
            if kind == "T" and node.get("params", {}).get("Mode"):
                hits.append(("trigger_modes", node["params"]["Mode"]))
            if kind == "R" and node.get("params", {}).get("Event"):
                hits.append(("replacement_events", node["params"]["Event"]))
            for table, token in hits:
                entry = self._lookup(table, token)
                if not entry:
                    continue
                key = (entry["rule"], token)
                if key not in out:
                    cite = {"rule": entry["rule"], "title": entry["title"],
                            "token": token, "card": rec.get("name")}
                    if entry["rule"] in self.rule_texts:
                        r = self.rule_texts[entry["rule"]]
                        cite["title"] = r.get("title") or cite["title"]
                    out[key] = cite
        return list(out.values())

    def citations_for_cards(self, names: list[str], records_by_name: dict) -> list[dict]:
        seen = {}
        for name in names:
            rec = records_by_name.get(name)
            if not rec:
                continue
            for c in self.citations_for_record(rec):
                key = (c["rule"], c["token"])
                if key not in seen:
                    seen[key] = c
        return sorted(seen.values(), key=lambda c: _rule_sort_key(c["rule"]))


def _rule_sort_key(rule: str):
    parts = rule.replace("a", ".1").split(".")
    try:
        return tuple(float(p) if p.replace(".", "").isdigit() else 0 for p in parts)
    except ValueError:
        return (0,)


def scenario_card_names(spec: dict) -> list[str]:
    names = []
    for cfg in spec.get("players", {}).values():
        for b in cfg.get("battlefield", []):
            names.append(b["card"] if isinstance(b, dict) else b)
        for zone in ("hand", "graveyard", "exile", "library_top"):
            names += cfg.get(zone, [])
    for a in spec.get("actions", []):
        if a.get("card"):
            names.append(a["card"])
    seen, ordered = set(), []
    for n in names:
        if n not in seen:
            seen.add(n)
            ordered.append(n)
    return ordered

"""Commander deck recommendation prototype.

The recommendation logic is mechanical, not co-occurrence-based: detect what
a commander DOES from its ability graph ("synergy hooks"), then run
complement queries for cards whose graphs connect to those hooks — token
makers pair with token payoffs, lifegain sources with lifegain triggers,
death triggers with sacrifice outlets. Every recommendation carries a
machine-readable WHY (hook + matched structure), and color identity comes
from the canonical card index.
"""
from __future__ import annotations

CI_ORDER = "wubrg"

# hook -> (detector over the commander's graph, complement queries)
HOOKS = {
    "makes_tokens": {
        "describe": "creates tokens",
        "complements": {
            "token_payoffs": {"chain": {"from": {"kind": "T", "mode": "TokenCreated"},
                                        "to": {}}},
            "token_doubling": {"chain": {"from": {"kind": "R",
                                                  "params": {"Event": "CreateToken"}},
                                         "to": {"api": "ReplaceToken"}}},
            "anthems": {"node": {"mode": "Continuous",
                                 "params": {"AddPower": True,
                                            "Affected": {"contains": "Creature.YouCtrl"}}}},
        },
    },
    "gains_life": {
        "describe": "gains life",
        "complements": {
            "lifegain_payoffs": {"chain": {"from": {"kind": "T", "mode": "LifeGained"},
                                           "to": {}}},
        },
    },
    "cares_about_death": {
        "describe": "triggers on creatures dying",
        "complements": {
            "sac_outlets": {"node": {"kind": "A", "apiKind": "AB",
                                     "params": {"Cost": {"regex": "Sac<[0-9X]+/Creature"}}}},
            "token_fodder": {"chain": {"from": {"kind": "T", "mode": "ChangesZone",
                                                "params": {"Destination": "Battlefield"}},
                                       "to": {"api": "Token"}}},
        },
    },
    "puts_counters": {
        "describe": "puts +1/+1 counters",
        "complements": {
            "proliferate": {"node": {"api": "Proliferate"}},
            "counter_doubling": {"chain": {"from": {"kind": "R",
                                                    "params": {"Event": "AddCounter"}},
                                           "to": {"api": "ReplaceCounter"}}},
        },
    },
    "sac_outlet": {
        "describe": "sacrifices creatures as a cost",
        "complements": {
            "death_triggers": {"chain": {"from": {"kind": "T", "mode": "ChangesZone",
                                                  "params": {"Origin": "Battlefield",
                                                             "Destination": "Graveyard"}},
                                         "to": {}}},
        },
    },
    "amplifies_death_triggers": {
        "describe": "makes dies-triggers trigger an additional time",
        "complements": {
            "death_triggers": {"chain": {"from": {"kind": "T", "mode": "ChangesZone",
                                                  "params": {"Origin": "Battlefield",
                                                             "Destination": "Graveyard"}},
                                         "to": {}}},
            "sac_outlets": {"node": {"kind": "A", "apiKind": "AB",
                                     "params": {"Cost": {"regex": "Sac<[0-9X]+/Creature"}}}},
        },
    },
    "buffs_tokens": {
        "describe": "grants abilities to your creature tokens",
        "complements": {
            "token_makers": {"chain": {"from": {"kind": {"any": ["A", "T"]}},
                                       "to": {"api": "Token"}}},
        },
    },
}


def _reaches_api(rec, api):
    return any(n.get("api") == api for n in rec["nodes"])


def detect_hooks(rec: dict) -> list[str]:
    hooks = []
    if _reaches_api(rec, "Token"):
        hooks.append("makes_tokens")
    if _reaches_api(rec, "GainLife") or any(
            n.get("keyword") == "Lifelink" for n in rec["nodes"]):
        hooks.append("gains_life")
    for n in rec["nodes"]:
        p = n.get("params", {})
        if n.get("kind") == "T" and p.get("Mode") == "ChangesZone" \
                and p.get("Origin") == "Battlefield" \
                and p.get("Destination") == "Graveyard" \
                and p.get("ValidCard") != "Card.Self":
            hooks.append("cares_about_death")
            break
    else:
        # Teysa-style: replacement/static doubling of dies triggers
        if any(n.get("kind") == "R" and "Moved" == n.get("params", {}).get("Event")
               for n in rec["nodes"]):
            hooks.append("cares_about_death")
    if _reaches_api(rec, "PutCounter"):
        hooks.append("puts_counters")
    if any("Sac<" in str(n.get("params", {}).get("Cost", ""))
           and "Creature" in str(n.get("params", {}).get("Cost", ""))
           for n in rec["nodes"]):
        hooks.append("sac_outlet")
    for n in rec["nodes"]:
        p = n.get("params", {})
        if p.get("Mode") == "Panharmonicon" \
                and p.get("Origin") == "Battlefield" \
                and p.get("Destination") == "Graveyard":
            hooks.append("amplifies_death_triggers")
        if p.get("Mode") == "Continuous" \
                and "Creature.token" in str(p.get("Affected", "")) \
                and ("AddKeyword" in p or "AddPower" in p):
            hooks.append("buffs_tokens")
    return hooks


def color_identity_ok(ci: str | None, commander_ci: set[str]) -> bool:
    if ci is None:
        return False
    return set(ci) <= commander_ci


def recommend(idx, commander_rec: dict, ci_by_name: dict,
              limit_per_class: int = 8) -> dict:
    name = commander_rec["name"]
    commander_ci = set(ci_by_name.get(name) or "")
    hooks = detect_hooks(commander_rec)
    out = {"commander": name, "color_identity": "".join(
        c for c in CI_ORDER if c in commander_ci), "hooks": {}}
    for hook in hooks:
        cfg = HOOKS[hook]
        classes = {}
        for cname, query in cfg["complements"].items():
            rows = []
            for hit in idx.search(query):
                rec = hit["record"]
                if rec["name"] == name:
                    continue
                if not color_identity_ok(ci_by_name.get(rec["name"]), commander_ci):
                    continue
                rows.append(rec["name"])
            seen, unique = set(), []
            for r in rows:
                if r not in seen:
                    seen.add(r)
                    unique.append(r)
            classes[cname] = {"total": len(unique),
                              "top": sorted(unique)[:limit_per_class]}
        out["hooks"][hook] = {"why": f"{name} {cfg['describe']}",
                              "complements": classes}
    return out
